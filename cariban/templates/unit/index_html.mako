<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "units" %>

<%block name="head">
    <script>
	var target = location.hash.substr(1)
	$(document).ready(function(){
		$('.nav-tabs a[href="#' + target + '"]').tab('show');
	});
    </script>
</%block>

<h2>${_('Morphemes')}</h2>

<div class="tabbable">
    <ul class="nav nav-tabs" id="all_morphemes" role="tablist">
        <li class="active"><a href="#morphemes" data-toggle="tab">Grammatical morphemes</a></li>
        <li><a href="#tadding" data-toggle="tab">t-adding verbs</a></li>
		<li><a href="#swadesh" data-toggle="tab">Swadesh list</a></li>
    </ul>
    <div class="tab-content" style="overflow: visible;">
        <div id="morphemes" class="tab-pane active">
			${request.get_datatable('units', u.cariban_models.Morpheme, morpheme_type="grammatical").render()}
        </div>
        <div id="tadding" class="tab-pane">
			${request.get_datatable('units', u.cariban_models.Morpheme, morpheme_type="t_adding").render()}
        </div>
        <div id="swadesh" class="tab-pane">
			${request.get_datatable('units', u.cariban_models.Morpheme, morpheme_type="lexical").render()}
        </div>
    </div>	
</div>