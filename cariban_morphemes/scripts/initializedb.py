from __future__ import unicode_literals
import sys

from clld.scripts.util import initializedb, Data, add_language_codes
from clld.db.meta import DBSession
from clld.db.models import common
import pynterlinear
from pycldf import Wordlist, Generic
from clld.lib.bibtex import EntryType, unescape
from nameparser import HumanName
import cariban_morphemes
from cariban_morphemes import models
import re
from clld.web.util import helpers as h
from clld_phylogeny_plugin.models import Phylogeny, LanguageTreeLabel, TreeLabel
import os
import csv
import json
#to edit tree labels
from Bio import Phylo
import io
from ipapy.ipastring import IPAString

import importlib.util
spec = importlib.util.spec_from_file_location("morph_merge", "/Users/florianm/Dropbox/Stuff/development/morph_merge/__init__.py")
mm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mm)


#This contains lists of:
# morphemes
# Cariban languages
# interlinear examples
# cognate sets
cariban_data = Wordlist.from_metadata("../cariban_morpheme_data.json")

#This contains lists of:
# constructions (clause types)
# morpheme functions in these constructions
construction_data = Generic.from_metadata("../cariban_construction_data.json")

print("Generating language information for markdown…")
#This will contain a dict to look up the language IDs (and names) based on glottocodes -- the CLLD app uses custom language IDs, but the CLDF files use glottocodes.
LANG_DIC = {}
#This will contain a dict to look up full language names based on shorthand forms (e.g. maqui). This is only used to render markdown.
LANG_ABBREV_DIC = {}
#and this is used to look up language names based on the code. used for trees
LANG_CODE_DIC = {}
for row in cariban_data["LanguageTable"]:
    LANG_DIC[row["Glottocode"]] = {"ID": row["ID"], "name": row["Name"]}
    LANG_ABBREV_DIC[row["Shorthand"]] = {"ID": row["ID"], "name": row["Name"]}
    # if row["Dialect_Of"] is None:
    LANG_CODE_DIC[row["ID"]] = {"shorthand": row["Shorthand"], "name": row["Name"]}
    
#Save to json to make the dics available to util.py
json_file = json.dumps(LANG_ABBREV_DIC)
f = open("lang_code_dic.json","w")
f.write(json_file)
f.close()

json_file = json.dumps(LANG_CODE_DIC)
f = open("lang_code_dic.json","w")
f.write(json_file)
f.close()
from cariban_morphemes import util

#To figure out whether a given t-adding verb would have the prefix tɨ- or t-
def t_prefix_form(string):
    initial = IPAString(unicode_string=string, ignore=True)
    if len(initial.consonants) > 0 and initial.consonants[0].is_equivalent(initial[0]):
        return "tɨ"
    else:
        return "t"
        
#This returns a author-year style reference from the bibtex file.
def get_source_name(source):
    year = source.get('year', 'nd')
    fields = {}
    jsondata = {}
    eds = ''
    authors = source.get('author')
    if not authors:
        authors = source.get('editor', '')
        if authors:
            eds = ' (eds.)'
    if authors:
        authors = unescape(authors).split(' and ')
        etal_string = ""
        if len(authors) > 2:
            authors = authors[:1]
            etal_string = " et al."

        authors = [HumanName(a) for a in authors]
        authors = [n.last or n.first for n in authors]
        authors = '%s%s' % (' and '.join(authors), eds)
        authors += etal_string

        return ('%s %s' % (authors, year)).strip()

