<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%namespace name="cmutil" file="../cmutil.mako"/>
<%! active_menu_item = "units" %>


<h3>${_('Whaa')} ${ctx.name}</h3>
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
	<td>Source:</td>
	<td>${h.linked_references(request, ctx)|n}</td>
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

% if ctx.description or ctx.markup_description:
${h.text2html(h.Markup("Comments: " + ctx.markup_description) if ctx.markup_description else ctx.description, mode='p')}
% endif
	
<dl>
% for key, objs in h.groupby(ctx.data, lambda o: o.key):
<dt>${key}</dt>
    % for obj in sorted(objs, key=lambda o: o.ord):
    <dd>${obj.value}</dd>
    % endfor
% endfor
</dl>

<h4>${_('Functions:')}</h4>
<%
shown_functions = {}
%>
<%
for i, value in enumerate(ctx.unitvalues):
	if value.unitparameter not in shown_functions.keys():
		shown_functions[value.unitparameter] = {}
	shown_functions[value.unitparameter][value] = value.construction
%>
<dl>
    % for function, function_construction_pair in shown_functions.items():
		<div style="clear: right;">
##		    <ul class="nav nav-pills pull-right">
##		        <li><a data-toggle="collapse" data-target="#s${i}">Show/hide details</a></li>
##		    </ul>
			<h4>
				<% construction_l = len(function_construction_pair.values()) %>
				<dt>${h.link(request, function)}
				<%
				construction_specified = False
				for i, construction in enumerate(function_construction_pair.values()):
					if construction != None: construction_specified = True
				%>
				%if construction_specified:	
				(in the \
				% for i, construction in enumerate(function_construction_pair.values()):
					${h.link(request, construction)}\
					<%
					if i < construction_l-2: comma = ","
					elif i == construction_l-2: comma = "and"
					else: comma = ""
					%>\
					${comma}
				%endfor
				<%
				if construction_l == 1: cons_text = "construction"
				else: cons_text = "constructions"
				%>
				${cons_text})
				%endif
			</dt>
			</h4>
		    <div id="s${i}" class="collapse in">
				% for morphemefunction in function_construction_pair.keys():
					${cmutil.sentences(morphemefunction)}
				%endfor
		    </div>
		</div>
    % endfor
</dl>
