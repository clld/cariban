# coding: utf8
from __future__ import unicode_literals
import re

from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from markupsafe import Markup

from clld.lib.bibtex import EntryType, unescape
from nameparser import HumanName
import clld
from clld import interfaces
from clld import RESOURCES
from clld.web.util.htmllib import HTML, literal
from clld.web.util.downloadwidget import DownloadWidget
from clld.db.meta import DBSession
from clld.db.models import common as models
from clld.web.adapters import get_adapter, get_adapters
from clld.web.util import helpers as h
from clld.lib.coins import ContextObject
from clld.lib import bibtex
from clld.lib import rdf
from cariban.models import Morpheme, Construction, Cognateset
from clld.db.models import Language, Source, Sentence
import cariban.models as cariban_models
from clld_phylogeny_plugin.models import Phylogeny, LanguageTreeLabel, TreeLabel

from cariban.config import LANG_ABBREV_DIC, FUNCTION_PARADIGMS, LANG_CODE_DIC
language_names = {}
for key, values in LANG_CODE_DIC.items():
    language_names[values["shorthand"]] = values["name"]
sampled_languages = {}
for key, values in LANG_ABBREV_DIC.items():
    sampled_languages[values["ID"]] = values["name"]

from collections import OrderedDict
from clld.web.util.multiselect import CombinationMultiSelect
import json
from Bio import Phylo
import csv
import io
# from pynterlinear import pynterlinear


separators = ["-", "=", "<", ">"]
def extract_allomorphs(full_string):
    portions = full_string.split("/")
    found_allomorphs = []
    def iter_parens(string):
        lose = re.sub("\((.*?)\)", r"\1", string, 1)
        keep = re.sub("\((.*?)\)", "", string, 1)
        if "(" in lose:
            iter_parens(lose)
        else:
            found_allomorphs.append(lose)
        if "(" in keep:
            iter_parens(keep)
        else:
            found_allomorphs.append(keep)
    for string in portions:
        iter_parens(string)
    return list(dict.fromkeys(found_allomorphs))

def merge_allomorphs(form):
    allomorphs = form.split("; ")
    if allomorphs[0][-1] in separators:
        prefix = True
        suffix = False
    elif allomorphs[0][0] in separators:
        prefix = False
        suffix = True
    else:
        prefix = False
        suffix = False
    allomorphs.sort(key=len)
    #We take the shortest allomorph as the base
    new_allomorphs = [allomorphs[0]]
    #Then we iterate the longer allomorphs
    for allomorph in allomorphs[1:]:
        #If there is an affricate, let's just add it straight away, we don't want to split these up
        if "͡" in allomorph:
            new_allomorphs.append(allomorph)
            continue
        found_hit = False
        #We iterate the allomorphs we already added to the new form
        for i, existing_allomorph in enumerate(new_allomorphs):
            # if found_hit:
            #     print("Aborting…")
            if not found_hit:
                # print("Looking at candidate %s, comparing it with %s" % (allomorph, existing_allomorph))
                if prefix:
                    right_border = len(allomorph)-2
                else:
                    right_border = len(allomorph)-1
                if suffix:
                    left_border = 1
                else:
                    left_border = 0
                for right_edge in range(right_border, -1, -1):
                    for left_edge in range(left_border, right_edge+1):
                        if left_edge == right_edge:
                            allo_slice = allomorph[left_edge]
                        else:
                            allo_slice = allomorph[left_edge:right_edge+1]
                        if suffix:
                            preserve = existing_allomorph[1::]
                        elif prefix:
                            preserve = existing_allomorph[0:-1]
                        else:
                            preserve = existing_allomorph
                        comp = preserve.replace("(","").replace(")","")
                        # print(f"Comparing {allo_slice} with {comp} [{left_edge}:{right_edge}]")
                        if allo_slice == comp:
                            # print(f"Got a hit! {allo_slice} in position {left_edge}:{right_edge} of {allomorph} is identical to {comp} ({existing_allomorph})")
                            new_allomorph = "(" + allomorph[:left_edge] + ")" + preserve + "(" + allomorph[right_edge+1:] + ")"
                            new_allomorph = new_allomorph.replace("-)", ")-")
                            new_allomorph = new_allomorph.replace("()","")
                            new_allomorphs[i] = new_allomorph
                            # print(new_allomorphs)
                            found_hit = True
        if not found_hit:
            # print("No match found between %s and %s" % (allomorph, existing_allomorph))
            new_allomorphs.append(allomorph)
    for i, new_allomorph in enumerate(new_allomorphs):
        for j, other_allomorph in enumerate(new_allomorphs):
            if i != j:
                if new_allomorph in extract_allomorphs(other_allomorph):
                    # print(f"removing {new_allomorph}, as it is an allomorph of {other_allomorph}")
                    new_allomorphs.remove(new_allomorph)
    return "; ".join(new_allomorphs)
    
