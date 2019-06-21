from __future__ import unicode_literals
import sys

from clld.scripts.util import initializedb, Data
from clld.db.meta import DBSession
from clld.db.models import common
from pynterlinear import pynterlinear
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

print("Generating language and construction paradigm information…")
#This will contain a dict to look up the language IDs (and names) based on glottocodes -- the CLLD app uses custom language IDs, but the CLDF files use glottocodes.
LANG_DIC = {}
#This will contain a dict to look up full language names based on shorthand forms (e.g. maqui). This is only used to render markdown.
LANG_ABBREV_DIC = {}
#and this is used to look up language names based on the code. used for trees
LANG_CODE_DIC = {}
for row in cariban_data["LanguageTable"]:
    if row["sampled"] == "y":
        LANG_DIC[row["glottocode"]] = {"ID": row["ID"], "name": row["Name"]}
        LANG_ABBREV_DIC[row["shorthand"]] = {"ID": row["ID"], "name": row["Name"]}
    if row["dialect_of"] == "":
        LANG_CODE_DIC[row["ID"]] = {"shorthand": row["shorthand"], "name": row["Name"]}
print(LANG_CODE_DIC)
#Save to json to make the dic available to util.py
json_file = json.dumps(LANG_ABBREV_DIC)
f = open("LANG_ABBREV_DIC.json","w")
f.write(json_file)
f.close()
from cariban_morphemes import util

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
        publisher_place="",
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
        if row["sampled"] == "y": lg_count+=1
        if row["dialect_of"] not in ["", "y"]:
            dialect_mapping[row["ID"]] = row["dialect_of"]
    print(dialect_mapping)
    i = 0
    for row in cariban_data["LanguageTable"]:
        if row["sampled"] == "y":
            i += 1
            print("%s/%s" % (i, lg_count), end="\r")        
            data.add(
                common.Language,
                row["ID"],
                id=row["ID"],
                name=row["Name"],
                latitude=float(row["Latitude"]) if row["Latitude"] is not None else None,
                longitude=float(row["Longitude"]) if row["Longitude"] is not None else None,
            )
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
    print("")
    
    print("Adding language sources…")    
    language_pks = {}
    for language in DBSession.query(common.Language):
        language_pks[language.id] = language.pk
    source_pks = {}
    for source in DBSession.query(common.Source):
        source_pks[source.id] = source.pk
    language_sources = {}
    mapreader = csv.DictReader(open("../../raw examples/lit_lang_mappings.csv"))
    for row in mapreader:
        DBSession.add(common.LanguageSource(language_pk=language_pks[row["Language_ID"]], source_pk=source_pks[row["Source"]]))
    
    print("Adding glossing abbreviations…")
    length = len(pynterlinear.get_all_abbrevs().keys())
    for i, (key, name) in enumerate(pynterlinear.get_all_abbrevs().items()):
        print("%s/%s" % (i+1, length), end="\r")
        DBSession.add(common.GlossAbbreviation(id=key, name=name))
    print("")    
    
    print("Adding examples…")
    gloss_replacements = {
        "1S": "1.S",
        "2S": "2.S",
        "3S": "3.S",
        "3P": "3.P",
        "1P": "1.P",
        "S_A_": "Sa",
        "S_P_": "Sp"
    }            
    def clldify_glosses(gloss_line):
        output = gloss_line
        for orig, new in gloss_replacements.items():
            output = output.replace(orig,new)
        return output
    
    ex_cnt = 0
    for row in cariban_data["ExampleTable"]:
        ex_cnt+=1
        
    for i, row in enumerate(cariban_data["ExampleTable"]):
        print("%s/%s" % (i+1, ex_cnt), end="\r")
        new_ex = data.add(common.Sentence,
        row["ID"],
        id=row["ID"],
        name=row["Name"],
        description=row["Translated_Text"],
        analyzed="\t".join(row["Analyzed_Word"]),
        gloss=clldify_glosses("\t".join(row["Gloss"])),
        language=data["Language"][LANG_DIC[row["Language_ID"]]["ID"]],
        comment=row["Comment"],
        markup_gloss=row["Morpheme_IDs"].replace(" ","\t")
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
    
    print("Adding morphemes…")
    morph_cnt=0
    for row in cariban_data["FormTable"]:
        morph_cnt+=1
    for i, row in enumerate(cariban_data["FormTable"]):
        print("%s/%s" % (i+1, morph_cnt), end="\r")
        new_morph = data.add(models.Morpheme,
            row["ID"],
            language=data["Language"][LANG_DIC[row["Language_ID"]]["ID"]],
            name="/".join(row["Form"]),
            id=row["ID"],
        )
        if row["Source"]:
            bib_key = row["Source"][0].split("[")[0]
            if len(row["Source"][0].split("[")) > 1:
                pages = row["Source"][0].split("[")[1].split("]")[0]
            else:
                pages = " "    
            if bib_key in data["Source"]:
                source = data["Source"][bib_key]
                DBSession.add(models.MorphemeReference(
                    morpheme=new_morph,
                    source=source,
                    key=source.id,
                    description=pages.replace("--","–")
                    )
                )
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
        models.FiniteType,
        "finite",
        id="finite",
        name="finite"
    )
    
    cons_cnt = 0
    for row in construction_data["FormTable"]:
        cons_cnt += 1
    for i, row in enumerate(construction_data["FormTable"]):
        print("%s/%s" % (i+1, cons_cnt), end="\r")
        data.add(
            models.Construction,
            row["ID"],
            id=row["ID"],
            language=data["Language"][LANG_DIC[row["Language_ID"]]["ID"]],
            name=row["Description"],
            declarativetype=data["DeclarativeType"][row["DeclarativeType"]],
            finitetype=data["FiniteType"][row["FiniteType"]]
        )
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
                            morpheme_function_key = "%s:%s:%s" % (morpheme, function, construction)
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
        for word in row["Morpheme_IDs"].split(" "):
            morph_ids = util.split_word(word)
            for unit_value in morph_ids:
                if unit_value in ["X","-","="]:
                    continue
                unitvaluesentence_key = "{0}-{1}".format(unit_value.replace(".","-"),row["ID"])
                if unitvaluesentence_key in data["UnitValueSentence"].keys():
                    continue
                is_illustrated[unit_value] = True
                morph_id = unit_value.split(":")[0]
                function = unit_value.split(":")[1]
                morph_function_id = "%s:%s" % (morph_id, function)
                if morph_function_id not in data["MorphemeFunction"].keys():
                    print("Example %s tries to illustrate inexistent morpheme function %s!" % (row["ID"], unit_value.replace(".","-")))
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
        new_cset = data.add(models.CognateSet,
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
    shortcut_cognates = {}
    for i, row in enumerate(cariban_data["FormTable"]):
        print("%s/%s" % (i+1, morph_cnt), end="\r")
        shortcut_cognates[row["ID"]] = row["Cognateset_ID"].split("; ")
        #Go through all cognatesets of which this morpheme is a part
        for cognate_ID in row["Cognateset_ID"].split("; "):
            lang_valueset = "%s_%s" % (row["Language_ID"], cognate_ID)
            # print(lang_valueset)
            if lang_valueset not in data["ValueSet"].keys():
                # print("Adding ValueSet for %s, cognate set %s" % (row["Language_ID"], cognate_ID))
                my_valueset = data.add(common.ValueSet,
                    lang_valueset,
                    id=lang_valueset,
                    language=data["Language"][LANG_DIC[row["Language_ID"]]["ID"]],
                    parameter=data["CognateSet"][cognate_ID],
                )
            else:
                my_valueset = data["ValueSet"][lang_valueset]
            my_value = data.add(models.Counterpart,
                cognate_ID+":"+row["ID"],
                valueset=my_valueset,
                name=row["Form"][0],
                description=row["Form"][0],
                markup_description=", ".join(row["Form"]),
                morpheme=data["Morpheme"][row["ID"]]
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
        data["CognateSet"][row["ID"]].markup_description = markup_description=util.generate_markup(row["Description"])
        if row["ID"] == "13pro":
            data["CognateSet"][row["ID"]].markup_description += util.generate_markup(
                util.comparative_function_paradigm(
                    ["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_old"],
                    "1+3 scenarios",
                    ["1+3S", "1+3>3", "3>1+3", "2>1+3", "1+3>2"]))
    print("")
    
    print("Adding trees…")
    tree_path = "../../trees"
    newick_files = {}
    tree_reader = csv.DictReader(open("../cariban_trees.csv"))
    tree_cnt = 0
    for row in tree_reader:
        tree_cnt += 1
        newick_files[row["ID"]] = {
            "orig": row["ID"]+"_orig.newick",
            "norm": row["ID"]+"_norm.newick",
            "source": row["Source"],
            "comment": row["Comment"]
        }
    c = 1
    for tree_id, values in newick_files.items():
        # print("%s/%s" % (c, tree_cnt), end="\r")
        print(tree_id)
        c += 1
        norm_biotree = Phylo.read(tree_path+"/"+values["norm"], "newick")
        orig_biotree = Phylo.read(tree_path+"/"+values["orig"], "newick")
        for node in norm_biotree.find_clades():
            if node.name == None:
                continue
            plain_name = node.name.replace("?","")
            if plain_name in LANG_CODE_DIC.keys():
                node.name = LANG_CODE_DIC[plain_name]["name"]
            else:
                print("Warning: Normalized tree %s has unknown languages %s." % (tree_id, plain_name))
                continue
        edited_tree = io.StringIO()
        Phylo.write(norm_biotree, edited_tree, "newick")
        tree = edited_tree.getvalue().replace(":0.00000","")
        edited_tree = io.StringIO()
        Phylo.write(orig_biotree, edited_tree, "newick")
        orig_tree = edited_tree.getvalue().replace(":0.00000","")
        norm_phylo = Phylogeny(
                id=tree_id+"_norm",
                name=str(data["Source"][values["source"]]) + " (Normalized)",
                markup_description=util.generate_markup("src:"+values["source"]),
                newick=tree
        )
        orig_phylo = Phylogeny(
                id=tree_id+"_orig",
                name=str(data["Source"][values["source"]]) + " (Original)",
                markup_description=util.generate_markup("src:"+values["source"]),
                newick=orig_tree
        )
        for l in DBSession.query(common.Language):
            if l.id in dialect_mapping.keys():
                lname = LANG_CODE_DIC[dialect_mapping[l.id]]["name"]
            else:
                lname = l.name
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
                    
def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodiucally whenever data has been updated.
    """

# main("hihi")
if __name__ == "__main__":  # pragma: no cover
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)
