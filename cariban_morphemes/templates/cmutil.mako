<%! from itertools import chain %>
<%def name="sentences(obj=None, fmt='long')">
	<%import cariban_morphemes.util as cmutil%>
    <% obj = obj or ctx %>
    <ul id="sentences-${obj.pk}" class="unstyled">
        % for a in obj.sentence_assocs:
            <li>
                <blockquote style="margin-top: 5px;">
                    ${h.link(request, a.sentence, label='%s %s:' % (_('Sentence'), a.sentence.id))}<br>
                    % if a.description and fmt == 'long':
                        <p>${a.description}</p>
                    % endif
                    ${cmutil.rendered_sentence(a.sentence, fmt=fmt)}
                    % if (a.sentence.references or a.sentence.source) and fmt == 'long':
                        Source: ${h.linked_references(request, a.sentence)|n} <span class="muted"></span>
                    % endif
                </blockquote>
            </li>
        % endfor
    </ul>
</%def>