def xify(text):
    ids = []
    for word in text.split(" "):
        ids.append(re.sub(r'([X])\1+', r'\1', re.sub("[^(\-|\=|\~)|]", "X", word)))
    return " ".join(ids)
    
# # regex to match standard abbreviations in gloss units:
# # We look for sequences of uppercase letters which are not followed by a lowercase letter.
GLOSS_ABBR_PATTERN = re.compile(
    '(?P<personprefix>1|2|3)?(?P<abbr>[A-Z]+)(?P<personsuffix>1|2|3)?(?=([^a-z]|$))')
ALT_TRANSLATION_LANGUAGE_PATTERN = re.compile(r'((?P<language>[a-zA-Z\s]+):)')
#
def split_word(word):
    output = []
    char_list = list(word)
    for i, char in enumerate(char_list):
        if len(output) == 0 or (char in ["-", "=", "~"] or output[-1] in ["-", "=", "~"]):
            output.append(char)
        else:
            output[-1]+=char
    return output

# this is a clone of a function from clld/helpers.py, with morpheme links built in
# #
# # TODO: enumerate exceptions: 1SG, 2SG, 3SG, ?PL, ?DU
# #
def rendered_sentence(sentence, abbrs=None, fmt='long', lg_name=False, src=False):
    """Format a sentence as HTML."""
    if sentence.xhtml:
        return HTML.div(
            HTML.div(Markup(sentence.xhtml), class_='body'), class_="sentence")

    if abbrs is None:
        q = DBSession.query(models.GlossAbbreviation).filter(
            or_(models.GlossAbbreviation.language_pk == sentence.language_pk,
                models.GlossAbbreviation.language_pk == None)
        )
        abbrs = dict((g.id, g.name) for g in q)

    def gloss_with_tooltip(gloss):
        person_map = {
            '1': 'first person',
            '2': 'second person',
            '3': 'third person',
        }

        res = []
        end = 0
        for match in GLOSS_ABBR_PATTERN.finditer(gloss):
            if match.start() > end:
                res.append(gloss[end:match.start()])

            abbr = match.group('abbr')
            if abbr in abbrs:
                explanation = abbrs[abbr]
                if match.group('personprefix'):
                    explanation = '%s %s' % (
                        person_map[match.group('personprefix')], explanation)

                if match.group('personsuffix'):
                    explanation = '%s %s' % (
                        explanation, person_map[match.group('personsuffix')])

                res.append(HTML.span(
                    HTML.span(gloss[match.start():match.end()].lower(), class_='sc'),
                    **{'data-hint': explanation, 'class': 'hint--bottom'}))
            else:
                res.append(abbr)

            end = match.end()

        res.append(gloss[end:])
        return filter(None, res)

    def alt_translation(sentence):
        res = ''
        if sentence.jsondata.get('alt_translation'):
            text = sentence.jsondata['alt_translation']
            name = ''
            if ALT_TRANSLATION_LANGUAGE_PATTERN.match(text):
                name, text = [t.strip() for t in text.split(':', 1)]
                name = HTML.span(name + ': ')
            res = HTML.div(name, HTML.span(text, class_='translation'))
        return res

    units = []
    if sentence.analyzed and sentence.gloss:
        analyzed = sentence.analyzed
        glossed = sentence.gloss
        if sentence.markup_gloss:
            analyzed_words = sentence.markup_gloss
        else:
            analyzed_words = glossed
        for word, gloss, morph_id in zip(analyzed.split('\t'), glossed.split('\t'), analyzed_words.split("\t")):
            obj_morphs = split_word(word)
            if sentence.markup_gloss:
                gloss_morphs = split_word(morph_id)
                for i, morph in enumerate(gloss_morphs):
                    if morph not in ["X","-","="]:
                        obj_morphs[i] = HTML.a(obj_morphs[i], href="/morpheme/%s" % morph.split(":")[0])
            parsed_word = HTML.text(*obj_morphs)
            gloss_morphs = re.split("[-|=]", gloss)
            units.append(HTML.div(
                HTML.div(parsed_word, class_='word'),
                HTML.div(*gloss_with_tooltip(gloss), **{'class': 'gloss'}),
                class_='gloss-unit'))
                    
    return HTML.div(
        HTML.div(
            HTML.div(
                HTML.div(sentence.original_script, class_='original-script')
                if sentence.original_script else '',
                HTML.div(literal(sentence.markup_text or sentence.name), class_='object-language')
                if sentence.name != sentence.analyzed.replace("\t", " ") else '',
                HTML.div(*units, **{'class': 'gloss-box'}) if units else '',
                HTML.div(sentence.description, class_='translation')
                if sentence.description else '',
                alt_translation(sentence),
                class_='body',
            ),
            class_="sentence",
        ),
        class_="sentence-wrapper",
    )
        
