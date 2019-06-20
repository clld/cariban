<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "pages" %>
<%block name="title">${ctx.name}</%block>

<h2>
	${ctx.name}
</h2>
<%include file="${'%s.mako' % ctx.id}"/>