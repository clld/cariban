<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "units" %>


<h2>${_('T-adding sstems')}</h2>
<div>
	${request.get_datatable('tverbs', u.cariban_models.TVerb).render()}
</div>
