<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "parameters" %>
<%block name="title">${_('Cognate set')} ${ctx.name}</%block>

<h2>${_('Cognate set')} ${ctx.name}</h2>

<p>Source: (${h.linked_references(request, ctx)|n})</p>
% if ctx.description:
<p>${ctx.description}</p>
% endif

% if map_ or request.map:
${(map_ or request.map).render()}
% endif

${request.get_datatable('values', h.models.Value, parameter=ctx).render()}
