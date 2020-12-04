<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "languages" %>
<%block name="title">${_('Language')} ${ctx.name}</%block>

<h2>${_('Language')} ${ctx.name}</h2>
% for type_, identifiers in h.groupby(sorted(ctx.identifiers, key=lambda i: i.type), lambda j: j.type):
    % for identifier in identifiers:
    ${type_.capitalize()}: ${h.language_identifier(request, identifier)}
    % endfor
% endfor
<div class="tabbable">
    <ul class="nav nav-tabs">
        <li class="active"><a href="#morphemes" data-toggle="tab">Grammatical morphemes</a></li>
        <li><a href="#constructions" data-toggle="tab">Constructions</a></li>
        <li><a href="#tadding" data-toggle="tab">t-adding verbs</a></li>
		<li><a href="#swadesh" data-toggle="tab">Lexical entries</a></li>
        <li><a href="#sentences" data-toggle="tab">Example sentences</a></li>
        <li><a href="#sources" data-toggle="tab">Sources</a></li>
    </ul>
    <div class="tab-content" style="overflow: visible;">
        <div id="morphemes" class="tab-pane active">
			${request.get_datatable('units', u.cariban_models.Morpheme, language=ctx, morpheme_type="grammatical").render()}
        </div>
        <div id="constructions" class="tab-pane">
            ${request.get_datatable('constructions', u.cariban_models.Construction, language=ctx).render()}
        </div>
        <div id="tadding" class="tab-pane">
			${request.get_datatable('units', u.cariban_models.Morpheme, language=ctx, morpheme_type="t_adding").render()}
        </div>
        <div id="swadesh" class="tab-pane">
			${request.get_datatable('units', u.cariban_models.Morpheme, language=ctx, morpheme_type="lexical").render()}
        </div>
        <div id="sentences" class="tab-pane">
			${request.get_datatable('sentences', h.models.Sentence, language=ctx).render()}
        </div>
        <div id="sources" class="tab-pane">
			${request.get_datatable('sources', h.models.Source, language=ctx).render()}
        </div>
    </div>	
</div>

<%def name="sidebar()">
    ${util.language_meta()}
</%def>