<%inherit file="../home_comp.mako"/>
<%namespace name="util" file="../util.mako"/>
<%namespace name="cmutil" file="../cmutil.mako"/>
## <%def name="sidebar()">
##     <div class="well">
##         <h3>Sidebar</h3>
##         <p>
##             Content
##         </p>
##     </div>
## </%def>
<h2>Verbal morphology with 1+3 (“first person exclusive”)</h2>

<p>
${h.text2html(u.generate_markup("""In most Cariban languages, the combination of first and third person (1+3, 1EXCL) is expressed by means of a free pronoun, usually accompanied by third person verbal morphology. However, most descriptions only mention or exemplify the scenarios 1+3S, and 1+3>3, some also 3>1+3. Less is said about 2>1+3 and 1+3>2.
Below is an overview of how these scenarios are expressed in the relevant unmarked main clauses for eleven languages.

Not included are lg:macushi and lg:kuikuro, as they have completely innovated main clause syntax, and lg:ingariko, as there are no examples of 1+3 marking."""))}
${h.text2html(u.generate_markup(
                u.comparative_function_paradigm(
                    ["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_pstpfv", "ing_old"],
                    "1+3 scenarios",
                    ["1+3S", "1+3>3", "3>1+3", "2>1+3", "1+3>2"])))}
${h.text2html(u.generate_markup("""
1+3S and 1+3>3 are straightforwardly reconstructible as a combination of the 1+3 pronoun cogset:13pro and third person marking.
In most languages, 3>1+3 is expressed with only a reflex of cogset:1pro, without any marking on the verb.
However, the two languages preserving the linking morpheme cogset:link (lg:panare and lg:hixka) indicate that this scenario was most likely expressed with cogset:13pro cogset:link.
lg:waiwai is exceptional in that it also has a reflex of cogset:3n in this scenario: ex:wai-57
However, this can be seen as a more general property of lg:waiwai, as cogset:3n also appears with object nominals (obj:amorɨ 'his hand' is followed by obj:n-): ex:wai-58

Moving on to combinations of second person and 1+3, the data is surprisingly sparse.
In 2>1+3 scenarios, lg:trio, lg:ikpeng, lg:kalina, lg:panare, and lg:waiwai show a reflex of cogset:13pro cogset:2a.
In 1+3>2 scenarios, lg:hixka, lg:ikpeng, lg:waiwai, and lg:waimiri show a reflex of cogset:13pro cogset:2p.
These cover enough subbranches to reconstruct them for lg:pc.

As for the other ways of expressing these scenarios, lg:maqui seems to have reanalyzed 1+3 as a “true” first person, employing the 2>1 and 1>2 markers morph:mak_12 and morph:mak_1on2, respectively.
lg:panare has two ways of expressing 1+3>2; both look like innovations.
One is with a combination of second person pronoun and linking morpheme: cogset:2pro cogset:link (with a postverbal cogset:13pro), the other stems from cogset:2pro cogset:13pro cogset:3n£cogset:3i.

"""))}
</p>