def generate_markup(non_f_str: str, html=True):
    return non_f_str
    ex_cnt = 0

    if non_f_str is None:
        return ""
        
    substitutions = {
        "'(.*?)'": r"‘\1’",
        "morph:([a-z\_0-9]*)\|?([\u00BF-\u1FFF\u2C00-\uD7FF\(\)\w]*[\-\=]?)": r"{morph_lk('\1','\2')}",
        "lg:([a-z]*)": r"{lang_lk('\1')}",
        "cons:([a-z\_]*)": r"{cons_lk('\1')}",
        "cogset:([a-z\_0-9]*)": r"{cogset_lk('\1')}",
        "src:([a-z\_0-9\[\]\-]*)": r"{src_lk('\1')}",
        "ex:([a-z\_0-9\-]*)": r"{render_ex('\1')}",
        "obj:([\w\-\(\)]*)": r"<i>\1</i>",
        "rc:([\w\-\(\)]*)": r"<i>*\1</i>",
    }
    for orig, sub in substitutions.items():
        non_f_str = re.sub(orig, sub, non_f_str)
    
    def cons_lk(shorthand):
        cons = DBSession.query(Construction).filter(Construction.id == shorthand)[0]
        return "<a href='/construction/%s'>%s</a>" % (shorthand, cons.language.name + " " + cons.name + " clause")
                
    def lang_lk(shorthand):
        if shorthand in LANG_ABBREV_DIC.keys():
            return "<a href='/languages/%s'>%s</a>" % (LANG_ABBREV_DIC[shorthand]["ID"], LANG_ABBREV_DIC[shorthand]["name"])
        elif shorthand in sampled_languages.keys():
            return "<a href='/languages/%s'>%s</a>" % (shorthand, sampled_languages[shorthand])
        elif shorthand in language_names.keys():
            return language_names[shorthand]
        elif shorthand in LANG_CODE_DIC.keys():
            return LANG_CODE_DIC[shorthand]["name"]
        else:
            language = DBSession.query(Language).filter(Language.id == shorthand)[0]
            return "<a href='/languages/%s'>%s</a>" % (shorthand, language.name)            
            
    def cogset_lk(cogset_id, text=""):
        if cogset_id == "":
            return ""
        cogset = DBSession.query(Cognateset).filter(Cognateset.id == cogset_id)[0]
        if text == "":
            return "<i><a href='/cognateset/%s'>%s</a></i>" % (cogset_id, cogset)
        else:
            return "<i><a href='/cognateset/%s'>%s</a></i>" % (cogset_id, text)

    def src_lk(source_str):
        bib_key = source_str.split("[")[0]
        source = DBSession.query(Source).filter(Source.id == bib_key)[0]
        if len(source_str.split("[")) > 1:
            pages = source_str.split("[")[1].split("]")[0]
            return "<a href='/sources/%s'>%s</a>: %s" % (bib_key, source, pages.replace("--", "–"))
        else:
            return "<a href='/sources/%s'>%s</a>" % (bib_key, source)

    def morph_lk(morph_id, form=""):
        if morph_id == "":
            return ""
        morph_list = DBSession.query(Morpheme).filter(Morpheme.id == morph_id)
        if len(list(morph_list)) == 0:
            #print(f"Morpheme {morph_id} not found in database!")
            return '' #f"MISSING MORPHEME {morph_id}"
        else:
            morph = morph_list[0]
        if html:
            if form == "": form = morph.name#.split("/")[0]
            return "<i><a href='/morpheme/%s'>%s</a></i>" % (morph_id, form)
        else:
            if form == "":
                allomorphs = morph.name.split("/")
                form = []
                for allomorph in allomorphs:
                    form.append("\\obj{%s}" % allomorph)
                form = "/".join(form)
            else:
                form = "\\obj{%s}" % form
            return form
        
    def render_ex(ex_id):
        nonlocal ex_cnt
        ex_cnt += 1
        example = DBSession.query(Sentence).filter(Sentence.id == ex_id)[0]
        return """
            <blockquote style='margin-top: 5px; margin-bottom: 5px'>
            (<a href='/example/%s'>%s</a>) %s (%s)
                %s
            </blockquote>""" % (example.id,ex_cnt,
                            lang_lk(example.language.id),
                            src_lk("%s[%s]" % (example.references[0].source.id, example.references[0].description)),
                            rendered_sentence(example)
                        )
    
    result = '' #eval(f'f"""{non_f_str}"""')
    return result.replace("-</a></i>£", "-</a></i>").replace("-}£", "-}").replace("£", " ").replace("\n\n","PARAGRAPHBREAK").replace("\n"," ").replace("PARAGRAPHBREAK","\n\n")
    
