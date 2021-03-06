<%! from itertools import chain %>
<%def name="sentences(obj=None, fmt='long')">
	<%import cariban.util as cmutil%>
    <% obj = obj or ctx %>
    <ul id="sentences-${obj.pk}" class="unstyled">
        % for a in obj.sentence_assocs:
            <li>
                <blockquote style="margin-top: 5px;">
                    ${h.link(request, a.sentence, label='(%s)' % (a.sentence.id))}
                    % if a.description and fmt == 'long':
                        <p>${a.description}</p>
                    % endif
                    ${cmutil.rendered_sentence(a.sentence, fmt=fmt)}
                    % if (a.sentence.references or a.sentence.source) and fmt == 'long':
                        (${h.linked_references(request, a.sentence)|n}) <span class="muted"></span>
                    % endif
                </blockquote>
            </li>
        % endfor
    </ul>
</%def>