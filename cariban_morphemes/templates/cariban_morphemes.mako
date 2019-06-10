<%inherit file="app.mako"/>


<%block name="brand">
    <a class="brand" style="padding-top: 7px; padding-bottom: 5px;" href="${request.route_url('dataset')}" title="${request.dataset.name}">
        Cariban Morphology
    </a>
</%block>

${next.body()}
