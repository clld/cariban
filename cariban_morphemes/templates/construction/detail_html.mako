<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "parameters" %>
<%block name="title">${_('Construction')} ${ctx.name}</%block>

<h2>The ${h.link(request, ctx.language)} ${ctx.name}</h2>

% if ctx.description:
<p>Source: (${h.linked_references(request, ctx)|n})</p>
% endif
% if ctx.description:
<p>${ctx.description}</p>
% elif ctx.markup_description:
${h.text2html(h.Markup(ctx.markup_description) if ctx.markup_description else ctx.description, mode='p')}
% endif

% if map_ or request.map:
${(map_ or request.map).render()}
% endif

${request.get_datatable('constructionmorphemes', h.models.Unit, construction=ctx.morphemefunctions).render()}