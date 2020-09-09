<% import json %>

${h.text2html(u.generate_markup("""In many Cariban languages, there are some verbs that show a reflex of a prefix rc:t(ɨ)- in certain contexts.
The prefix occurs where one would otherwise expect a reflex of cogset:3i, and does not seem to contribute a meaning of its own (anymore).
An overview of all cognates of such t-adding verbs in the database can be found <a href=/function/t-verb>here</a>.
Some sources (src:triomeira1999[234] for lg:tri, src:maquiritaricaceres2011[127] for lg:mak, src:wayanatavares2005[199] for lg:way, src:hixkaryanaderby1985[192--193] for lg:hix, src:waiwaihawkins1998[192] for lg:wai, and src:alves2017arara[156] for lg:ara) explicitly mention the lexically conditioned nature of this prefix and provide a list.
In these cases, I assumed that if a verb was not listed there, but does occur in the language, it shows no obj:t-.
In other cases, it is unclear whether a given verb would occur with obj:t-, given the right context.

The tree below shows, for any given language, how many of the reflexes of a verb that show rc:t- in some other language occur with a reflex of obj:t- in this language.
The first observation is that languages that are usually included in the Venezuelan branch show little to zero occurrences of rc:t-.
Also, lg:kalina seems to have absolutely zero reflexes of rc:t-.
lg:waimiri only has one potential example of rc:t-, and it is unclear whether that is the case, or whether it is the rc:t- occurring in the rc:t-Σ-tjɤ construction.

As for the verbs that trigger obj:t-, there is quite a bit of heterogeneity.
Some verbs only show reflexes in a subset of languages.
Other verbs have reflexes in a language that otherwise has rc:t-, but not for this verb.
In languages that have an overt reflex of cogset:3i in their person marking prefixes (lg:tri, lg:way, lg:mak, lg:arara), this /i/ disappears and is sometimes replaced by an /ɨ/.
In lg:arara and lg:maqui, most of the t-adding stems are analyzed as being /ɨ/-initial.

It can be argued that the core of this lexical cluster is cogset:t10 'to do, make, give'.
While, due to its complete absence from lg:arara/lg:ikpeng, it is not attested across the family, it shows rc:t- in all other languages that have reflexes of rc:t-, <b>including the Venezuelan branch</b>.
Reflexes of cogset:t10 also show interesting irregular properties.
In lg:trio, morph:tri_t10 does not show the usual form morph:tri_3sa_pst, but obj:kɨnɨ- (src:triomeira1999[308--309]).
[TO BE CONTINUED].

The solidly attested verbs are cogset:t1 'to eat starchy food', cogset:t14 'to shoot, kill', and cogset:t6 'to grate manioc', which occur in all subbranches for which reflexes of rc:t- are attested.
I have not found reflexes of cogset:t2 'to eat meat' in Pekodian, but it is attested to occur with rc:t- across the rest of the (t-adding) family.
Similarly, I have not found reflexes of cogset:t9 'to bathe' in lg:kuikuro, but it occurs with rc:t- everywhere else.

Then there are some verbs with a more restricted distribution:
cogset:t5 'to weave, make' is attested with rc:t- only in Guianan and Pekodian.
Reflexes of cogset:t3 'to take out' only occur in four Northern Amazonian languages.
cogset:t12 'to give' and cogset:t21 'to bring' are restricted to Parukotoan.
cogset:t7 'to throw out' shows rc:t- only in lg:trio and lg:maqui, but not in lg:apalai, which also has a reflex of it.
Similarly, cogset:t8 'to gather fruit' only shows rc:t- in these two languages, but not in Parukotoan and lg:wayana.
It is unclear whether the lg:kuikuro reflex of cogset:t4 'to blow, light fire' shows rc:t-; it is only attested in lg:trio otherwise.
For cogset:t19 'to dig out', it is unclear whether lg:ikpeng morph:ikp_t19 'to peel' is cognate or not; if not, the verb would only be attested in lg:maqui.

Finally, there is also a range of verbs which either only occur with rc:t- in a single language, or are even only attested at all for a single language:
cogset:t22 'to see' is attested across the family, but only shows rc:t- in lg:hixka.
Similarly, widely found cogset:t17 'to leave, abandon' only shows rc:t- in lg:waiwai.
lg:maqui has 2 t-adding verbs exclusive to it (src:maquiritaricaceres2011[127]), for lg:ikpeng I have found 4, and src:alves2017arara[156] lists 7 t-adding verbs that only occur in lg:arara.
src:gildea2007greenberg[29] give an additional verb which I was unable to find anywhere, cogset:t15 'to farm, fell'.
"""))}
<div id="my_tree"></div>







<% t_values = u.t_adding_pct() %>
<% my_tree = u.get_tree(
	request,
	t_values,
	"my_tree")
%>
<script>
	$(function() {
	    $('#my_tree').tree({
	        data: [
	    ${ json.dumps(my_tree) | n },
	],
			autoEscape: false,
			autoOpen: true
	    });
	});
</script>