def main(args):
    data = Data()
    
    print("Setting up dataset…")
    dataset = common.Dataset(id=cariban_morphemes.__name__,
        domain="cariban-morphology.herokuapp.com/",
        name="Cariban Morphology Database",
        description="Cariban Morphology Database",
        publisher_name="Florian Matter",
        publisher_url="http://www.isw.unibe.ch/ueber_uns/personen/ma_matter_florian/index_ger.html",
        publisher_place="University of Bern",
        license="http://creativecommons.org/licenses/by/4.0/",
        contact="florian.matter@isw.unibe.ch"
        )
        
    DBSession.add(dataset)
    
    print("Adding contributors (me)…")
    c = common.Contributor(id="fm",name="Florian Matter")
    dataset.editors.append(common.Editor(contributor=c, ord=1, primary=True))
      
    #Create shorthand lists for the paradigm generator function
    FUNCTION_PARADIGMS = []
    for entry in construction_data["ValueTable"]:
        for function in entry["Function"]:
            for construction in entry["Construction"]:
                function_entry = {
                    "Function": function,
                    "Construction": construction,
                    "Morpheme": entry["Morpheme"]
                }
                FUNCTION_PARADIGMS.append(function_entry)
                
    #Save to json to make the function paradigms available to util.py
    with open('function_paradigms.json', 'w') as fout:
        json.dump(FUNCTION_PARADIGMS, fout)
    
    print("Adding languages…")
    dialect_mapping = {}
    lg_count = 0
    for row in cariban_data["LanguageTable"]:
        if row["Sampled"] == "y": lg_count+=1
        if row["Dialect_Of"] not in [None, "y"]:
            dialect_mapping[row["ID"]] = row["Dialect_Of"]

    i = 0
    for row in cariban_data["LanguageTable"]:
        if row["Sampled"] == "y":# or row["Dialect_Of"] == None:
            i += 1
            print("%s/%s" % (i, lg_count), end="\r")        
            language = data.add(
                common.Language,
                row["ID"],
                id=row["ID"],
                name=row["Name"],
                latitude=float(row["Latitude"]) if row["Latitude"] is not None else None,
                longitude=float(row["Longitude"]) if row["Longitude"] is not None else None,
            )
            add_language_codes(data, language, isocode=row["ISO"], glottocode = row["Glottocode"])
    print("")
       
    print("Adding sources…")
    length = len(cariban_data.sources)
    for i, src in enumerate(cariban_data.sources.items()):
        print("%s/%s" % (i+1, length), end="\r")
        for invalid in ["isbn", "part", "institution"]:
            if invalid in src:
                del src[invalid]
        data.add(
            common.Source,
            src.id,
            id=src.id,
            name=get_source_name(src),
            description=src.get("title", src.get("booktitle")).replace("{","").replace("}",""),
            bibtex_type=getattr(EntryType, src.genre, EntryType.misc),
    **src)
    data.add(
        common.Source,
        "pc",
        id="pc",
        name="Personal communication",
        description="Placeholder for data obtained from personal communication.",
        bibtex_type=EntryType.misc
    )
    print("")

    DBSession.flush()
    print("Adding language sources…")
    mapreader = csv.DictReader(open("../../raw examples/lit_lang_mappings.csv"))
    for row in mapreader:
        if row["Language_ID"] not in data["Language"]: continue
        DBSession.add(
            common.LanguageSource(
                language_pk=data["Language"][row["Language_ID"]].pk,
                source_pk=data["Source"][row["Source"]].pk
            )
        )

    print("Adding glossing abbreviations…")
    length = len(pynterlinear.get_all_abbrevs().keys())
    for i, (key, name) in enumerate(pynterlinear.get_all_abbrevs().items()):
        print("%s/%s" % (i+1, length), end="\r")
        DBSession.add(common.GlossAbbreviation(id=key, name=name))
    print("")

    print("Adding examples…")
    gloss_replacements = {
        "S_A_": "Sa",
        "S_P_": "Sp"
    }
    def clldify_glosses(gloss_line):
        output = gloss_line
        for orig, new in gloss_replacements.items():
            output = output.replace(orig,new)
        output = re.sub(r"(\d)([A-Z])", r"\1.\2", output)
        return output

    ex_cnt = 0
    for row in cariban_data["ExampleTable"]:
        ex_cnt+=1

    for i, row in enumerate(cariban_data["ExampleTable"]):
        if row["Language_ID"] not in LANG_DIC.keys(): continue
        print("%s/%s" % (i+1, ex_cnt), end="\r")
        lang_id = LANG_DIC[row["Language_ID"]]["ID"]
        if lang_id in dialect_mapping:
            lang_id = dialect_mapping[lang_id]
        new_ex = data.add(common.Sentence,
        row["ID"],
        id=row["ID"],
        name=row["Name"],
        description=row["Translated_Text"],
        analyzed="\t".join(row["Analyzed_Word"]),
        gloss=clldify_glosses("\t".join(row["Gloss"])),
        language=data["Language"][lang_id],
        comment=row["Comment"],
        markup_gloss="\t".join(row["Morpheme_IDs"])
        )
        if row["Source"]:
            bib_key = row["Source"].split("[")[0]
            if len(row["Source"].split("[")) > 1:
                pages = row["Source"].split("[")[1].split("]")[0]
            else:
                pages = ""
            if bib_key in data["Source"]:
                source = data["Source"][bib_key]
                DBSession.add(common.SentenceReference(
                    sentence=new_ex,
                    source=source,
                    key=source.id,
                    description=pages.replace("--","–"))
                    )
    print("")
    
    def add_morpheme_reference(morpheme, source_string):
        if len(source_string.split("[")) > 1:
            bib_key = source_string.split("[")[0]
            pages = source_string.split("[")[1].split("]")[0]
        else:
            bib_key = source_string
            pages = ""
        if bib_key in data["Source"]:
            source = data["Source"][bib_key]
            DBSession.add(models.MorphemeReference(
                morpheme=morpheme,
                source=source,
                key=source.id,
                description=pages.replace("--","–")
                )
            )
        elif bib_key == "pc":
            print(type(morpheme.references))
            morpheme.references.append("%s, p.c." % pages)
            # morpheme.source = "%s, p.c." % pages
            
    print("Adding morphemes…")
    morph_cnt=0
    for row in cariban_data["FormTable"]:
        morph_cnt+=1
    for i, row in enumerate(cariban_data["FormTable"]):
        lang_id = LANG_DIC[row["Language_ID"]]["ID"]
        if lang_id in dialect_mapping:
            lang_id = dialect_mapping[lang_id]
        # print("%s/%s" % (i+1, morph_cnt), end="\r")
        form = mm.merge_allomorphs("; ".join(row["Form"])).split("; ")
        new_morph = data.add(models.Morpheme,
            row["ID"],
            morpheme_type="grammatical",
            language=data["Language"][lang_id],
            name="/".join(form),
            id=row["ID"],
        )
        if row["Source"]:
            add_morpheme_reference(new_morph, row["Source"][0])
            # bib_key = row["Source"][0].split("[")[0]
            # if len(row["Source"][0].split("[")) > 1:
            #     pages = row["Source"][0].split("[")[1].split("]")[0]
            # else:
            #     pages = " "
            # if bib_key in data["Source"]:
            #     source = data["Source"][bib_key]
            #     DBSession.add(models.MorphemeReference(
            #         morpheme=new_morph,
            #         source=source,
            #         key=source.id,
            #         description=pages.replace("--","–")
            #         )
            #     )
    print("")
    
    print("Adding constructions…")
    
    data.add(
        models.DeclarativeType,
        "imp",
        id="imp",
        name="imperative"
    )
    
    data.add(
        models.DeclarativeType,
        "decl",
        id="decl",
        name="declarative"
    )
    
    data.add(
        models.MainClauseVerb,
        "y",
        id="y",
        name="main clause verb"
    )
    
    data.add(
        models.MainClauseVerb,
        "n",
        id="n",
        name="subordinate clause verb"
    )
    
    cons_cnt = 0
    for row in construction_data["FormTable"]:
        cons_cnt += 1
    for i, row in enumerate(construction_data["FormTable"]):
        print("%s/%s" % (i+1, cons_cnt), end="\r")
        lang_id = LANG_DIC[row["Language_ID"]]["ID"]
        if lang_id in dialect_mapping:
            lang_id = dialect_mapping[lang_id]
        new_construction = data.add(
            models.Construction,
            row["ID"],
            id=row["ID"],
            language=data["Language"][lang_id],
            name=row["Description"],
            mainclauseverb=data["MainClauseVerb"][row["MainClauseVerb"]],
        )
        if row["DeclarativeType"] != None:
            new_construction.declarativetype = data["DeclarativeType"][row["DeclarativeType"]]
    print("")
    
    print("Adding morpheme functions…")
    for row in construction_data["ValueTable"]:
        for function in row["Function"]:
            my_key = function.replace(".","_")
            if function not in data["Meaning"].keys():
                data.add(models.Meaning,
                    function,
                    id=my_key,
                    name=function
                )
            if len(row["Construction"]) == 0:
                if len(row["Morpheme"]) == 1:
                    for morpheme in row["Morpheme"]:
                        data.add(models.MorphemeFunction,
                            "%s:%s" % (morpheme, function),
                            id="%s:%s" % (morpheme, function.replace(".","_")),
                            name="MorphemeFunction %s:%s"% (morpheme, function.replace(".","_")),
                            unit=data["Morpheme"][morpheme],
                            unitparameter=data["Meaning"][function],
                            construction=None
                        )
            else:
                for construction in row["Construction"]:
                    if len(row["Morpheme"]) == 1 and row["Morpheme"][0] != "?":
                        for morpheme in row["Morpheme"]:
                            if data["Morpheme"][morpheme].language != data["Construction"][construction].language:
                                print("Warning: the %s Morpheme %s is stated to occur in the %s construction %s!" % (
                                data["Morpheme"][morpheme].language,
                                data["Morpheme"][morpheme],
                                data["Construction"][construction].language,
                                data["Construction"][construction]
                                )
                                )
                            morpheme_function_key = "%s:%s:%s" % (morpheme, function, construction)
                            morpheme_function_key = morpheme_function_key.replace(".","_")
                            data.add(models.MorphemeFunction,
                                "%s:%s" % (morpheme, function),
                                id=morpheme_function_key,
                                name="MorphemeFunction %s:%s:%s"% (morpheme, function.replace(".","_"), construction),
                                unit=data["Morpheme"][morpheme],
                                unitparameter=data["Meaning"][function],
                                construction=data["Construction"][construction]
                            )
    
    print("Checking examples for illustrated morphemes…")
    proto_languages = ["pc"]
    is_illustrated = {}
    for key, row in data["MorphemeFunction"].items():
        if row.unit.language.id in proto_languages:
            continue
        is_illustrated["%s:%s" % (row.unit.id, row.unitparameter.id)] = False
    for i, row in enumerate(cariban_data["ExampleTable"]):
        print("%s/%s" % (i+1, ex_cnt), end="\r")
        # see what morphemes this example illustrates; separated by "; "
        for word in row["Morpheme_IDs"]:
            morph_ids = util.split_word(word)
            for unit_value in morph_ids:
                if unit_value in ["X","-","="]:
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
    print("")

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
    
    cogset_cnt = 0
    for row in cariban_data["CognatesetTable"]:
        cogset_cnt+=1
    print("Adding cognate sets…")
    for i, row in enumerate(cariban_data["CognatesetTable"]):
        print("%s/%s" % (i+1, cogset_cnt), end="\r")
        new_cset = data.add(models.Cognateset,
                row["ID"],
                id=row["ID"],
                name=row["Name"],
                description=row["Function"],
        )
        if row["Source"]:
            bib_key = row["Source"][0].split("[")[0]
            if len(row["Source"][0].split("[")) > 1:
                pages = row["Source"][0].split("[")[1].split("]")[0]
            else:
                pages = " "    
            if bib_key in data["Source"]:
                source = data["Source"][bib_key]
                DBSession.add(models.CognatesetReference(
                    cognateset=new_cset,
                    source=source,
                    key=source.id,
                    description=pages)
                    )
    print("")
    
    print("Adding cognates…")
    for i, row in enumerate(cariban_data["FormTable"]):
        print("%s/%s" % (i+1, morph_cnt), end="\r")
        #Go through all cognatesets of which this morpheme is a part
        for cognate_ID in row["Cognateset_ID"]:
            DBSession.add(models.Cognate(
                    cognateset=data["Cognateset"][cognate_ID],
                    counterpart=data["Morpheme"][row["ID"]]
                )
            )
    print("")
    
    print("Adding morpheme comments…")
    for i, row in enumerate(cariban_data["FormTable"]):
        print("%s/%s" % (i+1, morph_cnt), end="\r")
        data["Morpheme"][row["ID"]].markup_description=util.generate_markup(row["Comment"])
    print("")

    print("Adding constructions descriptions…")
    for i, row in enumerate(construction_data["FormTable"]):
        print("%s/%s" % (i+1, cons_cnt), end="\r")
        if row["Comment"] is None:
            description = ""
        else:
            description = util.generate_markup(row["Comment"])
        description += "\n" + util.generate_markup(util.transitive_construction_paradigm(row["ID"]))
        description += util.generate_markup(util.intransitive_construction_paradigm(row["ID"]))
        data["Construction"][row["ID"]].markup_description = description
    print("")

    print("Adding cognate set descriptions…")
    for i, row in enumerate(cariban_data["CognatesetTable"]):
        print("%s/%s" % (i+1, cogset_cnt), end="\r")
        data["Cognateset"][row["ID"]].markup_description = util.generate_markup(row["Description"])
        if row["ID"] == "13pro":
            data["Cognateset"][row["ID"]].markup_description += util.generate_markup(
                util.comparative_function_paradigm(
                    ["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_old", "kax_main"],
                    "1+3 scenarios",
                    ["1+3S", "1+3>3", "3>1+3", "2>1+3", "1+3>2"]))
    print("")

    print("Adding trees…")
    tree_path = "../../trees"
    newick_files = {}
    tree_reader = csv.DictReader(open("../cariban_trees.csv"))
    tree_cnt = 0
    own_trees = ["matter", "auto_tree", "lingpy_tree"]
    for row in tree_reader:
        if row["ID"] in own_trees: continue
        tree_cnt += 1
        newick_files[row["ID"]] = {
            "orig": row["ID"]+"_orig.newick",
            "norm": row["ID"]+"_norm.newick",
            "source": row["Source"],
            "comment": row["Comment"],
            "o_comment": row["Orig_Comment"]
        }
    #adding my own tree separately.
    for my_tree_count, tree_id in enumerate(own_trees):
        tree_cnt += 1
        print(tree_id)
        my_tree = Phylo.read(tree_path+"/"+"%s.newick" % tree_id, "newick")
        edited_tree = io.StringIO()
        Phylo.write(my_tree, edited_tree, "newick")
        tree = edited_tree.getvalue().replace(":0.00000","")
        my_phylo = Phylogeny(
                tree_id,
                id=tree_id,
                name="Matter (2019), Tree %s" % str(my_tree_count+1),
                newick=tree
        )
        DBSession.add(my_phylo)
    c = 1
    for tree_id, values in newick_files.items():
        print("%s/%s" % (c, tree_cnt), end="\r")
        c += 1
        norm_biotree = Phylo.read(tree_path+"/"+values["norm"], "newick")
        orig_biotree = Phylo.read(tree_path+"/"+values["orig"], "newick")
        uncertain_nodes = []
        for node in norm_biotree.find_clades():
            if node.name == None or not node.is_terminal():
                continue
            plain_name = node.name.replace("?","")
            if "?" in node.name: uncertain_nodes.append(plain_name)
            if plain_name in LANG_CODE_DIC.keys():
                node.name = LANG_CODE_DIC[plain_name]["name"]
            else:
                print("Warning: Normalized tree %s has unknown languages %s." % (tree_id, plain_name))
            if plain_name in uncertain_nodes: node.name += "?"
        edited_tree = io.StringIO()
        Phylo.write(norm_biotree, edited_tree, "newick")
        tree = edited_tree.getvalue().replace(":0.00000","")
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
                newick=tree
        )
        orig_phylo = Phylogeny(
                id=tree_id+"_orig",
                name=str(data["Source"][values["source"]]) + " (Original)",
                markup_description=util.generate_markup("Source: src:"+values["source"])+
                    "<br>This is a representation of the original classification. A normalized version can be found <a href='/phylogeny/%s_norm'>here</a>." % tree_id +
                    util.generate_markup(
                    "<br>Comments: %s" % values["comment"] +
                    " " + values["o_comment"]
                    ),
                newick=orig_tree
        )
        for l in DBSession.query(common.Language):
            if l.id in dialect_mapping.keys():
                lname = LANG_CODE_DIC[dialect_mapping[l.id]]["name"]
            else:
                lname = l.name
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
    print("")

    print("Adding pages…")
    data.add(models.Page,
                    "1+3",
                    id="1+3",
                    name="Person marking in 1+3 scenarios",
                    description="this page discusses person marking in 1+3 scenarios, something missing from many descriptions of Cariban languages.",
            )

    data.add(models.Page,
                    "pre_pc",
                    id="pre_pc",
                    name="Reconstruction of pre-Proto-Cariban person marking",
                    description="Speculative exploration of what developments might have led to the reconstructed PC person paradigms.",
            )
    data.add(models.Page,
                    "t_adding_verbs",
                    id="t_adding_verbs",
                    name="t-adding verbs",
                    description="",
            )
    
    
    print("Creating Set I LaTeX and csv tables…")
    main_clauses = ["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_pstpfv", "ing_old", "bak_main", "yuk_imm", "mac_new_imp", "pem_old", "kax_main", "aku_main"]
    main_clause_markers = [["Language_ID", "Feature_ID", "Value"]]
    
    for morpheme_function in FUNCTION_PARADIGMS:
        # if ("1+3" in morpheme_function["Function"] and "2" in morpheme_function["Function"]) or morpheme_function["Construction"] not in main_clauses:
        if morpheme_function["Construction"] not in main_clauses or morpheme_function["Morpheme"][0] == "?" or "1+3" in morpheme_function["Function"]:
            continue
        cognate_sets = []
        for morph in morpheme_function["Morpheme"]:
            if morph == "?":
                continue
            else:
                for counterpart in data["Morpheme"][morph].counterparts:
                    cognate_sets.append(counterpart.cognateset.id)
        main_clause_markers.append([
            data["Construction"][morpheme_function["Construction"]].language.id,
            morpheme_function["Function"],
            ":".join(cognate_sets)
        ])
        
    with open("/Users/florianm/Dropbox/Uni/Research/LiMiTS/trees/phylo_tree/feature_files/setone.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(main_clause_markers)
        
    for clause in main_clauses:
        lang_id = data["Construction"][clause].language.id
        
        table_file = open("../../thesis/tables/transitive/%s_tr.tex" % lang_id, "w")
        table_file.write(util.latex_table(util.transitive_construction_paradigm(clause, html=False)))
        table_file.close()
        
        table_file = open("../../thesis/tables/intransitive/%s_intr.tex" % lang_id, "w")
        table_file.write(util.latex_table(util.intransitive_construction_paradigm(clause, html=False)))
        table_file.close()
        
        table_file = open("../../thesis/tables/%s_person_marking.tex" % lang_id, "w")
        table_file.write("""\\begin{table}
\\caption{\\%s person marking}
\\label{tab:%s_person}
\\begin{minipage}{0.69\\textwidth}
\\centering
\\subcaption{transitive}
\\label{tab:%s_tr}
\input{tables/transitive/%s_tr.tex}
\\end{minipage}
\\hfill
\\begin{minipage}{0.29\\textwidth}
\\centering
\\subcaption{intransitive}
\\label{tab:%s_intr}
\input{tables/intransitive/%s_intr.tex}
\\end{minipage}
\\end{table}""" % (LANG_CODE_DIC[lang_id]["shorthand"], lang_id, lang_id, lang_id, lang_id, lang_id))
        table_file.close()

    print("Adding t-adding verb cognate sets…")
    t_reader = csv.DictReader(open("../cariban_t_cognates.csv"))
    for row in t_reader:
        cognate_ID = "t"+row["ID"]
        rec_t_form = "*[%s]%s" % (t_prefix_form(row["Form"]), row["Form"])
        t_cogset = data.add(models.Cognateset,
            cognate_ID,
            id=cognate_ID,
            name=rec_t_form,
            description="t-adding verb: ‘%s’" % row["Meaning"]
        )
        if row["Source"]:
            bib_key = row["Source"].split("[")[0]
            if len(row["Source"].split("[")) > 1:
                pages = row["Source"].split("[")[1].split("]")[0]
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
    
    print("Adding swadesh lists…")
    proto_forms = {}
    proto_reader = csv.DictReader(open("../../trees/phylo_tree/cariban_reconstructions.csv"))
    for row in proto_reader:
        proto_forms[row["ID"]] = row["Form"]
    swadesh_reader = csv.DictReader(open("../../trees/phylo_tree/cariban_swadesh_list.csv"))
    for row in swadesh_reader:
        cognate_ID = row["Feature_ID"]+"-"+row["Cognate_ID"]
        if cognate_ID in proto_forms:
            form = "*" + proto_forms[cognate_ID]
        else:
            form = ""
        if cognate_ID not in data["Cognateset"]:
            swadesh_cogset = data.add(models.Cognateset,
                cognate_ID,
                id=cognate_ID,
                name=form,
            )
                    
    first_found = []
    swadesh_reader = csv.DictReader(open("../../trees/phylo_tree/cariban_swadesh_list.csv"))
    for row in swadesh_reader:
        if row["Language_ID"] not in data["Language"].keys(): continue
        function = row["Feature_ID"].replace(".","_")
        morph_id = row["Language_ID"] + "_" + function
        cognate_ID = row["Feature_ID"]+"-"+row["Cognate_ID"]
        if morph_id in first_found: continue
        first_found.append(morph_id)
        if function not in data["Meaning"].keys():
            data.add(models.Meaning,
                function,
                id=function,
                name=function
            )
        morpheme = data.add(models.Morpheme,
                    morph_id,
                    id=morph_id,
                    morpheme_type="lexical",
                    name=row["Value"],
                    language=data["Language"][row["Language_ID"]],
                )
        data.add(models.MorphemeFunction,
            "%s:%s" % (morph_id, function),
            id="%s:%s" % (morph_id, function),
            name="MorphemeFunction %s:%s"% (morph_id, function),
            unit=data["Morpheme"][morph_id],
            unitparameter=data["Meaning"][function],
            construction=None
        )
        if row["Source"]:
            add_morpheme_reference(morpheme, row["Source"])
            
        DBSession.add(models.Cognate(
                cognateset=data["Cognateset"][cognate_ID],
                counterpart=morpheme
            )
        )
    
    print("Adding t-adding verbs…")
    t_langs = {}
    t_verbs = {}
    non_t_adding_lgs = ["ing","mac","kar","wmr","pan"]
    data.add(models.Meaning,
        "t_verb",
        id="t-verb",
        name="t-adding verb"
    )
    t_reader = csv.DictReader(open("../cariban_t_verbs.csv"))
    for row in t_reader:
        if row["Language_ID"] == "cari1283": continue
        cognate_ID = "t"+row["Cognateset_ID"]
        lang_id = LANG_DIC[row["Language_ID"]]["ID"]
        if lang_id in dialect_mapping:
            lang_id = dialect_mapping[lang_id]
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
            name=row["Form"],
            language=data["Language"][lang_id],
        )
        DBSession.add(models.Cognate(
                cognateset=data["Cognateset"][cognate_ID],
                counterpart=t_verb
            )
        )
        if row["t?"] == "y":
            t_verb.name = "[%s]%s" % (t_prefix_form(t_verb.name), t_verb.name)
            t_verb.markup_description = util.generate_markup("Shows cogset:t")
        if row["t?"] == "?" and lang_id not in non_t_adding_lgs:
            t_verb.name = "[t-?]"+t_verb.name
            t_verb.markup_description = util.generate_markup("It is not known if this verb shows cogset:t")
        if row["t?"] == "n":
            t_verb.markup_description = util.generate_markup("Does not show cogset:t")
        if lang_id not in t_langs.keys():
            t_langs[lang_id] = {
                "y": 0,
                "n": 0,
                "?": 0
            }
        if cognate_ID not in t_verbs.keys():
            t_verbs[cognate_ID] = {
                "y": 0,
                "n": 0,
                "?": 0
            }
        t_langs[lang_id][row["t?"]] += 1
        if lang_id not in non_t_adding_lgs:
            t_verbs[cognate_ID][row["t?"]] += 1
        if row["Source"]:
            add_morpheme_reference(t_verb, row["Source"])
            
        data.add(models.MorphemeFunction,
            "t_"+row["ID"],
            id="t_"+row["ID"],
            name="t-Verb %s" % row["Meaning"],
            unit=t_verb,
            unitparameter=data["Meaning"]["t_verb"],
            construction=None
        )
    for lang, values in t_langs.items():
        data["Language"][lang].update_jsondata(t_values=values)
    for verb, values in t_verbs.items():
        data["Cognateset"][verb].description += " (%s/%s)" % (str(values["y"]), str(values["n"]+values["y"]+values["?"]))
        data["Cognateset"][verb].markup_description = util.generate_markup("This verb occurs with obj:t- in %s of %s languages which show reflexes of cogset:t." % (str(values["y"]), str(values["n"]+values["y"]+values["?"])))
            
def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodiucally whenever data has been updated.
    """

# main("hihi")
if __name__ == "__main__":  # pragma: no cover
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)
