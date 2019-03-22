<%! from pynterlinear import pynterlinear %>
<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "morphemes" %>

<%def name="sidebar()">
    % if ctx.value_assocs:
    <%util:well title="${_('Datapoints')}">
        <ul>
        % for va in ctx.value_assocs:
            % if va.value:
            <li>${h.link(request, va.value.valueset, label='%s' % (va.value.valueset.parameter.name))}</li>
            % endif
        % endfor
        </ul>
    </%util:well>
    % endif
</%def>

<h2>${_('Morpheme')} ${ctx.id}</h2>
<dl>
    <dt>${_('Language')}:</dt>
    <dd>${h.link(request, ctx.language)}</dd>
</dl>