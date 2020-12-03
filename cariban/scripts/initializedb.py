import io
import re

from clld.cliutil import Data, bibtex2source, add_language_codes
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex
from clld_phylogeny_plugin.models import Phylogeny, LanguageTreeLabel, TreeLabel
#to edit tree labels
from Bio import Phylo
from ipapy.ipastring import IPAString

import cariban
from cariban import models, util


# #To figure out whether a given t-adding verb would have the prefix tɨ- or t-
def t_prefix_form(string):
    initial = IPAString(unicode_string=string, ignore=True)
    if len(initial.consonants) > 0 and initial.consonants[0].is_equivalent(initial[0]):
        return "tɨ"
    return "t"


def main(args):  # pragma: no cover
    data = Data()

    print("Setting up dataset…")
    dataset = common.Dataset(
        id=cariban.__name__,
        domain="cariban.clld.org",
        name="Cariban Morphology Database",
        description="Cariban Morphology Database",
        publisher_name="Max Planck Institute for Evolutionary Anthropology",
        publisher_url="https://www.eva.mpg.de",
        publisher_place="Leipzig",
        license="https://creativecommons.org/licenses/by/4.0/",
        contact="florian.matter@isw.unibe.ch",
        jsondata={'function_paradigms': []},
    )

    fps = []
    for morph_func in args.cldf["ValueTable"]:
        for function in morph_func["Function"]:
            for cons in morph_func["Construction"]:
                fps.append({
                    'Function': function,
                    'Construction': cons,
                    'Morpheme': morph_func['Morpheme']})
    dataset.update_jsondata(function_paradigms=fps)

    DBSession.add(dataset)
    DBSession.flush()

    print("Adding contributors…")
    c = common.Contributor(id="fm",name="Florian Matter", email="florianmatter@gmail.com", url="https://florianmatter.gitlab.io/")
    dataset.editors.append(common.Editor(contributor=c, ord=1, primary=True))

    print("Adding languages…")
    dialect_mapping = {}
    lang_shorthands = {}
    glottocodes = {}
    lang_ids = {}
    for lang in args.cldf["LanguageTable"]:
        if lang["Sampled"] == "y":
            language = data.add(
                common.Language,
                lang["ID"],
                id=lang["ID"],
                name=lang["Name"],
                latitude=float(lang["Latitude"]) if lang["Latitude"] is not None else None,
                longitude=float(lang["Longitude"]) if lang["Longitude"] is not None else None,
                jsondata={'Shorthand': lang['Shorthand'], 'Glottocode': lang['Glottocode']},
            )
            add_language_codes(data, language, isocode=lang["ISO"], glottocode = lang["Glottocode"])
        if lang["Dialect_Of"] not in [None, "y"]:
            dialect_mapping[lang["ID"]] = lang["Dialect_Of"]
        lang_shorthands[lang["Shorthand"]] = {"ID": lang["ID"], "Name": lang["Name"]}
        glottocodes[lang["Glottocode"]] = {"ID": lang["ID"], "Name": lang["Name"], "Shorthand": lang["Shorthand"]}
        lang_ids[lang["ID"]] = {"Glottocode": lang["Glottocode"], "Name": lang["Name"], "Shorthand": lang["Shorthand"]}

    def get_lang_id(key):
        if key in lang_shorthands:
            lang_id = lang_shorthands[key]["ID"]
        elif key in glottocodes:
            lang_id = glottocodes[key]["ID"]
        elif key in lang_ids:
            lang_id = key
        else:
            print("Could not identify language %s" % key)
            return None
        if lang_id in dialect_mapping:
            lang_id = dialect_mapping[lang_id]
        return lang_id

    def get_key_and_page(source_string):
        if len(source_string.split("[")) > 1:
            bib_key = source_string.split("[")[0]
            pages = source_string.split("[")[1].split("]")[0]
        else:
            bib_key = source_string
            pages = ""
        return bib_key, pages

    print("Adding sources…")
    for rec in bibtex.Database.from_file(args.cldf.bibpath):
        data.add(common.Source, rec.id, _obj=bibtex2source(rec))
    
    print("Adding language sources…")
    DBSession.flush()
    for rec in bibtex.Database.from_file(args.cldf.bibpath):
        if "keywords" in rec:
            for keyword in rec["keywords"].split(","):
                if keyword in lang_shorthands:
                    lang_id = get_lang_id(keyword.strip(" "))
                    if lang_id in data["Language"]:
                        data.add(common.LanguageSource,
                        rec.id+lang_id,
                        language_pk=data["Language"][lang_id].pk,
                        source_pk=data["Source"][rec.id].pk
                        )
        
    data.add(
        common.Source,
        "pc",
        id="pc",
        name="Personal communication",
        description="Placeholder for data obtained from personal communication.",
        bibtex_type=bibtex.EntryType.misc
    )

