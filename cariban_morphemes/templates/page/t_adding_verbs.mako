<% import json %>
<div id="my_tree"></div>

<% t_values = u.t_adding_pct() %>
<% my_tree = u.get_tree(
	request,
	t_values,
	"my_tree")
%>
${ my_tree }
<script>
	$(function() {
	    $('#my_tree').tree({
	        data: [
	    ${ json.dumps(my_tree) | n },
	],
			autoEscape: false,
			autoOpen: true
	    });
	});
</script>