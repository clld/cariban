from clld.web.datatables.unit import Units
from clld.web.datatables.parameter import Parameters

# class Morphemes(Units):
#     def col_defs(self):
#         return [
#             IntegerIdCol(self, 'id'),
#             LinkCol(self, 'form'),
#             # Col(self, 'count_entries', sTitle='# Entries')
#         ]
#

# class CognateSets(Parameters):
#     def get_options(self):
#         opts = super(Parameters, self).get_options()
#         opts['aaSorting'] = [[1, 'asc'], [3, 'asc']]
#         return opts
#
# def includeme(config):
#     pass
# #     config.register_datatable('morphemes', Morphemes)
#     config.register_datatable('parameters', CognateSets)