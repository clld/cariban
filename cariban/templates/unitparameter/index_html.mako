<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "unitparameters" %>


<h2>${_('Functions')}</h2>

<div class="tabbable">
    <ul class="nav nav-tabs" id="all_meanings" role="tablist">
        <li class="active"><a href="#inflectional" data-toggle="tab">Inflectional</a></li>
        <li><a href="#derivational" data-toggle="tab">Other</a></li>
        <li><a href="#lexical" data-toggle="tab">Lexical meanings</a></li>
    </ul>
    <div class="tab-content" style="overflow: visible;">
        <div id="inflectional" class="tab-pane active">
			${request.get_datatable('unitparameters', u.cariban_models.Meaning, meaning_type="inflectional").render()}
        </div>
        <div id="derivational" class="tab-pane">
			${request.get_datatable('unitparameters', u.cariban_models.Meaning, meaning_type="derivational").render()}
        </div>
        <div id="lexical" class="tab-pane">
			${request.get_datatable('unitparameters', u.cariban_models.Meaning, meaning_type="lexical").render()}
        </div>
    </div>	
</div>