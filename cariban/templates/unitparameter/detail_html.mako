<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "unitparameters" %>

% if ctx.meaning_type == "lexical":
	<h2>${_('Meaning')} ‘${ctx.name}’ </h2>
% else:
	<h2>${_('Function')} ${ctx.name} </h2>
% endif 


<div>
    <% dt = request.registry.getUtility(h.interfaces.IDataTable, 'unitvalues'); dt = dt(request, h.models.UnitValue, unitparameter=ctx, meaning_type=ctx.meaning_type) %>
    ${dt.render()}
</div>