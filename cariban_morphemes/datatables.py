from clld.web.datatables import Unitparameters, Units, Values, Parameters, Unitvalues, Languages, Sentences
from clld.db.models.common import (
    Language, UnitParameter, UnitValue
)
from clld.db.models import common
from clld.web.datatables.base import (
    Col, LinkCol, PercentCol, IntegerIdCol, LinkToMapCol, DataTable, DetailsRowLinkCol, RefsCol
)
from clld.web.datatables.value import (ValueNameCol)
from clld.web.datatables.unit import (DescriptionLinkCol)
from cariban_morphemes.models import Counterpart, CognateSet, Morpheme, Construction, Meaning, MorphemeFunction
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
    
    def search(self, qs):
        if self.dt.unitparameter and self.dt.unitparameter.domain:
            return common.UnitDomainElement.name.contains(qs)
        return common.UnitValue.name.contains(qs)
            
    def format(self, item):
        obj = self.get_obj(item).unitvalues
        my_link = []
        found_functions = []
        for i in obj:
            if i.unitparameter not in found_functions:
                my_link.append(link(self.dt.req, i.unitparameter, **self.get_attrs(i.unitparameter)))
            found_functions.append(i.unitparameter)
        return my_link
        
class MorphemeCol(LinkCol):
    def __init__(self, dt, name, **kw):
        # kw['sTitle'] = "Cognate"
        Col.__init__(self, dt, name, **kw)
    
    def get_attrs(self, item):
        return dict(label = self.get_obj(item).name)

class Meanings(Unitparameters):
    def col_defs(self):
        return [
            LinkCol(self, 'Gloss'),
        ]
        
class Morphemes(Units):

    def col_defs(self):
        base = [
            LinkCol(self, 'form'),
            FunctionCol(self, 'function'),
        ]
           
        if not self.language:
            base.append(LinkCol(self, 'language', model_col=Language.name, get_obj=lambda i: i.language)
            )  
        return base + [
            CognatesetCol(self, 'cognatesets', get_obj=lambda i: i.counterparts),
            RefsCol(self, 'references'),
        ]
    
class Cognatesets(Parameters):
    def col_defs(self):
        return [
            LinkCol(self, 'reconstructed'),
            Col(self, 'description'),
            RefsCol(self, 'references')
        ]
           
class Counterparts(Values):
    def col_defs(self):
        return [
            LinkCol(self, 'language', model_col=Language.name, get_obj=lambda i: i.morpheme.language),
            MorphemeCol(self, 'form', get_obj=lambda i: i.morpheme),
            FunctionCol(self, 'function', get_obj=lambda i: i.morpheme),
            RefsCol(self, 'references', get_obj=lambda i: i.morpheme)
        ]

class Constructions(DataTable):
    __constraints__ = [Language]
    
    def base_query(self, query):
        
        if self.language:
            return query.filter(Construction.language_pk == self.language.pk)
        
        return query
        
    
    def col_defs(self):
        base = [
            LinkCol(self, 'name')
        ]
        if not self.language:
            base.append(LinkCol(self, 'language', get_obj=lambda i: i.language))
        return base
            

class MorphemeFunctions(Unitvalues):
    __constraints__ = Unitvalues.__constraints__ + [Construction, Language]
    
    def base_query(self, query):
        
        if self.unitparameter:
            query = query.filter(MorphemeFunction.unitparameter_pk == self.unitparameter.pk)
            
        if self.construction:
            query = query.filter(MorphemeFunction.construction_pk == self.construction.pk)
            
        return query
    
    def col_defs(self):
        base = [
            MorphemeCol(self, 'form', get_obj=lambda i: i.unit),
        ]
        if not self.unitparameter:
            base.append(LinkCol(self, 'function', get_obj=lambda i: i.unitparameter))
        if not self.construction:
            base.append(LinkCol(self, 'construction', get_obj=lambda i: i.construction))
        if not self.language and not self.construction:
            base.append(LinkCol(self, 'language', model_col=Language.name, get_obj=lambda i: i.unit.language))
        return base + [
            CognatesetCol(self, 'cognatesets', get_obj=lambda i: i.unit.counterparts),
            RefsCol(self, 'references', get_obj=lambda i: i.unit)
        ]
        
class Languages (Languages):
    def col_defs(self):
        return [
            LinkCol(self, 'name'),
            LinkToMapCol(self, 'm', sTitle="Show on map"),
            Col(self,
                'latitude',
                sDescription='<small>The geographic latitude</small>'),
            Col(self,
                'longitude',
                sDescription='<small>The geographic longitude</small>'),
        ]
   
class TsvCol(Col):
    def search(self, qs):
        return super(TsvCol, self).search('\t'.join(qs.split()))
             
class Sentences(Sentences):

    def col_defs(self):
        base = [
            Col(self, 'id', bSortable=False, input_size='mini'),
            LinkCol(self, 'name', sTitle='Primary text', sClass="object-language"),
            TsvCol(self, 'analyzed', sTitle='Analyzed text'),
            TsvCol(self, 'gloss', sClass="gloss"),
            Col(self,
                'description',
                sTitle=self.req.translate('Translation'),
                sClass="translation"),
            DetailsRowLinkCol(self, "d", sTitle="IGT"),
        ]
        if not self.language:
            base.append(LinkCol(
                self,
                'language',
                model_col=Language.name,
                get_obj=lambda i: i.language,
                bSortable=not self.language,
                bSearchable=not self.language))
        base.append(RefsCol(self, 'references'))
        return base
        
def includeme(config):
    config.register_datatable('unitparameters', Meanings)
    config.register_datatable('units', Morphemes)
    config.register_datatable('parameters', Cognatesets)
    config.register_datatable('values', Counterparts)
    config.register_datatable('sentences', Sentences)
    config.register_datatable('languages', Languages)
    config.register_datatable('unitvalues', MorphemeFunctions)
    config.register_datatable('constructions', Constructions)