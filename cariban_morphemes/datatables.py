from clld.web.datatables import Unitparameters, Units, Values, Parameters, Unitvalues, Languages
from clld.db.models.common import (
    Language
)
from clld.web.datatables.base import (
    Col, LinkCol, PercentCol, IntegerIdCol, LinkToMapCol, DataTable, DetailsRowLinkCol, RefsCol
)
from clld.web.datatables.value import (ValueNameCol)
from clld.web.datatables.unit import (DescriptionLinkCol)
from cariban_morphemes.models import Counterpart, CognateSet, Morpheme
from clld.interfaces import IMenuItems
from clld.web.util.helpers import (
    link, button, icon, JS_CLLD, external_link, linked_references, JSDataTable,
)
class CognatesetCol(Col):
    def __init__(self, dt, name, **kw):
        kw['sTitle'] = "Cognate set(s)"
        Col.__init__(self, dt, name, **kw)

    def get_attrs(self, item):
        return dict(label = item)
    
    def format(self, item):
        obj = self.get_obj(item)
        my_link = []
        for i in obj:
            my_link.append(link(self.dt.req, i.valueset.parameter, **self.get_attrs(i.valueset.parameter)))
        return my_link

class FunctionCol(LinkCol):
    def __init__(self, dt, name, **kw):
        kw['sTitle'] = "Function(s)"
        Col.__init__(self, dt, name, **kw)
    
    def get_attrs(self, item):
        return dict(label = item)
        
    def format(self, item):
        obj = self.get_obj(item).unitvalues
        my_link = []
        for i in obj:
            my_link.append(link(self.dt.req, i.unitparameter, **self.get_attrs(i.unitparameter)))
        return my_link
        
class MorphemeCol(LinkCol):
    def __init__(self, dt, name, **kw):
        # kw['sTitle'] = "Cognate"
        Col.__init__(self, dt, name, **kw)
    
    def get_attrs(self, item):
        return dict(label = self.get_obj(item).name)
      
    # def format(self, item):
    #     return(self.get_obj(item).name)
        
class Meanings(Unitparameters):
    def col_defs(self):
        return [
            LinkCol(self, 'Gloss'),
        ]

class Morphemes(Units):
    def col_defs(self):
        return [
            LinkCol(self, 'form'),
            DescriptionLinkCol(self, 'function'),
            LinkCol(self, 'language', model_col=Language.name, get_obj=lambda i: i.language),
            CognatesetCol(self, 'cognatesets', get_obj=lambda i: i.counterparts),
            RefsCol(self, 'references'),
        ]
    
class Cognatesets(Parameters):
    def col_defs(self):
        return [
            # DetailsRowLinkCol(self, 'd'),
            LinkCol(self, 'reconstructed'),
            RefsCol(self, 'references')
        ]

class LanguageMorphemes(Units):
    def col_defs(self):
        return [
            LinkCol(self, 'form'),
            DescriptionLinkCol(self, 'function'),
            LinkCol(self, 'language', model_col=Language.name, get_obj=lambda i: i.language),
            CognatesetCol(self, 'cognatesets', get_obj=lambda i: i.counterparts),
            RefsCol(self, 'references'),
        ]
           
class Counterparts(Values):
    def col_defs(self):
        return [
            LinkCol(self, 'language', model_col=Language.name, get_obj=lambda i: i.morpheme.language),
            MorphemeCol(self, 'form', get_obj=lambda i: i.morpheme),
            FunctionCol(self, 'function', get_obj=lambda i: i.morpheme),
            RefsCol(self, 'references', get_obj=lambda i: i.morpheme)
        ]

class Functions(Unitvalues):
    def col_defs(self):
        return [
            MorphemeCol(self, 'form', get_obj=lambda i: i.unit),
            LinkCol(self, 'language', model_col=Language.name, get_obj=lambda i: i.unit.language),             
            RefsCol(self, 'references', get_obj=lambda i: i.unit),
            CognatesetCol(self, 'cognatesets', get_obj=lambda i: i.unit.counterparts),
        ]

class Languages(Languages):
    def col_defs(self):
        return [
            LinkCol(self, 'name'),
            LinkToMapCol(self, 'm'),
            Col(self,
                'latitude',
                sDescription='<small>The geographic latitude</small>'),
            Col(self,
                'longitude',
                sDescription='<small>The geographic longitude</small>'),
        ]
        
def includeme(config):
    config.register_datatable('unitparameters', Meanings)
    config.register_datatable('units', Morphemes)
    config.register_datatable('unitvalues', Functions)
    config.register_datatable('parameters', Cognatesets)
    config.register_datatable('values', Counterparts)
    config.register_datatable('languages', Languages)
    config.register_datatable('languagemorphemes', LanguageMorphemes)