def html_table(lol, caption):
    output = ""
    output += '<table class="table paradigm-table"> <caption>%s</caption>' % caption
    for sublist in lol:
        output += '  <tr><td class="td paradigm-td">'
        output += '    </td><td class="td paradigm-td">'.join(sublist)
        output += '  </td></tr>'
    output += '</table>'
    return output

def render_latex_code(input):
    # if "morph:" not in input:
    #     return pynterlinear.get_expex_code(input)
    # else:
        return generate_markup(input, html=False)
    
def latex_table(lol):
    output = """\\begin{tabular}{@{}"""
    col_cnt = len(lol[1])
    for i in range(0,col_cnt):
        output += "l"
    output += "@{}}\n\\mytoprule"
    for i, sublist in enumerate(lol):
        sublist = [render_latex_code(x) for x in sublist]
        output += "\n"
        output += " & ".join(sublist)
        output += "\\\\"
        if i == 0: output += "\n\\mymidrule"
    output += """\n\\mybottomrule
\\end{tabular}"""
    return output

def keyify(list, hash):
    return re.sub(r"(\d):", r"\1", ":".join(get_args(list, hash))).strip(":")

#This takes a list of keys (in this case, of parameter names) and a hash (in this case, of an entry), and returns a list of values from the hash. Used to combine different parameters
def get_args(list, hash): 
    output = []
    for item in list:
        output.append(hash[item])
    return(output)

def person_sort(s):
    sortation = {
        "1": 1,
        "2": 2,
        "3": 5,
        "1+2": 3,
        "1+3": 4,
        "": 0
    }
    return sortation[re.sub("[A,S,P]", "", s)]
    