#     print("Adding glossing abbreviations…")
#     length = len(pynterlinear.get_all_abbrevs().keys())
#     for i, (key, name) in enumerate(pynterlinear.get_all_abbrevs().items()):
#         print("%s/%s" % (i+1, length), end="\r")
#         DBSession.add(common.GlossAbbreviation(id=key, name=name))
#     print("")
#
    print("Adding examples…")
    gloss_replacements = {
        "S_A_": "Sa",
        "S_P_": "Sp"
    }
    def clldify_glosses(gloss_line):
        for orig, new in gloss_replacements.items():
            gloss_line = gloss_line.replace(orig,new)
        gloss_line = re.sub(r"(\d)([A-Z])", r"\1.\2", gloss_line)
        return gloss_line

    for ex in args.cldf["ExampleTable"]:
        lang_id = get_lang_id(ex["Language_ID"])
        new_ex = data.add(common.Sentence,
            ex["ID"],
            id=ex["ID"],
            name=ex["Name"],
            description=ex["Translated_Text"],
            analyzed="\t".join(ex["Analyzed_Word"]),
            gloss=clldify_glosses("\t".join(ex["Gloss"])),
            language=data["Language"][lang_id],
            comment=ex["Comment"],
            markup_gloss="\t".join(ex["Morpheme_IDs"])
        )
        
        if ex["Source"]:
            bib_key, pages = get_key_and_page(ex["Source"])
            if bib_key in data["Source"]:
                source = data["Source"][bib_key]
                DBSession.add(common.SentenceReference(
                    sentence=new_ex,
                    source=source,
                    key=source.id,
                    description=pages.replace("--","–"))
                )

    def add_morpheme_reference(morpheme, source_string):
        bib_key, pages = get_key_and_page(source_string)
        if bib_key in data["Source"]:
            source = data["Source"][bib_key]
            DBSession.add(models.MorphemeReference(
                morpheme=morpheme,
                source=source,
                key=source.id,
                description=pages.replace("--","–")
                )
            )

    print("Adding morphemes…")
    for morph in args.cldf["FormTable"]:
        lang_id = get_lang_id(morph["Language_ID"])
        form = util.merge_allomorphs("; ".join(morph["Form"])).split("; ")
        new_morph = data.add(models.Morpheme,
            morph["ID"],
            morpheme_type="grammatical",
            language=data["Language"][lang_id],
            name="/".join(form),
            id=morph["ID"],
        )
        
        if morph["Source"]: add_morpheme_reference(new_morph, morph["Source"][0])

    print("Adding constructions…")
    data.add(models.DeclarativeType, "imp", id="imp", name="imperative")
    data.add(models.DeclarativeType, "decl", id="decl", name="declarative")
    data.add(models.MainClauseVerb, "y", id="y", name="main clause construction")
    data.add(models.MainClauseVerb, "n", id="n", name="subordinate clause construction")

    for cons in args.cldf["ParameterTable"]:
        lang_id = get_lang_id(cons["Language_ID"])
        new_construction = data.add(
            models.Construction,
            cons["ID"],
            id=cons["ID"],
            language=data["Language"][lang_id],
            name=cons["Description"],
            mainclauseverb=data["MainClauseVerb"][cons["MainClauseVerb"]],
        )
        if cons["DeclarativeType"]: new_construction.declarativetype = data["DeclarativeType"][cons["DeclarativeType"]]

    def add_morph_func(morpheme, func_key, construction):
        data.add(models.MorphemeFunction,
            "%s:%s" % (morpheme, function),
            id="%s:%s" % (morpheme, func_key),
            name="MorphemeFunction %s:%s"% (morpheme, func_key),
            unit=data["Morpheme"][morpheme],
            unitparameter=data["Meaning"][function],
            construction=construction
        )

    print("Adding morpheme functions…")
    for morph_func in args.cldf["ValueTable"]:
        for function in morph_func["Function"]:
            func_key = function.replace(".","_")
            if ">" in function or function == "LK" or bool(re.search(r"\d[SP]$", function) or function == "3"):
                meaning_type="inflectional"
            else:
                meaning_type="derivational"
            if function not in data["Meaning"]:
                data.add(models.Meaning,
                    function,
                    id=func_key,
                    name=function,
                    meaning_type=meaning_type
                )
            #Only some morpheme functions are specified as occurring in specific constructions
            if len(morph_func["Construction"]) == 0:
                for morpheme in morph_func["Morpheme"]:
                    add_morph_func(morpheme, func_key, None)
            else:
                for construction in morph_func["Construction"]:
                    if len(morph_func["Morpheme"]) == 1 and morph_func["Morpheme"][0] != "?":
                        for morpheme in morph_func["Morpheme"]:
                            if data["Morpheme"][morpheme].language != data["Construction"][construction].language:
                                print("Warning: the %s Morpheme %s is stated to occur in the %s construction %s!" % (
                                data["Morpheme"][morpheme].language,
                                data["Morpheme"][morpheme],
                                data["Construction"][construction].language,
                                data["Construction"][construction]
                                )
                                )
                            cons_func_key = func_key + ":" + construction
                            add_morph_func(morpheme, cons_func_key, data["Construction"][construction])

    print("Checking examples for illustrated morphemes…")
    proto_languages = ["pc"]
    is_illustrated = {}
    for key, row in data["MorphemeFunction"].items():
        if row.unit.language.id in proto_languages: continue
        is_illustrated["%s:%s" % (row.unit.id, row.unitparameter.id)] = False
    for row in args.cldf["ExampleTable"]:
        for word in row["Morpheme_IDs"]:
            morph_ids = util.split_word(word)
            for unit_value in morph_ids:
                if unit_value in ["X","-","=", "~"]:
                    continue
                unitvaluesentence_key = "{0}-{1}".format(unit_value.replace(".","-"),row["ID"])
                if unitvaluesentence_key in data["UnitValueSentence"].keys():
                    continue
                is_illustrated[unit_value] = True
                morph_id = unit_value.split(":")[0]
                if morph_id not in data["Morpheme"].keys():
                    print("Warning: Example %s illustrates unknown morpheme %s" % (row["ID"], morph_id))
                elif data["Morpheme"][morph_id].language != data["Sentence"][row["ID"]].language:
                    print("Warning: The %s example %s claims to contain the %s morpheme %s." % (
                        data["Sentence"][row["ID"]].language,
                        row["ID"],
                        data["Morpheme"][morph_id].language,
                        data["Morpheme"][morph_id]
                    )
                    )
                if ":" not in unit_value:
                    print("%s in %s contains no defined function!" % (unit_value, row["ID"]))
                function = unit_value.split(":")[1]
                morph_function_id = "%s:%s" % (morph_id, function)
                if morph_function_id not in data["MorphemeFunction"].keys():
                    print("Warning: Example %s tries to illustrate inexistent morpheme function %s!" % (row["ID"], unit_value.replace(".","-")))
                    continue
                data.add(models.UnitValueSentence,
                unitvaluesentence_key,
                sentence=data["Sentence"][row["ID"]],
                unitvalue=data["MorphemeFunction"][morph_function_id],
                )


    # see how many morpheme functions are illustrated with example sentences
    good_ill = [key for key, value in is_illustrated.items() if value]
    not_ill = [key for key, value in is_illustrated.items() if not value]
    not_ill.sort()
    cov = len(good_ill)/len(is_illustrated)*100
    print("Morpheme exemplification coverage is at %s%%. List of unillustrated morphemes saved to unillustrated_morphemes.txt" % str(round(cov, 2)))
    f = open("../unillustrated_morphemes.txt", "w")
    for morph in not_ill:
        f.write(morph+"\n")
    f.close()

    print("Adding cognate sets…")
    for cogset in args.cldf["CognatesetTable"]:
        new_cset = data.add(models.Cognateset,
            cogset["ID"],
            id=cogset["ID"],
            name=cogset["Name"],
            description=cogset["Function"],
            cogset_type="grammatical"
        )
        if cogset["Source"]:
            for source in cogset["Source"]:
                bib_key, pages = get_key_and_page(source)
                if bib_key in data["Source"]:
                    source = data["Source"][bib_key]
                    DBSession.add(models.CognatesetReference(
                        cognateset=new_cset,
                        source=source,
                        key=source.id,
                        description=pages)
                        )

    print("Adding cognates…")
    for morph in args.cldf["FormTable"]:
        for cognate_ID in morph["Cognateset_ID"]:
            DBSession.add(models.Cognate(
                    cognateset=data["Cognateset"][cognate_ID],
                    counterpart=data["Morpheme"][morph["ID"]]
                    )
            )

    print("Adding morpheme comments…")
    for row in args.cldf["FormTable"]:
        data["Morpheme"][row["ID"]].markup_description=util.generate_markup(row["Comment"])

    print("Adding construction descriptions…")
    for cons in args.cldf["ParameterTable"]:
        if cons["Comment"] is None:
            description = ""
        else:
            description = util.generate_markup(cons["Comment"])
        description += "\n" + util.generate_markup(util.transitive_construction_paradigm(cons["ID"]))
        description += util.generate_markup(util.intransitive_construction_paradigm(cons["ID"]))
        data["Construction"][cons["ID"]].markup_description = description


    print("Adding cognate set descriptions…")
    for cogset in args.cldf["CognatesetTable"]:
        data["Cognateset"][cogset["ID"]].markup_description = util.generate_markup(cogset["Description"])
        # if cogset["ID"] == "13pro":
        #     data["Cognateset"][cogset["ID"]].markup_description += util.generate_markup(
        #         util.comparative_function_paradigm(
        #             ["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_old", "kax_main"],
        #             "1+3 scenarios",
        #             ["1+3S", "1+3>3", "3>1+3", "2>1+3", "1+3>2"]))

    
    def add_tree_labels(phylo):
        uncertain_nodes = []
        for node in phylo.find_clades():
            if node.name == None or not node.is_terminal():
                continue
            plain_name = node.name.replace("?","")
            if "?" in node.name: uncertain_nodes.append(plain_name)
            if plain_name in lang_ids:
                node.name = lang_ids[plain_name]["Name"].replace("'", "’")
            if plain_name in uncertain_nodes: node.name += "?"
        return phylo, uncertain_nodes
        
    print("Adding trees…")
    own_trees = ["matter"]
    tree_path = str(args.cldf.tablegroup._fname.parent / '..' / 'raw')
    newick_files = {}
    for tree in args.cldf["cariban_trees.csv"]:
        if tree["ID"] in own_trees: continue
        newick_files[tree["ID"]] = {
            "orig": tree["ID"]+"_orig.newick",
            "norm": tree["ID"]+"_norm.newick",
            "source": tree["Source"],
            "comment": tree["Comment"],
            "o_comment": tree["Orig_Comment"]
        }
    #adding my own trees separately.
    for my_tree_count, tree_id in enumerate(own_trees):
        my_tree = Phylo.read(tree_path+"/"+"%s.newick" % tree_id, "newick")
        my_tree, uncertain_nodes = add_tree_labels(my_tree)
        
        edited_tree = io.StringIO()
        Phylo.write(my_tree, edited_tree, "newick")
        tree = edited_tree.getvalue().replace(":0.00000","")
        
        my_phylo = Phylogeny(
                tree_id,
                id=tree_id,
                name="Matter (2020)",# % str(my_tree_count+1),
                newick=tree,
                markup_description="My own, conservative, classification."
        )
        
        for l in DBSession.query(common.Language):
            lname = l.name.replace("'", "’")
            if l.id in uncertain_nodes: lname += "?"
            new_label = LanguageTreeLabel(
                language=l,
                treelabel=TreeLabel(
                    id="%s_%s" % (tree_id, l.id),
                    name=lname,
                    phylogeny=my_phylo
                )
            )
              
        DBSession.add(my_phylo)
        
    #adding the other trees
    for tree_id, values in newick_files.items():
        norm_biotree = Phylo.read(tree_path+"/"+values["norm"], "newick")
        orig_biotree = Phylo.read(tree_path+"/"+values["orig"], "newick")
        
        norm_biotree, uncertain_nodes = add_tree_labels(norm_biotree)
            
        edited_tree = io.StringIO()
        Phylo.write(norm_biotree, edited_tree, "newick")
        norm_tree = edited_tree.getvalue().replace(":0.00000","")
        
        edited_tree = io.StringIO()
        Phylo.write(orig_biotree, edited_tree, "newick")
        orig_tree = edited_tree.getvalue().replace(":0.00000","")
        
        norm_phylo = Phylogeny(
                id=tree_id+"_norm",
                name=str(data["Source"][values["source"]]) + " (Normalized)",
                markup_description=util.generate_markup("Source: src:"+values["source"])+
                "<br>This is a normalized version of <a href='/phylogeny/%s_orig'>this original tree</a>." % tree_id +
                util.generate_markup(
                    "<br>Comments: %s" % values["comment"]
                ),
                newick=norm_tree
        )
        
        if values["o_comment"] == None:
            o_comment = ""
        else:
            o_comment = values["o_comment"]
        orig_phylo = Phylogeny(
                id=tree_id+"_orig",
                name=str(data["Source"][values["source"]]) + " (Original)",
                markup_description=util.generate_markup("Source: src:"+values["source"])+
                    "<br>This is a representation of the original classification. A normalized version can be found <a href='/phylogeny/%s_norm'>here</a>." % tree_id +
                    util.generate_markup(
                    "<br>Comments: %s" % values["comment"] +
                    " " + o_comment
                    ),
                newick=orig_tree
        )
        for l in DBSession.query(common.Language):
            lname = l.name.replace("'", "’")
            if l.id in uncertain_nodes: lname += "?"
            new_label = LanguageTreeLabel(
                language=l,
                treelabel=TreeLabel(
                    id="%s_%s" % (tree_id, l.id),
                    name=lname,
                    phylogeny=norm_phylo
                )
            )
        DBSession.add(norm_phylo)
        DBSession.add(orig_phylo)

    print("Adding t-adding verb cognate sets…")
    for t_verb_set in args.cldf["cariban_t_cognates.csv"]:
        cognate_ID = "t"+t_verb_set["ID"]
        rec_t_form = "*[%s]%s" % (t_prefix_form(t_verb_set["Form"]), t_verb_set["Form"])
        t_cogset = data.add(models.Cognateset,
            cognate_ID,
            id=cognate_ID,
            name=rec_t_form,
            description="‘%s’ (*t-adding verb)" % t_verb_set["Parameter_ID"],
            cogset_type="t_adding"
        )
        if t_verb_set["Source"]:
            bib_key = t_verb_set["Source"].split("[")[0]
            if len(t_verb_set["Source"].split("[")) > 1:
                pages = t_verb_set["Source"].split("[")[1].split("]")[0]
            else:
                pages = " "
            if bib_key in data["Source"]:
                source = data["Source"][bib_key]
                DBSession.add(models.CognatesetReference(
                    cognateset=t_cogset,
                    source=source,
                    key=source.id,
                    description=pages)
                    )
    
    print("Adding t-adding verbs…")
    t_langs = {}
    t_verbs = {}
    non_t_adding_lgs = ["ing","mac","kar","wmr","pan"]
    data.add(models.Meaning,
        "t_verb",
        id="t-verb",
        name="t-adding verb",
    )
    for t_verb_entry in args.cldf["cariban_t_verbs.csv"]:
        if t_verb_entry["Language_ID"] == "cari1283": continue
        cognate_ID = "t"+t_verb_entry["Cognateset_ID"]
        lang_id = get_lang_id(t_verb_entry["Language_ID"])
        morph_id = lang_id+"_"+cognate_ID
        if morph_id in data["Morpheme"].keys():
            if morph_id + "_2" in data["Morpheme"].keys():
                morph_id += "_3"
            else:
                morph_id += "_2"
        t_verb = data.add(models.Morpheme,
            morph_id,
            id=morph_id,
            morpheme_type="t_adding",
            name=t_verb_entry["Form"],
            language=data["Language"][lang_id],
        )
        DBSession.add(models.Cognate(
                cognateset=data["Cognateset"][cognate_ID],
                counterpart=t_verb
            )
        )
        if t_verb_entry["t"] == "y":
            t_verb.name = "[%s]%s" % (t_prefix_form(t_verb.name), t_verb.name)
            t_verb.markup_description = util.generate_markup("Shows cogset:t")
        if t_verb_entry["t"] == "?" and lang_id not in non_t_adding_lgs:
            t_verb.name = "[t-?]"+t_verb.name
            t_verb.markup_description = util.generate_markup("It is not known if this verb shows cogset:t")
        if t_verb_entry["t"] == "n":
            t_verb.markup_description = util.generate_markup("Does not show cogset:t")
        if lang_id not in t_langs.keys():
            t_langs[lang_id] = {"y": 0, "n": 0, "?": 0}
        if cognate_ID not in t_verbs.keys():
            t_verbs[cognate_ID] = {"y": 0, "n": 0, "?": 0}
        t_langs[lang_id][t_verb_entry["t"]] += 1
        if lang_id not in non_t_adding_lgs:
            t_verbs[cognate_ID][t_verb_entry["t"]] += 1
        if t_verb_entry["Source"]:
            add_morpheme_reference(t_verb, t_verb_entry["Source"])

        data.add(models.MorphemeFunction,
            "t_"+t_verb_entry["ID"],
            id="t_"+t_verb_entry["ID"],
            name="t-Verb %s" % t_verb_entry["Parameter_ID"],
            unit=t_verb,
            unitparameter=data["Meaning"]["t_verb"],
            construction=None
        )
    for lang, values in t_langs.items():
        data["Language"][lang].update_jsondata(t_values=values)
    for verb, values in t_verbs.items():
        # data["Cognateset"][verb].description += " (%s/%s)" % (str(values["y"]), str(values["n"]+values["y"]+values["?"]))
        data["Cognateset"][verb].markup_description = util.generate_markup("This verb occurs with obj:t- in %s of %s languages which show reflexes of cogset:t." % (str(values["y"]), str(values["n"]+values["y"]+values["?"])))

    print("Adding reconstructed lexemes…")
    proto_forms = {}
    for cogset in args.cldf["cariban_lexical_reconstructions.csv"]:
        proto_forms[cogset["ID"]] = cogset["Form"]

    first_found = []
    for entry in args.cldf["cariban_swadesh_list.csv"]:
        cognateset_ID = entry["Parameter_ID"].replace("/","_")+"-"+entry["Cognateset_ID"]
        if cognateset_ID not in data["Cognateset"]:
            if cognateset_ID in proto_forms:
                form = "*" + proto_forms[cognateset_ID].replace("; ", " / ")
            # else:
            #     form = ""
                data.add(models.Cognateset,
                    cognateset_ID,
                    id=cognateset_ID,
                    name=form,
                    description=cognateset_ID,
                    cogset_type="lexical"
                )
        lang_id = get_lang_id(entry["Language_ID"])
        if lang_id not in data["Language"]: continue
        function = entry["Parameter_ID"].replace(".","_")
        morph_id = entry["Language_ID"] + "_" + function
        if morph_id in first_found: continue
        first_found.append(morph_id)
        if function not in data["Meaning"].keys():
            data.add(models.Meaning,
                function,
                id=function,
                name=function,
                meaning_type="lexical"
            )
        morpheme = data.add(models.Morpheme,
                    morph_id,
                    id=morph_id,
                    morpheme_type="lexical",
                    name=entry["Value"][0],
                    language=data["Language"][lang_id],
                )
        data.add(models.MorphemeFunction,
            "%s:%s" % (morph_id, function),
            id="%s:%s" % (morph_id, function),
            name="MorphemeFunction %s:%s"% (morph_id, function),
            unit=data["Morpheme"][morph_id],
            unitparameter=data["Meaning"][function],
            construction=None
        )
        if entry["Source"]:
            add_morpheme_reference(morpheme, entry["Source"])
        
        if cognateset_ID in proto_forms:
            DBSession.add(models.Cognate(
                    cognateset=data["Cognateset"][cognateset_ID],
                    counterpart=morpheme
                )
            )
    
def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodiucally whenever data has been updated.
    """
