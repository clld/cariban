from __future__ import unicode_literals
import sys

from clld.scripts.util import initializedb, Data
from clld.db.meta import DBSession
from clld.db.models import common

from pycldf import Wordlist
from clld.lib.bibtex import EntryType
import cariban_morphemes
from cariban_morphemes import models

from clld_glottologfamily_plugin.util import load_families
import clld_cognacy_plugin

cariban_data = Wordlist.from_metadata("../cariban_data.json")

def main(args):
    data = Data()

    dataset = common.Dataset(id=cariban_morphemes.__name__, domain="cariban_morphemes.clld.org")
    DBSession.add(dataset)
    
    lang_dic = {}
    # add languages in the sample to data["Language"]
    for row in cariban_data["LanguageTable"]:
        lang_dic[row["ID"]] = {"abbrev": row["abbrev"], "name": row["Name"]}
        # print(row)
        data.add(
            common.Language,
            row["ID"],
            id=row["ID"],
            name=row["Name"],
            latitude=float(row["Latitude"]) if row["Latitude"] is not None else None,
            longitude=float(row["Longitude"]) if row["Longitude"] is not None else None,
        )
    
    #add sources to data["Sources"]
    for src in cariban_data.sources.items():
            for invalid in ["isbn", "part", "institution"]:
                if invalid in src:
                    del src[invalid]
            data.add(
                common.Source,
                src.id,
                id=src.id,
                name=src.get("author", src.get("editor")),
                description=src.get("title", src.get("booktitle")),
                bibtex_type=getattr(EntryType, src.genre, EntryType.misc),
    **src)
    print(dir(common.Unit))
    # #trying to add morphemes as units instead of values of parameters
    for row in cariban_data["FormTable"]:
        # print("Adding morpheme {0} with ID {1} for language {2}".format(row["Form"],row["ID"],row["Language_ID"]))
        data.add(common.Unit,
            row["ID"],
            language=data["Language"][row["Language_ID"]],
            name=row["Form"],
            description=row["Parameter_ID"],
            id=row["ID"],
            markup_description=row["Cognateset_ID"]
        )
        for morpheme_function in row["Parameter_ID"].split("; "):
            my_key = morpheme_function.replace(".","-")
            if morpheme_function not in data["UnitParameter"].keys():
                # print("Adding a brand new FUNCTION with id %s, name %s!" % (my_key, morpheme_function))
                data.add(common.UnitParameter,
                    morpheme_function,
                    id=my_key,
                    name=morpheme_function
                )
            # print("Adding the function %s to the morpheme %s!" % (data["UnitParameter"][morpheme_function], row["ID"]))
            data.add(common.UnitValue,
                row["ID"]+":"+my_key,
                id=row["ID"]+":"+my_key,
                name=lang_dic[row["Language_ID"]]["name"]+": "+my_key,
                unit=data["Unit"][row["ID"]],
                unitparameter=data["UnitParameter"][morpheme_function]
            )
            # print(data["UnitParameter"][morpheme_function].unitvalues)

    #adding morphemes as valuesets (with single values) and cognacy sets as parameters; not ideal
    for row in cariban_data["FormTable"]:
        if row["Language_ID"] == "cari1283":
            data.add(common.Parameter,row["Cognateset_ID"],name=row["Form"],id=row["Cognateset_ID"])
    # print(dir(common.Unit))      
    for row in cariban_data["FormTable"]:
        if row["Language_ID"] != "cari1283":
            for cognate_ID in row["Cognateset_ID"].split("; "):
                lang_valueset = "%s_%s" % (lang_dic[row["Language_ID"]]["abbrev"], cognate_ID)
                # print(lang_valueset)
                if lang_valueset not in data["ValueSet"].keys():
                    data.add(common.ValueSet,
                        lang_valueset,
                        id=lang_valueset,
                        language=data["Language"][row["Language_ID"]],
                        parameter=data["Parameter"][cognate_ID],
                    )
                for morpheme_function in row["Parameter_ID"].split("; "):
                    my_key = morpheme_function.replace(".","-")
                    data.add(common.Value,
                        row["ID"]+":"+my_key,
                        valueset=data["ValueSet"][lang_valueset],
                        name=row["Form"]+": "+morpheme_function,
                        description=morpheme_function,
                        markup_description=row["Form"]
                    )
                
    
    for row in cariban_data["ExampleTable"]:
        new_ex = data.add(common.Sentence,
        row["ID"],
        id=row["ID"],
        name=row["Name"],
        description=row["Translated_Text"],
        analyzed=" ".join(row["Analyzed_Word"]),
        gloss=" ".join(row["Gloss"]),
        language=data["Language"][row["Language_ID"]],
        comment=row["Comment"]
        # source=data["Source"][row["Source"].split("[")[0]]
        # source=row["Source"]
        )
        if row["Source"]:
            bib_key = row["Source"].split("[")[0]
            if len(row["Source"].split("[")) > 1:
                pages = row["Source"].split("[")[1].split("]")[0]
            else:
                pages = " "    
            if bib_key in data["Source"]:
                source = data["Source"][bib_key]
                DBSession.add(common.SentenceReference(
                    sentence=new_ex,
                    source=source,
                    key=source.id,
                    description=pages)
                    )
        
        #see what morphemes this example illustrates; separated by "; "
        if row["Illustrates_Morpheme"].split("; ") != [""]:
            for unit_value in row["Illustrates_Morpheme"].split("; "):
                unit = unit_value.split(":")[0]
                data.add(common.ValueSentence,
                "{0}-{1}".format(unit,row["ID"]),
                sentence=data["Sentence"][row["ID"]],
                value=data["Value"][unit_value.replace(".","-")],
                )
                data.add(models.UnitValueSentence,
                "{0}-{1}".format(unit_value.replace(".","-"),row["ID"]),
                sentence=data["Sentence"][row["ID"]],
                unitvalue=data["UnitValue"][unit_value.replace(".","-")],
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
