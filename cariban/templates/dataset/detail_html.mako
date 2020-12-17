<%inherit file="../home_comp.mako"/>
<%namespace name="util" file="../util.mako"/>
<%doc>
<%def name="sidebar()">
    <div class="well">
        <h3>Sidebar</h3>
        <p>
            Content
        </p>
    </div>
</%def>
</%doc>
<%def name="sidebar()">
    ${util.cite()}
</%def>

<div>
<h2>Comparative Cariban Database</h2>

##<p class="lead">
##    Abstract.
##</p>
<p>
This database contains information on verbal morphology and lexical data of <a href="/languages">22 Cariban languages</a>.
It is intended as a companion piece to my dissertation.

For each language, there is a list of:

<ol>
<li> <a href="/morphemes">grammatical morphemes</a>
<li> <a href="/constructions">verbal constructions</a>, which contain person marking paradigms
<li> <a href="/morphemes#tadding">t-adding verbs</a>, a group of transitive verbs with an idiosyncratic 3P marker rc:t-
<li> <a href="/morphemes#swadesh">lexical morphemes</a>, compiled for my <a href="https://gitlab.com/florianmatter/cariban_phylo/">phylogenetic classification</a>
<li> <a href="/examples">example sentences</a>
<li> relevant <a href="/sources">literature</a>
</ol>

All language-specific morphemes are connected via cognate sets, separated into <a href="/cognatesets">grammatical morphemes</a>, <a href="/cognatesets#tadding">t-adding verbs</a>, and <a href="/cognatesets#swadesh">lexical data</a>.
Uses of person markers are, if possible, illustrated with examples; see for example <a href="/morpheme/ikp_12a">this Ikpeng morpheme</a>.

Not all languages are equally extensively featured, due to different descriptive coverage. Of the extant Cariban languages, only <a href="https://glottolog.org/resource/languoid/id/japr1238">Japrería</a> is not featured at all.
<a href="/languages/kax">Werikyana</a> data was partially contributed by <a href="https://linguistics.uoregon.edu/profile/spike">Spike Gildea</a>.
</p>
</div>