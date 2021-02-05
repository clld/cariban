import io
import re
import itertools
from collections import OrderedDict

from sqlalchemy import or_
from markupsafe import Markup
from Bio import Phylo

from clld.db.meta import DBSession
from clld.db.models import common as models
from clld.db.models import Language, Source, Sentence
from clld.web.util import helpers as h
from clld.web.util.htmllib import HTML, literal
from clld.web.util.multiselect import CombinationMultiSelect
from clld_phylogeny_plugin.models import Phylogeny

from cariban.models import Morpheme, Construction, Cognateset
from cariban import models as cariban_models
assert cariban_models


separators = ["-", "=", "<", ">"]
PERSON_SPECS = ["1", "2", "1+2", "1+3", "3"]


def text2html(*args, **kw):
    res = str(h.text2html(*args, **kw))
    res = res.replace(' class="table ', ' class="table table-nonfluid ')
    return res


def function_paradigms():
    return models.Dataset.first().jsondata['function_paradigms']


def extract_allomorphs(full_string):
    def iterate(string):
        for repl in [r"\1", ""]:  # Keep content in braces of drop it.
            variant = re.sub(r"\((.*?)\)", repl, string, 1)
            if "(" in variant:
                for i in iterate(variant):
                    yield i
            else:
                yield variant

    found_allomorphs = list(itertools.chain(*[iterate(s) for s in full_string.split("/")]))
    # Deduplicate while keeping the order:
    seen = set()
    return [x for x in found_allomorphs if not (x in seen or seen.add(x))]


def merge_allomorphs(form):
    allomorphs = form.split("; ")
    prefix = allomorphs[0][-1] in separators
    suffix = False if prefix else allomorphs[0][0] in separators
    allomorphs.sort(key=len)
    # We take the shortest allomorph as the base
    new_allomorphs = [allomorphs[0]]
    # Then we iterate the longer allomorphs
    for allomorph in allomorphs[1:]:
        # If there is an affricate, let's just add it straight away, we don't want to split these up
        if "͡" in allomorph:
            new_allomorphs.append(allomorph)
            continue
        found_hit = False
        # We iterate the allomorphs we already added to the new form
        for i, existing_allomorph in enumerate(new_allomorphs):
            if not found_hit:
                right_border = len(allomorph) - (2 if prefix else 1)
                left_border = 1 if suffix else 0
                for right_edge in range(right_border, -1, -1):
                    for left_edge in range(left_border, right_edge + 1):
                        if left_edge == right_edge:
                            allo_slice = allomorph[left_edge]
                        else:
                            allo_slice = allomorph[left_edge:right_edge + 1]
                        if suffix:
                            preserve = existing_allomorph[1::]
                        elif prefix:
                            preserve = existing_allomorph[0:-1]
                        else:
                            preserve = existing_allomorph
                        comp = preserve.replace("(","").replace(")","")
                        if allo_slice == comp:
                            new_allomorph = "({}){}({})".format(
                                allomorph[:left_edge], preserve, allomorph[right_edge+1:])
                            new_allomorph = new_allomorph.replace("-)", ")-")
                            new_allomorph = new_allomorph.replace("()","")
                            new_allomorphs[i] = new_allomorph
                            found_hit = True
        if not found_hit:
            new_allomorphs.append(allomorph)
    for new_allomorph, other_allomorph in itertools.permutations(new_allomorphs, 2):
        if new_allomorph in extract_allomorphs(other_allomorph):
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
def rendered_sentence(sentence, abbrs=None, **kw):
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


def generate_markup(string: str, html=True):
    ex_cnt = 0

    languages = {}
    for lang in DBSession.query(Language):
        languages[lang.id] = languages[lang.jsondata["Shorthand"]] = lang

    if string is None:
        return ""

    def cons_lk(shorthand):
        c = Construction.get(shorthand)
        return "<a href='/construction/{}'>{} {} clause</a>".format(c.id, c.language.name, c.name)

    def lang_lk(shorthand):
        lang = languages[shorthand]
        return "<a href='/languages/%s'>%s</a>" % (lang.id, lang.name)

    def cogset_lk(cogset_id, text=""):
        if cogset_id == "":
            return ""
        cogset = Cognateset.get(cogset_id)
        return "<i><a href='/cognateset/%s'>%s</a></i>" % (cogset_id, text or cogset)

    def src_lk(source_str, parens=False):
        bib_key = source_str.split("[")[0]
        source = DBSession.query(Source).filter(Source.id == bib_key)[0]
        if len(source_str.split("[")) > 1:
            pages = source_str.split("[")[1].split("]")[0]
            if not parens:
                return "<a href='/sources/%s'>%s</a>: %s" % (bib_key, source, pages.replace("--", "–"))
            else:
                return "(<a href='/sources/%s'>%s</a>: %s)" % (bib_key, source, pages.replace("--", "–"))
        else:
            if not parens:
                return "<a href='/sources/%s'>%s</a>" % (bib_key, source)
            else:
                return "(<a href='/sources/%s'>%s</a>)" % (bib_key, source)

    def morph_lk(morph_id, form=""):
        if morph_id == "":
            return ""
        morph_list = DBSession.query(Morpheme).filter(Morpheme.id == morph_id)
        if len(list(morph_list)) == 0:
            return '' #f"MISSING MORPHEME {morph_id}"
        morph = morph_list[0]
        if html:
            return "<i><a href='/morpheme/%s'>%s</a></i>" % (morph_id, form or morph.name)
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
        example = Sentence.get(ex_id)
        return """
<blockquote style='margin-top: 5px; margin-bottom: 5px'>
    (<a href='/example/%s'>%s</a>) %s (%s)
    %s
</blockquote>""" % (
            example.id,
            ex_cnt,
            lang_lk(example.language.id),
            src_lk("%s[%s]" % (example.references[0].source.id, example.references[0].description)),
            rendered_sentence(example)
        )

    for pattern, repl in [
        ("'(.*?)'", r"‘\1’"),
        ("morph:([a-z\_0-9]*)\|?([\u00BF-\u1FFF\u2C00-\uD7FF\(\)\w]*[\-\=]?)",
            lambda m: morph_lk(m.groups()[0], m.groups()[1])),
        ("lg:([a-z]*)", lambda m: lang_lk(m.groups()[0])),
        ("cons:([a-z\_0-9]*)", lambda m: cons_lk(m.groups()[0])),
        ("cogset:([a-z\_0-9]*)", lambda m: cogset_lk(m.groups()[0])),
        ("psrc:([a-z\_0-9\[\]\-]*)", lambda m: src_lk(m.groups()[0], parens=True)),
        ("src:([a-z\_0-9\[\]\-]*)", lambda m: src_lk(m.groups()[0])),
        ("ex:([a-z\_0-9\-]*)", lambda m: render_ex(m.groups()[0])),
        ("obj:([\w\-\(\)]*)", lambda m: '<i>{}</i>'.format(m.groups()[0])),
        ("rc:([\w\-\(\)]*)", lambda m: '<i>*{}</i>'.format(m.groups()[0])),
    ]:
        string = re.sub(pattern, repl, string)

    return string\
        .replace("-</a></i>£", "-</a></i>")\
        .replace("-}£", "-}")\
        .replace("£", " ")\
        .replace("\n\n","PARAGRAPHBREAK")\
        .replace("\n"," ")\
        .replace("PARAGRAPHBREAK","\n\n")


