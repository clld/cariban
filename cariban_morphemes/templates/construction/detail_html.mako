<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "constructions" %>
<%block name="title">${_('Construction')} ${ctx.name}</%block>

<h2>
	The ${h.link(request, ctx.language)} ${ctx.name} clause
</h2>
% if ctx.declarativetype or ctx.finitetype:
<p>(\
% if ctx.declarativetype:
${h.link(request, ctx.declarativetype)}\
% endif
% if ctx.declarativetype and ctx.finitetype:
,
%endif
% if ctx.finitetype:
${h.link(request, ctx.finitetype)}\
% endif
)</p>
% endif

% if ctx.source:
<p>Source: (${h.linked_references(request, ctx)|n})</p>
% endif
% if ctx.description:
<p>${ctx.description}</p>
% elif ctx.markup_description:
${h.text2html(h.Markup(ctx.markup_description) if ctx.markup_description else ctx.description, mode='p')}
% endif

${request.get_datatable('unitvalues', h.models.UnitValue, construction=ctx).render()}