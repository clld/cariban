<% import markdown, json %>
<p>
${h.Markup(u.generate_markup("""
src:meira2010origin[489] suggest this new reconstruction of lg:pc person marking:
"""))}
${h.Markup(u.generate_markup(u.transitive_construction_paradigm("pc_main")))}
<br>
${h.Markup(u.generate_markup(markdown.markdown("""
For 3>1 and 3>2, the proclitics cogset:1p and cogset:2p are combined with the linker cogset:link.
All scenarios with a third person P now are combinations of some other person marker and the third person P marker cogset:3i.
<br>
The 1/2P proclitics are speculated to have originated (at a pre-lg:pc stage) from free pronouns cogset:1pro and cogset:2pro.
They also suggest that cogset:3n was added at a later stage (src:meira2010origin[497]).
A possible source for this addition is a third person pronoun (src:gildea1994inversion[202]), which src:meira2002first[268] reconstructs as rc:(i)nɤrɤ.
If one applies these speculations in order to get to pre-lg:pc person marking, one would arrive at the following paradigm:

&nbsp;	| | | | |
---|---|---|---|---|
&nbsp;	|	1P						|	2P						|	1+2P	|	3P	
1A		|		-					|rc:morph:pc_12				|	-		| rc:morph:pc_1a£morph:pc_3i	
2A		|	rc:morph:pc_12				|	-						|	-		| rc:morph:pc_2a£morph:pc_3i
1+2A	|		-					|	-						|			| rc:morph:pc_12a£morph:pc_3i	
3A		|rc:morph:pc_1pro morph:pc_link|rc:morph:pc_2pro morph:pc_link|rc:morph:pc_12|rc:morph:pc_3pro morph:pc_3i

This of course immediately raises the question of whether the other elements that were added to cogset:3i also had pronominal sources.
Considering that cogset:1a does not show a huge distribution, and that most languages show a reflex of cogset:1sa in 1>3 function, it does not seem unlikely that lg:pc had rc:morph:pc_1sa£morph:pc_3i for 1>3.
Considering this form, and that of the second person marker (cogset:1sa and cogset:2a), the similarity to the suggested pronominal sources of cogset:1p and cogset:2p (cogset:1pro and cogset:2pro) becomes clear immediately.
Similarly to cogset:1pro and cogset:2pro combining with cogset:link to yield lg:pc morph:pc_1p£morph:pc_link and morph:pc_2p£morph:pc_link, cogset:1pro and cogset:2pro could have easily combined with cogset:3i to yield morph:pc_1sa£morph:pc_3i and morph:pc_2a£morph:pc_3i.

&nbsp;	| | | | |
---|---|---|---|---|
&nbsp;	|	1P						|	2P						|	1+2P	|	3P	
1A		|		-					|rc:morph:pc_12				|	-		| rc:morph:pc_1pro morph:pc_3i	
2A		|	rc:morph:pc_12				|	-						|	-		| rc:morph:pc_2pro morph:pc_3i
1+2A	|		-					|	-						|			| rc:morph:pc_12a£morph:pc_3i	
3A		|rc:morph:pc_1pro morph:pc_link|rc:morph:pc_2pro morph:pc_link|rc:morph:pc_12|rc:morph:pc_3pro morph:pc_3i

This leaves the last element combining with cogset:3i: the 1+2 marker cogset:12a.
While there are many 1+2 pronouns that suggest a reconstructible component rc:kɨ- (src:meira2002first[261]), a form rc:kɨt cannot be reconstructed for 1+2 pronouns, and a purely pronominal origin seems unlikely.
However, many languages do not show a reflex of rc:kɨ- in their 1+2 markers, instead only having reflexes of rc:t-.
src:gildea1998[81--82] explains these languages as having lost rc:kɨ-.
An alternative hypothesis would be that they never added rc:kɨ-, preserving an old 1+2 marker rc:t-.
All reflexes of rc:kɨt- would then be innovations, combining the same element rc:kɨ, which appears in many pronoun forms, with rc:t-.
This prospect is especially interesting considering that reflexes of a form rc:t- appear in 1>3 function only in lg:kalina, lg:ingariko, and lg:panare.
lg:trio and lg:ingariko use obj:t- as a 1S marker.
lg:hixka, lg:waiwai, lg:waimiri, and lg:apalai do not show reflexes of rc:kɨ in their 1+2 marking, only having rc:t-.
However, the rest of the family shows a massive preference for rc:kɨt- as a 1+2 marker.
In fact, rc:t- as 1+2 seems to be restricted to a geographically contiguous area in the Northern Amazon.
Also, rc:t- shows no strong genealogical influence -- both lg:waimiri and lg:apalai are not yet placed in a branch.
Interestingly, lg:wayana also shows forms without rc:kɨ.

Leaving aside the issue of 1+2 forms, which are different from first and second person forms in their use of rc:k- in 3>1+2 scenarios anyway, what is different about this reconstructed system?
Crucially, in 1/2>3, 3>1/2, and 3>3 scenarios, it is only the P argument that is marked on the verb, while the A is expressed as a free pronoun preceding the verb.
This in turn is of course reminiscent of the reanalyses of subordinate nominalized clauses becoming main clauses throughout the history of Cariban, e.g. the cons:pan_new.
Could lg:pc main clause syntax have come from nominalizations?
Potentially; a large issue are the 1>2, 2>1, and 3>1+2 scenarios, for which the reconstruction cogset:12 does seem to make the most sense.
And even though there are many languages which have something other than a reflex of cogset:12, none of them show any form which could be seen as a reflex of a first or second person possessor.
The situation is different in 3>1+2 scenarios, though, where rc:k- is also 1+2POSS.
In addition, 2>1 and 1>2 scenarios have undergone quite a bit of restructuring (src:heath1998pragmatic), so it is not entirely unthinkable that a potential original marking (different from rc:k-) has disappeared altogether.
""", extensions=["tables"])))}
${h.text2html(u.generate_markup(
                u.comparative_function_paradigm(
                    ["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_pstpfv", "ing_old"],
                    "1+3 scenarios",
                    ["1>2", "2>1", "3>1+2"])))}
