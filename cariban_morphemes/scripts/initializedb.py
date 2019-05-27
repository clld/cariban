from __future__ import unicode_literals
import sys

from clld.scripts.util import initializedb, Data
from clld.db.meta import DBSession
from clld.db.models import common
from cariban_morphemes import util
from pycldf import Wordlist
from clld.lib.bibtex import EntryType, unescape
from nameparser import HumanName
import cariban_morphemes
from cariban_morphemes import models
import re
from clld.web.util import helpers as h

from clld_glottologfamily_plugin.util import load_families

cariban_data = Wordlist.from_metadata("../cariban_data.json")
        
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
        if len(authors) > 2:
            authors = authors[:1]

        authors = [HumanName(a) for a in authors]
        authors = [n.last or n.first for n in authors]
        authors = '%s%s' % (' and '.join(authors), eds)

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
    
    print("Adding languages…")
    lang_dic = {}
    lang_abbrev_dic = {}
    lg_count = 0
    for row in cariban_data["LanguageTable"]:
        lg_count+=1
    for i, row in enumerate(cariban_data["LanguageTable"]):
        print("%s/%s" % (i+1, lg_count), end="\r")
        if row["sampled"] != "y":
            continue
        lang_dic[row["glottocode"]] = {"ID": row["ID"], "name": row["Name"]}
        lang_abbrev_dic[row["shorthand"]] = {"ID": row["ID"], "name": row["Name"]}
        data.add(
            common.Language,
            row["ID"],
            id=row["ID"],
            name=row["Name"],
            latitude=float(row["Latitude"]) if row["Latitude"] is not None else None,
            longitude=float(row["Longitude"]) if row["Longitude"] is not None else None,
        )
    print("")
    print(lang_dic)

       
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
            description=src.get("title", src.get("booktitle")),
            bibtex_type=getattr(EntryType, src.genre, EntryType.misc),
    **src)
    print("")

        
    print("Adding glossing abbreviations…")
    gloss_txt = open("/Users/florianm/Dropbox/Stuff/development/interlinear_text_tools/glossing.txt", "r").read()
    length = len(gloss_txt.split("\n"))
    for i, glossline in enumerate(gloss_txt.split("\n")):
        print("%s/%s" % (i+1, length), end="\r")
        key = glossline.split("\t")[0].upper()
        name = glossline.split("\t")[1]
        DBSession.add(common.GlossAbbreviation(id=key, name=name))
    print("")    
    
    print("Adding examples…")
    gloss_replacements = {
        "1S": "1.S",
        "2S": "2.S",
        "3S": "3.S",
        "3P": "3.P",
        "1P": "1.P",
        "S_A_": "SA",
        "S_P_": "SP"
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
        # print(lang_dic[row["Language_ID"]]["ID"])
        new_ex = data.add(common.Sentence,
        row["ID"],
        id=row["ID"],
        name=row["Name"],
        description=row["Translated_Text"],
        analyzed="\t".join(row["Analyzed_Word"]),
        gloss=clldify_glosses("\t".join(row["Gloss"])),
        language=data["Language"][lang_dic[row["Language_ID"]]["ID"]],
        comment=row["Comment"],
        markup_gloss=row["Morpheme_IDs"].replace(" ","\t")
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
    print("")
    
    cognate_sets = {}
    cogset_cnt = 0
    for row in cariban_data["CognatesetTable"]:
        cognate_sets[row["ID"]] = name=row["Name"]
        cogset_cnt+=1
        
    def generate_markup(non_f_str: str):
        if non_f_str is None:
            return ""
            
        substitutions = {
            "morph:([a-z\_0-9]*)\|?([\u00BF-\u1FFF\u2C00-\uD7FF\(\)\w]*[\-\=]?)": r"{morph_lk('\1','\2')}",
            "lg:([a-z]*)": r"{lang_lk('\1')}",
            "cogset:([a-z\_0-9]*)": r"{cogset_lk('\1')}",
            "src:([a-z\_0-9\[\]\-]*)": r"{src_lk('\1')}",
            "ex:([a-z\_0-9\-]*)": r"{render_ex('\1')}",
        }
        for orig, sub in substitutions.items():
            non_f_str = re.sub(orig, sub, non_f_str)
                
        def lang_lk(shorthand):
            if shorthand in lang_abbrev_dic.keys():
                return "<a href='/languages/%s' >%s</a>" % (lang_abbrev_dic[shorthand]["ID"], lang_abbrev_dic[shorthand]["name"])
            else:
                return "<a href='/languages/%s' >%s</a>" % (shorthand, data["Language"][shorthand].name)            
                
        def cogset_lk(cogset_id, text=""):
            if text == "":
                return "<a href='/cognateset/%s' >%s</a>" % (cogset_id, cognate_sets[cogset_id])
            else:
                return "<a href='/cognateset/%s' >%s</a>" % (cogset_id, text)
    
        def src_lk(source):
            bib_key = source.split("[")[0]
            if len(source.split("[")) > 1:
                pages = source.split("[")[1].split("]")[0]
                return "<a href='/sources/%s' >%s: %s</a>" % (bib_key, get_source_name(cariban_data.sources[bib_key]), pages)
            else:
                return "<a href='/sources/%s' >%s</a>" % (bib_key, get_source_name(cariban_data.sources[bib_key]))

        def morph_lk(morph_id, form=""):
            if form == "":
                form = data["Morpheme"][morph_id].name
            return "<i><a href='/morpheme/%s' >%s</a></i>" % (morph_id, form)
            
        def render_ex(ex_id):
            
            print(data["Sentence"][ex_id].references[0].source.id)
            return """
                <blockquote style='margin-top: 5px;'>
                %s (%s)
                    %s
                </blockquote>""" % (lang_lk(data["Sentence"][ex_id].language.id), src_lk("%s[%s]" % (data["Sentence"][ex_id].references[0].source.id, data["Sentence"][ex_id].references[0].description)), util.rendered_sentence(data["Sentence"][ex_id]))
                
        return eval(f'f"""{non_f_str}"""')
    
    print("Adding morphemes…")
    morph_cnt=0
    for row in cariban_data["FormTable"]:
        morph_cnt+=1
    for i, row in enumerate(cariban_data["FormTable"]):
        print("%s/%s" % (i+1, morph_cnt), end="\r")    
        data.add(models.Morpheme,
            row["ID"],
            language=data["Language"][lang_dic[row["Language_ID"]]["ID"]],
            name=", ".join(row["Form"]),
            description=", ".join(row["Parameter_ID"]),
            markup_description=generate_markup(row["Description"]),
            id=row["ID"],
        )
        for morpheme_function in row["Parameter_ID"]:
            my_key = morpheme_function.replace(".","_")
            #Check if there is already such a function (meaning) defined
            if morpheme_function not in data["Meaning"].keys():
                # print("Adding a brand new FUNCTION with id %s, name %s!" % (my_key, morpheme_function))
                data.add(models.Meaning,
                    morpheme_function,
                    id=my_key,
                    name=morpheme_function
                )
            # print("Adding the function %s to the morpheme %s!" % (data["UnitParameter"][morpheme_function], row["ID"]))
            #This is the "MorphemeFunction" linking a Morpheme (Unit) with a Meaning (UnitParameter)
            data.add(common.UnitValue,
                row["ID"]+":"+my_key,
                id=row["ID"]+":"+my_key,
                name=lang_dic[row["Language_ID"]]["name"]+": "+my_key,
                unit=data["Morpheme"][row["ID"]],
                unitparameter=data["Meaning"][morpheme_function]
            )
    print("")
    
    print("Checking examples for illustrated morphemes…")
    proto_languages = ["pc"]
    is_illustrated = {}
    for key, row in data["UnitValue"].items():
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
                if unit_value.replace(".","-") not in data["UnitValue"].keys():
                    print("Example %s tries to illustrate inexistent morpheme function %s!" % (row["ID"], unit_value.replace(".","-")))
                    continue
                data.add(models.UnitValueSentence,
                unitvaluesentence_key,
                sentence=data["Sentence"][row["ID"]],
                unitvalue=data["UnitValue"][unit_value.replace(".","-")],
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
                
    print("Adding cognate sets…")
    for i, row in enumerate(cariban_data["CognatesetTable"]):
        print("%s/%s" % (i+1, cogset_cnt), end="\r")
        new_cset = data.add(models.CognateSet,
                row["ID"],
                id=row["ID"],
                name=row["Name"],
                markup_description=generate_markup(row["Description"])
        )
        if row["Source"]:
            for source in row["Source"]:
                bib_key = source.split("[")[0]
                if len(source.split("[")) > 1:
                    pages = source.split("[")[1].split("]")[0]
                else:
                    pages = " "    
                if bib_key in data["Source"]:
                    new_cset.source = data["Source"][bib_key]
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
                    language=data["Language"][lang_dic[row["Language_ID"]]["ID"]],
                    parameter=data["CognateSet"][cognate_ID],
                )
            else:
                my_valueset = data["ValueSet"][lang_valueset]
            my_value = data.add(models.Counterpart,
                cognate_ID+":"+row["ID"],
                valueset=my_valueset,
                name=row["Form"][0]+": "+", ".join(row["Parameter_ID"]),
                description=row["Form"][0],
                markup_description=", ".join(row["Form"]),
                morpheme=data["Morpheme"][row["ID"]]
            )
    print("")              
    
def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodiucally whenever data has been updated.
    """

# main("hihi")
if __name__ == "__main__":  # pragma: no cover
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)
