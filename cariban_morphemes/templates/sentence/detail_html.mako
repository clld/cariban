<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%import cariban_morphemes.util as cmutil%>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "sentences" %>

<%def name="sidebar()">
    % if ctx.value_assocs:
    <%util:well title="${_('Cognate sets')}">
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

<h3>${_('Sentence')} ${ctx.id}</h3>

${h.link(request, ctx.language)}
% if ctx.source:
<dd>${ctx.source.split("[")[0]}: ${ctx.source.split("[")[1].split("]")[0]}</dd>
% endif
% if ctx.references:
(${h.linked_references(request, ctx)|n})
% endif
${cmutil.rendered_sentence(ctx)|n}

<dl>
% if ctx.comment:
<dt>Comment:</dt>
<dd>${ctx.markup_comment or ctx.comment|n}</dd>
% endif
% if ctx.type:
<dt>${_('Type')}:</dt>
<dd>${ctx.type}</dd>
% endif
</dl>
