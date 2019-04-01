from clld.web.datatables import Unitparameters, Units, Values, Parameters
from clld.db.models.common import (
    Language
)
from clld.web.datatables.base import (
    Col, LinkCol, PercentCol, IntegerIdCol, LinkToMapCol, DataTable, DetailsRowLinkCol
)
from clld.web.datatables.value import (ValueNameCol, RefsCol)
from clld.web.datatables.unit import (DescriptionLinkCol)

class Meanings(Unitparameters):
    def col_defs(self):
        return [
            IntegerIdCol(self, 'id'),
            LinkCol(self, 'form'),
            # Col(self, 'count_entries', sTitle='# Entries')
        ]

class Morphemes(Units):
    def col_defs(self):
        return [
            LinkCol(self, 'name'),
            DescriptionLinkCol(self, 'description'),
            LinkCol(
                self, 'language', model_col=Language.name, get_obj=lambda i: i.language),
        ]
    
class Cognatesets(Parameters):
    def col_defs(self):
        return [
            DetailsRowLinkCol(self, 'd'),
            LinkCol(self, 'name'),
        ]
        
class Counterparts(Values):
    pass
    
def includeme(config):
    config.register_datatable('unitparameters', Meanings)
    config.register_datatable('units', Morphemes)
    config.register_datatable('parameters', Cognatesets)
    config.register_datatable('values', Counterparts)