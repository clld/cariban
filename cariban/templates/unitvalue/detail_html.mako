<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "unitparameters" %>

<h2>${_('Unit Value')} ${ctx.name}</h2>

<dl>
    <dt>Language:</dt>
    <dd>${h.link(request, ctx.unit.language)}</dd>
    <dt>Function:</dt>
    <dd>${h.link(request, ctx.unitparameter)}</dd>
</dl>