def build_table(table, label):
    output = []
    x_values = []
    y_values = []
    output.append([])
    for y_key, y in table.items():
        if y_key not in y_values:
            y_values.append(y_key)
        for x_key, x in y.items():
            if x_key not in x_values:
                x_values.append(x_key)
    sort_me = True
    for x_value in x_values:
        if re.sub("[A,S,P]", "", x_value) not in ["1", "2", "3", "1+2", "1+3"]: sort_me = False
    if sort_me:
        x_values = sorted(x_values, key=person_sort)
    row_count = 0
    output[0].append(label)
    for x in x_values:
        output[row_count].append(x)
    
    for x_key in table.keys():
        output.append([])
        row_count += 1
        output[row_count].append(x_key)
        for i in x_values:
            output[row_count].append("")
        for y_key, y in table[x_key].items():
            col_count = 0
            while col_count < len(x_values):
                if output[0][col_count+1] == y_key:
                    if type(y) is list:
                        # print(y)
                        y = ", ".join(y)
                    output[row_count][col_count+1] = y
                col_count += 1
    if label == "": del output[0]
    return output


def intransitive_construction_paradigm(construction, html=True):
    # print("constructing intransitive paradigm for %s" % construction)
    table = {}
    entries = []
    for entry in FUNCTION_PARADIGMS:
        new_entry = entry
        # if re.match("\d(\+\d)?\w", entry["Function"]) and "." not in entry["Function"]:
        if re.match("\d(\+\d)?S", entry["Function"]) and "." not in entry["Function"]:
            new_entry["S"] = entry["Function"].replace("S","")
        else:
            continue
        entries.append(new_entry)
        
    for entry in entries:
        if entry["S"] not in table.keys() and entry["Construction"] == construction:
            table[entry["S"]] = {"":[]}
    
    table = dict(sorted(table.items(), key=lambda kv: person_sort(kv[0])))
    table = OrderedDict(table.items())
    for entry in entries:
        if entry["Construction"] != construction: continue
        string = ""
        for morpheme in entry["Morpheme"]:
            string += "morph:" + morpheme + "£"
        table[entry["S"]][""].append(string)
            
    table = dict((k, v) for k, v in table.items() if "morph:" in str(v))
    
    if "morph:" not in str(table):
        return ""
    if html:
        return html_table(build_table(table, " "), "Intransitive person marking")
    else:
        return build_table(table, " ")

def comparative_function_paradigm(constructions, label, values):
    entries = []
    for entry in FUNCTION_PARADIGMS:
        for value in values:
            if value == entry["Function"]:
                entries.append(entry)
    x_dim = ["Function"]
    y_dim = ["Construction"]
        
    table = {}
    #Iterate through all entries and generate the necessary rows in the appropriate tables
    for entry in entries:
        if entry["Construction"] not in constructions:
            continue
        y_key = "cons:"+keyify(y_dim, entry)
        if y_key not in table.keys():
            table[y_key] = {}
            
    table = OrderedDict(table.items())
    #Iterate through all entries and put the form into the appropriate place
    for entry in entries:
        if entry["Construction"] not in constructions:
            continue
        y_key = "cons:"+keyify(y_dim, entry)
        my_y = table[y_key]
        good = True
        x_key = keyify(x_dim, entry)
        if x_key not in my_y.keys(): my_y[x_key] = []
        # for col, val in filtered_parameters.items():
            # if entry[col] != val:
                # good = False
        if good:
            #Find the appropriate column
            string = ""
            for morpheme in entry["Morpheme"]:
                string += "morph:" + morpheme + "£"
            my_y[x_key].append(string)
    return html_table(build_table(table, " "), label)
     