</p>

${h.Markup(u.generate_markup("""
Interestingly, two languages not in my sample, lg:bakairi and lg:yukpa show reflexes of cogset:1p and cogset:2p in 2>1 and 1>2 constructions -- exactly what one would have expected based on the spread of cogset:12 from 3>1+2 to these scenarios, and the potential strict P-marking (possessor-marking) nature of pre-lg:pc verbs.
Even more interestingly, these two languages are at the periphery of the family, in Southern Brazil and Northern Colombia, respectively.
"""))}

<h6>1>2 marking throughout the family:</h6>
<div id="tree1" style="width: 500px; float:left; margin:10px"></div>

<h6>2>1 marking throughout the family:</h6>
<div id="tree2" style="width: 500px; float:left; margin:10px"></div>

<h6>1>3 marking throughout the family:</h6>
<div id="tree3" style="width: 500px; float:left; margin:10px"></div>

<h6>3>1 marking throughout the family:</h6>
<div id="tree4" style="width: 500px; float:left; margin:10px"></div>

<h6>3>2 marking throughout the family:</h6>
<div id="tree5" style="width: 500px; float:left; margin:10px"></div>

<% tree1 = u.get_morpheme_tree(
	["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_pstpfv", "ing_old"],
	"1>2",
	"gildea_norm",
	False,
)
tree2 = u.get_morpheme_tree(
	["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_pstpfv", "ing_old"],
	"2>1",
	"gildea_norm",
	False,
)
tree3 = u.get_morpheme_tree(
	["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_pstpfv", "ing_old"],
	"1>3",
	"gildea_norm",
	False,
)
tree4 = u.get_morpheme_tree(
	["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_pstpfv", "ing_old"],
	"3>1",
	"gildea_norm",
	False,
)
tree5 = u.get_morpheme_tree(
	["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_pstpfv", "ing_old"],
	"3>2",
	"gildea_norm",
	False,
)
 %>

<script>
	
	$(function() {
	    $('#tree1').tree({
	        data: [
	    ${ json.dumps(tree1) | n },
	],
			autoEscape: false,
			autoOpen: true
	    });
	    $('#tree2').tree({
	        data: [
	    ${ json.dumps(tree2) | n },
	],
			autoEscape: false,
			autoOpen: true
	    });
	    $('#tree3').tree({
	        data: [
	    ${ json.dumps(tree3) | n },
	],
			autoEscape: false,
			autoOpen: true
	    });
		
	    $('#tree4').tree({
	        data: [
	    ${ json.dumps(tree4) | n },
	],
			autoEscape: false,
			autoOpen: true
	    });
		
	    $('#tree5').tree({
	        data: [
	    ${ json.dumps(tree5) | n },
	],
			autoEscape: false,
			autoOpen: true
	    });
		
	});
</script>