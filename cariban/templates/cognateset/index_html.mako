<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "cognatesets" %>
<%block name="title">${_('Cognate sets')}</%block>

<%block name="head">
    <script src="${request.static_url('cariban:static/scripts/tab_anchors.js')}"></script>
</%block>

<h2>${title()}</h2>
<!-- <div>
    ${ctx.render()}
</div> -->

<div class="tabbable">
    <ul class="nav nav-tabs" id="all_cogsets" role="tablist">
        <li class="active"><a href="#morphemes" data-toggle="tab">Grammatical morphemes</a></li>
        <li><a href="#tadding" data-toggle="tab">t-adding verbs</a></li>
		<li><a href="#swadesh" data-toggle="tab">Swadesh list</a></li>
    </ul>
    <div class="tab-content" style="overflow: visible;">
        <div id="morphemes" class="tab-pane active">
			${request.get_datatable('cognatesets', u.cariban_models.Cognateset, cogset_type="grammatical").render()}
        </div>
        <div id="tadding" class="tab-pane">
			${request.get_datatable('cognatesets', u.cariban_models.Cognateset, cogset_type="t_adding").render()}
        </div>
        <div id="swadesh" class="tab-pane">
			${request.get_datatable('cognatesets', u.cariban_models.Cognateset, cogset_type="lexical").render()}
        </div>
    </div>
</div>