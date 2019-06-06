<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "parameters" %>
<%block name="title">${_('Construction')} ${ctx.name}</%block>

<h2>The ${h.link(request, ctx.language)} ${ctx.name} clause</h2>

% if ctx.source:
<p>Source: (${h.linked_references(request, ctx)|n})</p>
% endif
% if ctx.description:
<p>${ctx.description}</p>
% elif ctx.markup_description:
${h.text2html(h.Markup(ctx.markup_description) if ctx.markup_description else ctx.description, mode='p')}
% endif

${request.get_datatable('unitvalues', h.models.UnitValue, construction=ctx).render()}

## This is what is called for the language index view in vanilla CLLD
## ${request.get_datatable('values', h.models.Value, language=ctx).render()}


## Values for a parameter
## ${request.get_datatable('values', h.models.Value, parameter=ctx).render()}
