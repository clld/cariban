<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "constructions" %>
<%block name="title">${_('Construction')} ${ctx.name}</%block>

${request.get_datatable('constructions', u.cariban_models.Construction, finitetype=ctx).render()}