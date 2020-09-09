from xml.etree.ElementTree import fromstring
from xmljson import badgerfish as bf
import sys
import os
import csv
from cariban import util
from pycldf import Wordlist             
import re
import pyperclip
lexicon = {}
cariban_data = Wordlist.from_metadata("../cariban_data.json")
for row in cariban_data["FormTable"]:
    alt_glossings = row["Glossing"].split("; ")
    if len(alt_glossings) == 0 or alt_glossings[0] == "":
        meanings = row["Parameter_ID"]
    else:
        meanings = alt_glossings
    lexicon[row["ID"]] = {
        "forms": row["Form"],
        "meanings": meanings,
        "language": row["Language_ID"],
    }
# print(lexicon)

def search_lexicon(form, meaning, language):
    if len(lexicon) == 0:
        return("X")
    if not meaning.isupper():
        new_meaning = meaning.replace(".", " ")
    else:
        new_meaning = meaning
    for morph_id, morpheme in lexicon.items():
        if form in morpheme["forms"] and new_meaning in morpheme["meanings"] and language in morpheme["language"]:
            return(morph_id)
    return("X")
print(lexicon["kui_3i"])
print(search_lexicon("i-", "3S", "kuik1246"))
out = ""
for row in cariban_data["ExampleTable"]:
    x_out = []
    for word in zip(row["Analyzed_Word"], row["Gloss"]):
        # print(word)
        x_string = ""
        for morpheme in zip(re.split('(?<=\-|\=)', word[0]), re.split('\-|\=', word[1])):
            morph_form = morpheme[0]
            if not morpheme[1].isupper():
                morph_gloss = morpheme[1].replace(".", " ")
            else:
                morph_gloss = morpheme[1]
            result = search_lexicon(morph_form, morph_gloss, row["Language_ID"])
            if result == "X":
                x_string+="X%s" % morph_form[-1]
            else:
                x_string+=result+"-"
        x_out.append(x_string[0:-1])
    out+=" ".join(x_out)+"\n"
pyperclip.copy(out)