def html_table(lol, caption):
    return str(HTML.table(
        HTML.caption(caption),
        *[HTML.tr(*[HTML.td(col, class_='td paradigm-td') for col in row]) for row in lol],
        **{'class': 'table paradigm-table'},
    ))


def keyify(list, hash):
    return re.sub(r"(\d):", r"\1", ":".join([hash[item] for item in list])).strip(":")


def person_sort(s):
    return ([""] + PERSON_SPECS).index(re.sub("[A,SP]", "", s))


def build_table(table, label):
    x_values = []
    y_values = []
    for y_key, y in table.items():
        if y_key not in y_values:
            y_values.append(y_key)
        for x_key, x in y.items():
            if x_key not in x_values:
                x_values.append(x_key)

    if all(re.sub("[A,SP]", "", x_value) in PERSON_SPECS for x_value in x_values):
        x_values = sorted(x_values, key=person_sort)
    rows = [[label] + x_values]

    for x_key in table.keys():
        row = [x_key] + ["" for _ in x_values]
        for y_key, y in table[x_key].items():
            col_count = 0
            while col_count < len(x_values):
                if rows[0][col_count + 1] == y_key:
                    row[col_count + 1] = ", ".join(y) if type(y) is list else y
                col_count += 1
        rows.append(row)
    if label == "":
        del rows[0]
    return rows


def intransitive_construction_paradigm(construction, html=True):
    # print("constructing intransitive paradigm for %s" % construction)
    table = {}
    entries = []
    for entry in function_paradigms():
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
    
    table = OrderedDict(sorted(table.items(), key=lambda kv: person_sort(kv[0])))
    for entry in entries:
        if entry["Construction"] != construction: continue
        string = ""
        for morpheme in entry["Morpheme"]:
            string += "morph:" + morpheme + "£"
        table[entry["S"]][""].append(string)

    table = OrderedDict((k, v) for k, v in table.items() if "morph:" in str(v))

    if "morph:" not in str(table):
        return ""
    if html:
        return html_table(build_table(table, " "), "Intransitive person marking")
    return build_table(table, " ")


def comparative_function_paradigm(constructions, label, values):
    entries = []
    for entry in function_paradigms():
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
        x_key = keyify(x_dim, entry)
        if x_key not in my_y.keys(): my_y[x_key] = []
        #Find the appropriate column
        string = ""
        for morpheme in entry["Morpheme"]:
            string += "morph:" + morpheme + "£"
        my_y[x_key].append(string)
    return html_table(build_table(table, " "), label)


def transitive_construction_paradigm(construction, html=True):
    x_dim = ["P"]
    y_dim = ["A"]
    filtered_parameters = {"Construction": construction}

    entries = []
    for entry in function_paradigms():
        new_entry = {k: v for k, v in entry.items()}
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
            
    table = OrderedDict(sorted(table.items(), key=lambda kv: person_sort(kv[0])))
    #Iterate through all entries and put the form into the appropriate place
    for entry in entries:
        if entry["Construction"] != construction:
            continue
        y_key = keyify(y_dim, entry)
        my_y = table[y_key]
        x_key = keyify(x_dim, entry)
        if x_key not in my_y.keys():
            my_y[x_key] = []

        if all(entry[col] == val for col, val in filtered_parameters.items()):
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
    return {'ms': CombinationMultiSelect}


def parameter_detail_html(request=None, context=None, **kw):
    return {'ms': CombinationMultiSelect}


def default_tree(request=None, ctx=None, **kw):
    return DBSession.query(Phylogeny).filter(Phylogeny.id == "gildea_norm")[0]


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
    json_clade = {"name": clade.name or "Clade"}
    if not clade.is_terminal():
        json_clade["children"] = [get_clade_as_json(node) for node in clade]
    return json_clade


def get_tree(request, values, tree_name):
    my_tree = Phylo.read(io.StringIO(Phylogeny.get("matter").newick), "newick")
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
    for entry in function_paradigms():
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
    my_tree = Phylo.read(io.StringIO(Phylogeny.get("matter").newick), "newick")
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