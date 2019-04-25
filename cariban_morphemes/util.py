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