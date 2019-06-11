# coding: utf8
from __future__ import unicode_literals
import re

from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from markupsafe import Markup

import clld
from clld import interfaces
from clld import RESOURCES
from clld.web.util.htmllib import HTML, literal
from clld.web.util.downloadwidget import DownloadWidget
from clld.db.meta import DBSession
from clld.db.models import common as models
from clld.web.adapters import get_adapter, get_adapters
from clld.lib.coins import ContextObject
from clld.lib import bibtex
from clld.lib import rdf
from cariban_morphemes import models as cariban_models

from collections import OrderedDict

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

def html_table(lol, caption):
    output = ""
    output += '<table class="table paradigm-table"> <caption>%s</caption>' % caption
    for sublist in lol:
        output += '  <tr><td class="td paradigm-td">'
        output += '    </td><td class="td paradigm-td">'.join(sublist)
        output += '  </td></tr>'
    output += '</table>'
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
    
def build_table(table, label, caption):
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
                        y = "; ".join(y)
                    output[row_count][col_count+1] = y
                col_count += 1
    if label == "": del output[0]
    return html_table(output, caption)

def intransitive_construction_paradigm(construction, functions):
    table = {}
    entries = []
    for entry in functions:
        new_entry = entry
        if re.match("\d(\+\d)?S", entry["Function"]):
            new_entry["S"] = entry["Function"]#.replace("S","")
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
            string += "morph:" + morpheme + " "
        table[entry["S"]][""].append(string)
            
    table = dict((k, v) for k, v in table.items() if "morph:" in str(v))
    
    if "morph:" not in str(table):
        return ""
    return build_table(table, "", "Intransitive person marking")
        
def transitive_construction_paradigm(construction, functions):
    x_dim = ["P"]
    y_dim = ["A"]
    
    filtered_parameters = {
        "Construction": construction
    }
    
    entries = []
    for entry in functions:
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
                string += "morph:" + morpheme + " "
            my_y[x_key].append(string)
    return build_table(table, " ", "Transitive person marking")