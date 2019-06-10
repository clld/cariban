<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "parameters" %>
<%block name="title">${_('Cognate set')} ${ctx.name}</%block>

<h2>${_('Cognate set')} ${ctx.name}</h2>

<table class="table table-nonfluid">
    <tbody>
	<tr>
	<td>Reconstructed form:</td>
	<td>${ctx.name}</td>
	</tr>
	% if ctx.description:
		<tr>
		<td>Original function:</td>
		<td>${ctx.description}</td>
		</tr>
	% endif
	% if ctx.references:
		<tr>
			<td>Source:</td>
			<td>${h.linked_references(request, ctx)|n}</td>
		</tr>
	%endif
    </tbody>
</table>

% if ctx.markup_description:
${h.text2html(h.Markup(ctx.markup_description), mode='p')}
% endif

% if map_ or request.map:
${(map_ or request.map).render()}
% endif

${request.get_datatable('values', h.models.Value, parameter=ctx).render()}
