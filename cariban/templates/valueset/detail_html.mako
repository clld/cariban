<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%namespace name="cmutil" file="../cmutil.mako"/>
<%! active_menu_item = "contributions" %>

<h3>${h.link(request, ctx.language)} ${_('reflexes of')} ${h.link(request, ctx.parameter)}</h3>

% if ctx.description:
${h.text2html(h.Markup(ctx.markup_description) if ctx.markup_description else ctx.description, mode='p')}
% endif

% for i, value in enumerate(ctx.values):
<%unit = value.morpheme%>
<dl>
<h4>${h.link(request, unit)}</h4>
Functions:
    % for j, unitvalue in enumerate(unit.unitvalues):
		<div style="clear: right;">
		    <ul class="nav nav-pills pull-right">
		        <li><a data-toggle="collapse" data-target="#s${j}">Show/hide details</a></li>
		    </ul>
			<h4>
				<dt>${h.link(request, unitvalue.unitparameter)}</dt>
			</h4>
		    <div id="s${j}" class="collapse in">
				${cmutil.sentences(unitvalue)}
		    </div>
		</div>
    ##<dd>${h.link(request, unitvalue)}</dd>
    % endfor
</dl>
% endfor

<%def name="sidebar()">
<div class="well well-small">
<dl>
    <dt class="language">${_('Language')}:</dt>
    <dd class="language">${h.link(request, ctx.language)}</dd>
    <dt class="parameter">${_('Cognate set')}:</dt>
    <dd class="parameter">${h.link(request, ctx.parameter)}</dd>
    % if ctx.references or ctx.source:
    <dt class="source">${_('Source')}:</dt>
        % if ctx.source:
        <dd>${ctx.source}</dd>
        % endif
        % if ctx.references:
        <dd class="source">${h.linked_references(request, ctx)|n}</dd>
        % endif
    % endif
    ${util.data(ctx, with_dl=False)}
</dl>
</div>
</%def>