def transitive_construction_paradigm(construction, html=True):
    x_dim = ["P"]
    y_dim = ["A"]
    
    filtered_parameters = {
        "Construction": construction
    }
    
    entries = []
    for entry in FUNCTION_PARADIGMS:
        new_entry = entry
        if re.match("\d(\+\d)?P", entry["Function"]):
            new_entry["P"] = entry["Function"]#.replace("P","")
            new_entry["S"] = ""
            new_entry["A"] = ""
        elif re.match("\d(\+\d)?A", entry["Function"]):
            new_entry["P"] = ""
            new_entry["S"] = ""
            new_entry["A"] = entry["Function"]#.replace("A","")
        elif ">" in entry["Function"]:
            new_entry["P"] = entry["Function"].split(">")[1]+"P"
            new_entry["A"] = entry["Function"].split(">")[0]+"A"
            new_entry["S"] = ""
        else:
            continue
        entries.append(new_entry)
        
    table = {}
    #Iterate through all entries and generate the necessary rows in the appropriate tables
    for entry in entries:
        if entry["Construction"] != construction: continue
        y_key = keyify(y_dim, entry)
        if y_key not in table.keys():
            table[y_key] = {}
            
    table = dict(sorted(table.items(), key=lambda kv: person_sort(kv[0])))
    table = OrderedDict(table.items())
    #Iterate through all entries and put the form into the appropriate place
    for entry in entries:
        if entry["Construction"] != construction: continue
        y_key = keyify(y_dim, entry)
        my_y = table[y_key]
        good = True
        x_key = keyify(x_dim, entry)
        if x_key not in my_y.keys(): my_y[x_key] = []
        for col, val in filtered_parameters.items():
            if entry[col] != val:
                good = False
        if good:
            #Find the appropriate column
            string = ""
            for morpheme in entry["Morpheme"]:
                string += "morph:" + morpheme + "£"
            my_y[x_key].append(string)
    if html:
        return html_table(build_table(table, " "), "Transitive person marking")
    else:
        return build_table(table, " ")
    
def phylogeny_detail_html(request=None, context=None, **kw):
    return {
        'ms': CombinationMultiSelect,
}

def parameter_detail_html(request=None, context=None, **kw):
    return {
        'ms': CombinationMultiSelect,
}

def default_tree(request=None, ctx=None, **kw):
    tree = DBSession.query(Phylogeny).filter(Phylogeny.id == "gildea_norm")[0]
    return tree

def t_adding_pct():
    result = {}
    for l in DBSession.query(Language):
        if l.id == "pc": continue
        result[l.id] = "%s/%s" % (
                                    l.jsondata["t_values"]["y"],
                                    (l.jsondata["t_values"]["y"]+l.jsondata["t_values"]["n"]+l.jsondata["t_values"]["?"])
                                )
    return result
    
def get_clade_as_json(clade):
    json_clade = {}
    if clade.name is None:
        json_clade["name"] = "Clade"
    else:
        json_clade["name"] = clade.name
    if not clade.is_terminal():
        json_clade["children"] = []
        for node in clade:
            json_clade["children"].append(get_clade_as_json(node))
    return json_clade

def get_tree(request, values, tree_name):
    my_tree = Phylo.read(io.StringIO(DBSession.query(Phylogeny).filter(Phylogeny.id == "matter")[0].newick), "newick")
    for node in my_tree.find_clades():
        if node.name == None:
            continue
        if node.is_terminal():
            node.name = node.name.replace("?","")
            new_name = "lg:" + node.name
        else:
            new_name = node.name
        if node.name in values.keys():
            if type(values[node.name]) is str:
                new_name += ": " + values[node.name]
            elif type(values[node.name]) is list:
                append_string = []
                for value in values[node.name]:
                    append_string.append(h.link(request, value))
                new_name += ": " + "; ".join(append_string)
            else:
                new_name += ": " + h.link(request, values[node.name])
        node.name = new_name
        node.name = generate_markup(node.name)
    return get_clade_as_json(my_tree.clade)
    
