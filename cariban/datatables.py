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
from cariban.models import Cognate, Cognateset, Morpheme, Construction, Meaning, MorphemeFunction, DeclarativeType, MainClauseVerb
from clld.interfaces import IMenuItems
from clld.web.util.helpers import (
    link, button, icon, JS_CLLD, external_link, linked_references, JSDataTable,
)
from sqlalchemy.orm import joinedload
from clldutils.misc import dict_merged

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
            my_link.append(link(self.dt.req, i.cognateset, **self.get_attrs(i.cognateset)))
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
        found_functions = []
        for i in obj:
            if i.unitparameter not in found_functions:
                my_link.append(link(self.dt.req, i.unitparameter, **self.get_attrs(i.unitparameter)))
            found_functions.append(i.unitparameter)
        return my_link
    
    def search(self, qs):
        return Morpheme.unitvalues.any(UnitValue.name.contains(qs))
        
class Meanings(Unitparameters):
    
    def __init__(self, req, model, **kw):
        self.meaning_type = kw.pop('meaning_type', req.params.get('meaning_type', None))
        if self.meaning_type:
            kw['eid'] = 'Meanings-' + self.meaning_type
        super(Meanings, self).__init__(req, model, **kw)
    
    def xhr_query(self):
        return dict_merged(super(Meanings, self).xhr_query(), meaning_type=self.meaning_type)
        
    def base_query(self, query):
        if self.meaning_type:
            query = query.filter(Meaning.meaning_type == self.meaning_type)
        return query
        
    def col_defs(self):
        return [
            LinkCol(self, 'Gloss', model_col=UnitParameter.name),
        ]

class Morphemes(Units):
    
    __constraints__ = [MorphemeFunction, Language, Cognateset]
    
    def __init__(self, req, model, **kw):
        self.morpheme_type = kw.pop('morpheme_type', req.params.get('morpheme_type', None))
        if self.morpheme_type:
            kw['eid'] = 'Morphemes-' + self.morpheme_type
        super(Morphemes, self).__init__(req, model, **kw)
    
    def xhr_query(self):
        return dict_merged(super(Morphemes, self).xhr_query(), morpheme_type=self.morpheme_type)
                
    def base_query(self, query):
        query = query.join(Language).join(Cognate).options(
            joinedload(
                Morpheme.language
            )
            )

        if self.language:
            query = query.filter(Morpheme.language == self.language)
        
        if self.morpheme_type:
            query = query.filter(Morpheme.morpheme_type == self.morpheme_type)
        
        return query
        
    def col_defs(self):
        base = [
            LinkCol(self, 'form', model_col=Morpheme.name),
            FunctionCol(self, 'function', bSortable=False),
        ]
           
        if not self.language:
            base.append(LinkCol(self, 'language', model_col=Language.name, get_obj=lambda i: i.language)
            )  
        return base + [
            CognatesetCol(self, 'cognatesets', get_obj=lambda i: i.counterparts, bSearchable=False ),
            RefsCol(self, 'references'),
        ]
    
class Cognatesets(DataTable):
    def col_defs(self):
        return [
            LinkCol(self, 'reconstructed', model_col=Cognateset.name),
            Col(self, 'description'),
            RefsCol(self, 'references')
        ]
        
class Cognates(DataTable):
    
    __constraints__ = [Cognateset, Language]
    
    def base_query(self, query):
        
        query = query\
        .join(Morpheme)\
        .join(Language)
        
        
        if self.cognateset:
            return query.filter(Cognate.cognateset_pk == self.cognateset.pk)
            
    def col_defs(self):
        return [
            LinkCol(self, 'language', get_obj=lambda i: i.counterpart.language, model_col=Language.name),
            LinkCol(self, 'form', get_obj=lambda i: i.counterpart, model_col=Morpheme.name),
            FunctionCol(self, 'function', get_obj=lambda i: i.counterpart),
            RefsCol(self, 'references', get_obj=lambda i: i.counterpart)
        ]

class Constructions(DataTable):
    __constraints__ = [Language, DeclarativeType, MainClauseVerb]

    def base_query(self, query):
        
        query = query.join(Language).outerjoin(DeclarativeType).join(MainClauseVerb).options(joinedload(Construction.language))
        
        if self.language:
            return query.filter(Construction.language == self.language)
        
        if self.declarativetype:
            return query.filter(Construction.declarativetype_pk == self.declarativetype.pk)
            
        if self.mainclauseverb:
            return query.filter(Construction.mainclauseverb_pk == self.mainclauseverb.pk)
        
        return query
        
    
    def col_defs(self):
        base = [
            LinkCol(self, 'name'),
        ]
        if not self.language:
            base.append(LinkCol(self, 'language', get_obj=lambda i: i.language, model_col=Language.name))

        if not self.declarativetype:
            base.append(LinkCol(self, 'declarativetype', sTitle="Declarative?", get_obj=lambda i: i.declarativetype, model_col=DeclarativeType.name))
            
        if not self.mainclauseverb:
            base.append(LinkCol(self, 'mainclauseverb', sTitle="Main clause verb?", get_obj=lambda i: i.mainclauseverb, model_col=MainClauseVerb.name))
            
        return base
            

class MorphemeFunctions(Unitvalues):
    __constraints__ = Unitvalues.__constraints__ + [Construction, Language]
    
    def base_query(self, query):
        
        query = query\
            .join(Morpheme)\
            .join(Language)\
            .join(Construction)\
            .join(UnitParameter)

        if self.unitparameter:
            query = query.filter(MorphemeFunction.unitparameter_pk == self.unitparameter.pk)
            
        if self.construction:
            query = query.filter(MorphemeFunction.construction_pk == self.construction.pk)
            
        return query
    
    def col_defs(self):
        base = [
            LinkCol(self, 'form', get_obj=lambda i: i.unit, model_col=Morpheme.name),
        ]
        if not self.unitparameter:
            base.append(FunctionCol(self, 'function', get_obj=lambda i: i.unit))
        if not self.construction:
            base.append(LinkCol(self, 'construction', get_obj=lambda i: i.construction, model_col=Construction.name))
        if not self.language and not self.construction:
            base.append(LinkCol(self, 'language', model_col=Language.name, get_obj=lambda i: i.unit.language))
        return base + [
            CognatesetCol(self, 'cognatesets', get_obj=lambda i: i.unit.counterparts, bSearchable=False),
            RefsCol(self, 'references', get_obj=lambda i: i.unit)
        ]
        
class Languages(Languages):
    def col_defs(self):
        return [
            LinkCol(self, 'name'),
            LinkToMapCol(self, 'm', sTitle="Show on map"),
            Col(self,
                'latitude',
                sDescription='<small>The geographic latitude</small>',
                bSearchable=False
                ),
                
            Col(self,
                'longitude',
                sDescription='<small>The geographic longitude</small>',
                bSearchable=False
                ),
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
    config.register_datatable('cognates', Cognates)
    config.register_datatable('cognatesets', Cognatesets)
    # config.register_datatable('values', Counterparts)
    config.register_datatable('sentences', Sentences)
    config.register_datatable('languages', Languages)
    config.register_datatable('unitvalues', MorphemeFunctions)
    config.register_datatable('constructions', Constructions)