<% import markdown %>
<% set_1_clauses = ["apa_main", "tri_main", "way_main", "mak_main", "kar_main", "hix_main", "wai_main", "ara_main", "ikp_main", "wmr_main", "pan_pstpfv", "ing_old"] %>
% for c in set_1_clauses:
	${c}
	${h.Markup(u.generate_markup(u.transitive_construction_paradigm(c)))}<br>
% endfor