def get_morpheme_tree(clauses, scenario, tree_name, reconstructed=False):
    set_1 = {}
    for i in clauses:
        set_1[i] = {}
    for entry in FUNCTION_PARADIGMS:
        if entry["Construction"] in set_1:
            if entry["Function"] not in set_1[entry["Construction"]].keys():
                set_1[entry["Construction"]][entry["Function"]] = [entry["Morpheme"]]
            else:
                set_1[entry["Construction"]][entry["Function"]].append(entry["Morpheme"])
    lang_clauses = {}
    for clause in set_1:
        cons = DBSession.query(Construction).filter(Construction.id == clause)[0]
        lang_clauses[cons.language.id] = set_1[clause]
    lang_clauses["kax"] = {
        "3>1+2": [["k-"]],
        "1>2": [["k-"]],
        "2>1": [["k-"]],
        "1>3": [["w-"]],
        "1+2>3": [["k(ɨt)-"]],
        "3>1": [["j-"],["Ø-"]],
        "3>2": [["o(w)-"]]
    }
    lang_clauses["bak"] = {
        "3>1+2": [["k-"]],
        "1>2": [["ə-"]],
        "2>1": [["j-"]],
        "1>3": [["s-"]],
        "1+2>3": [["kɨd-"]],
        "3>1": [["ɨ-"],["j-"]],
        "3>2": [["ə-"]]
    }
    lang_clauses["yuk"] = {
        "3>1+2": [["ɨp", "n-"]],
        "1>2": [["aw", "oj-"]],
        "2>1": [["am", "j-"]],
        "1>3": [["aw", "Ø-"]],
        "1+2>3": [["ɨp", "Ø-"]],
        "3>1": [["aw", "j-"]],
        "3>2": [["am", "oj-"]]
    }
    lang_clauses["aku"] = {
        "3>1+2": [["k-"]],
        "1>2": [["k-"]],
        "2>1": [["k-"]],
        "1>3": [["i-"],["Ø-"]],
        "1+2>3": [["kɨt-"]],
        "3>1": [["jː-"],["Øː-"]],
        "3>2": [["ə-"]]
    }
    lang_clauses["cum"] = {
        "1>2": [["kaj-"], ["kən-"], ["k-"]],
        "2>1": [["kaj-"], ["k-"]],
        "1>3": [["w-"], ["i-"]],
    }
    lang_clauses["tam"] = {
        "3>1+2": ["?"],
        "1>2": ["?"],
        "2>1": ["?"],
        "1>3": [["t-"]],
        "1+2>3": [["kɨt͡ʃ-"]]
    }
    lang_clauses["car"] = {
        "3>1+2": [["k-"]],
        "1>2": [["k-"]],
        "2>1": [["k-"]],
        "1>3": [["i-"]],
        "1+2>3": [["kɨt-"]],
        "3>1": [["j-"], ["ji-"], ["voice"]],
        "3>2": [["əj-"]]
    }
    lang_clauses["pem"] = {
        "1>3": "s-",
        "1>2": ["?"],
        "2>1": ["?"],
    }
    my_tree = Phylo.read(io.StringIO(DBSession.query(Phylogeny).filter(Phylogeny.id == "matter")[0].newick), "newick")
    for node in my_tree.find_clades():
        if node.name == None:
            continue
        if node.is_terminal():
            node.name = node.name.replace("?","")
            new_name = "lg:" + node.name
        else:
            new_name = node.name
        if node.name in lang_clauses.keys():
            if scenario in lang_clauses[node.name].keys():
                all_morphs = []
                for morpheme_combo in lang_clauses[node.name][scenario]:
                    this_morph = []
                    for morpheme in morpheme_combo:
                        if DBSession.query(Morpheme).filter(Morpheme.id == morpheme).count() >= 1:
                            if not reconstructed or DBSession.query(Morpheme).filter(Morpheme.id == morpheme)[0].counterparts[0].cognateset.id == "NA":
                                this_morph.append("morph:" + morpheme)#data["Morpheme"][morpheme].name + " "
                            else:
                                # print()
                                for counterpart in DBSession.query(Morpheme).filter(Morpheme.id == morpheme)[0].counterparts:
                                    this_morph.append("cogset:" + counterpart.cognateset.id)
                        else:
                            this_morph.append("obj:" + morpheme)
                    all_morphs.append("£".join(this_morph))
            else:
                all_morphs = ["-"]
        else:
            all_morphs = ["-"]
        node.name = new_name + " " + " OR ".join(all_morphs)
        node.name = generate_markup(node.name)
    return get_clade_as_json(my_tree.clade)