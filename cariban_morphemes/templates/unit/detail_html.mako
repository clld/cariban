<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%namespace name="cmutil" file="../cmutil.mako"/>
<%! active_menu_item = "units" %>


<h3>${_('Morpheme')} ${ctx.name}</h3>

## <p>
##     ${ctx.description}
## </p>

<table class="table table-nonfluid">
    <tbody>
	<tr>
	<td>Form:</td>
	<td>${ctx.name}</td>
	</tr>
	<tr>
	<td>Language:</td>
	<td>${h.link(request, ctx.language)}</td>
	</tr>
	<tr>
	<td>Cognate set(s):</td>
	<td>
	% if ctx.counterparts:
		<ul class="inline">
			% for c in ctx.counterparts:
				<li>${h.link(request, c.valueset.parameter)}</li>
			% endfor
		</ul>
	% endif
	</td>
	</tr>
    </tbody>
</table>

<dl>
% for key, objs in h.groupby(ctx.data, lambda o: o.key):
<dt>${key}</dt>
    % for obj in sorted(objs, key=lambda o: o.ord):
    <dd>${obj.value}</dd>
    % endfor
% endfor
</dl>

<h4>${_('Functions:')}</h4>
<dl>
    % for i, value in enumerate(ctx.unitvalues):
		<div style="clear: right;">
		    <ul class="nav nav-pills pull-right">
		        <li><a data-toggle="collapse" data-target="#s${i}">Show/hide details</a></li>
		    </ul>
			<h4>
				<dt>${h.link(request, value.unitparameter)}</dt>
			</h4>
		    <div id="s${i}" class="collapse in">
				${cmutil.sentences(value)}
		    </div>
		</div>
    ##<dd>${h.link(request, value)}</dd>
    % endfor
</dl>
