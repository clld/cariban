<% import json %>
<%block name="head">
    <script src="${request.static_url('cariban_morphemes:static/scripts/tree.jquery.js')}"></script>
    <link rel="stylesheet" href="${request.static_url('cariban_morphemes:static/css/jqtree.style.css')}">
</%block>

<div>
${h.text2html(u.generate_markup("""This is a demonstration for plotting reflexes of different cognate sets with the same use on family trees.
	For example, here I show the origin of all morphemes in the function 1>2, plotted on the tree by src:gildea2012classification:"""))}
</div>
<div id="tree1"></div>
<% tree1 = u.get_morpheme_tree(
	["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_pstpfv", "ing_old"],
	"1>2",
	"gildea_norm",
	True,
) %>
</div>
${h.text2html(u.generate_markup("""As another example, here is the 1>3 marker in the rather small tree by src:mattei2002busca:"""))}
<div id="tree2"></div>
<% tree2 = u.get_morpheme_tree(
	["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_pstpfv", "ing_old"],
	"1>3",
	"mattei_norm",
	True,
) %>
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
	});
</script>