<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "parameters" %>
<%block name="title">${_('Cognate set')} ${ctx.name}</%block>

<h2>${_('Cognate set')} ${ctx.name}</h2>

% if ctx.references:
<p>Source: (${h.linked_references(request, ctx)|n})</p>
% endif
Original function: ${ctx.description}
% if ctx.markup_description:
${h.text2html(h.Markup(ctx.markup_description), mode='p')}
% endif

% if map_ or request.map:
${(map_ or request.map).render()}
% endif

${request.get_datatable('values', h.models.Value, parameter=ctx).render()}
