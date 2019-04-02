from clld.web.datatables import Unitparameters, Units, Values, Parameters
from clld.db.models.common import (
    Language
)
from clld.web.datatables.base import (
    Col, LinkCol, PercentCol, IntegerIdCol, LinkToMapCol, DataTable, DetailsRowLinkCol
)
from clld.web.datatables.value import (ValueNameCol, RefsCol)
from clld.web.datatables.unit import (DescriptionLinkCol)

from clld.interfaces import IMenuItems

class CognateSetCol(LinkCol):

    """Render the label for a Value."""

    def get_obj(self, item):
        print(item.counterparts)
        return item.counterparts

    def get_attrs(self, item):
        label = item.__unicode__()
        title = label
        return {'label': label, 'title': title}

    def order(self):
        return DomainElement.number \
            if self.dt.parameter and self.dt.parameter.domain \
            else Value.description

    def search(self, qs):
        if self.dt.parameter and self.dt.parameter.domain:
            return DomainElement.name.__eq__(qs)
        return icontains(Value.description, qs)
        
        
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
            LinkCol(self, 'form'),
            DescriptionLinkCol(self, 'function'),
            LinkCol(
                self, 'language', model_col=Language.name, get_obj=lambda i: i.language),
            # CognateSetCol(self, "cognate sets")
        ]
    
class Cognatesets(Parameters):
    def col_defs(self):
        return [
            DetailsRowLinkCol(self, 'd'),
            LinkCol(self, 'form'),
        ]
        
class Counterparts(Values):
    pass
    
def includeme(config):
    config.register_datatable('unitparameters', Meanings)
    config.register_datatable('units', Morphemes)
    config.register_datatable('parameters', Cognatesets)
    config.register_datatable('values', Counterparts)