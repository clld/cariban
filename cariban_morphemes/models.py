from zope.interface import implementer
from sqlalchemy import (
    Column,
    String,
    Unicode,
    Integer,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
import sqlalchemy as sa
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from clld import interfaces
from cariban_morphemes.interfaces import IConstruction, IDeclarativeType, IMainClauseVerb, IPage, ICognateset, ICognate
from clld.db.meta import Base, CustomModelMixin, PolymorphicBaseMixin
from clld.db.models import UnitParameter, Unit, Value, Parameter, ValueSet, UnitValue, Sentence, IdNameDescriptionMixin, HasSourceMixin, common, Language

@implementer(interfaces.IUnitParameter)
class Meaning(CustomModelMixin, UnitParameter):
    pk = Column(Integer, ForeignKey('unitparameter.pk'), primary_key=True)
    form = Column(String)
    meaning_type = Column(String)
    
@implementer(IDeclarativeType)
class DeclarativeType(Base, IdNameDescriptionMixin):
    pk = Column(Integer, primary_key=True)
    
@implementer(IMainClauseVerb)
class MainClauseVerb(Base, IdNameDescriptionMixin):
    pk = Column(Integer, primary_key=True)
    
@implementer(IConstruction)
class Construction(Base, PolymorphicBaseMixin, IdNameDescriptionMixin, HasSourceMixin):
    pk = Column(Integer, primary_key=True)
    language = relationship(Language, backref="constructions")
    language_pk = Column(Integer, ForeignKey("language.pk"))
    declarativetype = relationship(DeclarativeType, backref="constructions")
    declarativetype_pk = Column(Integer, ForeignKey("declarativetype.pk"))
    mainclauseverb = relationship(MainClauseVerb, backref="constructions")
    mainclauseverb_pk = Column(Integer, ForeignKey("mainclauseverb.pk"))
    
@implementer(interfaces.IUnit)
class Morpheme(CustomModelMixin, Unit, HasSourceMixin):
    morpheme_type = Column(String)
    pk = Column(Integer, ForeignKey('unit.pk'), primary_key=True)
    construction_pk = Column(Integer, ForeignKey("construction.pk"))
        
@implementer(interfaces.IUnitValue)
class MorphemeFunction(UnitValue, CustomModelMixin, PolymorphicBaseMixin):
    pk = Column(Integer, ForeignKey('unitvalue.pk'), primary_key=True)
    construction = relationship(Construction, backref="morphemefunctions")
    construction_pk = Column(Integer, ForeignKey("construction.pk"))
    
class MorphemeReference(Base, common.HasSourceMixin):
    morpheme_pk = Column(Integer, ForeignKey('unit.pk'))
    morpheme = relationship(Morpheme, backref="references")

@implementer(ICognateset)
class Cognateset(Base,
                 PolymorphicBaseMixin,
                 IdNameDescriptionMixin,
                 ):
    pk = Column(Integer, primary_key=True)

class CognatesetReference(Base, HasSourceMixin):
    cognateset_pk = sa.Column(sa.Integer, sa.ForeignKey('cognateset.pk'))
    cognateset = sa.orm.relationship(Cognateset, backref="references")

@implementer(ICognate)
class Cognate(Base):
    """
    The association table between morphemes in particular languages and
    cognate sets.
    """
    cognateset_pk = sa.Column(sa.Integer, sa.ForeignKey('cognateset.pk'))
    cognateset = sa.orm.relationship(Cognateset, backref='cognates')
    counterpart_pk = sa.Column(sa.Integer, sa.ForeignKey('morpheme.pk'))
    counterpart = sa.orm.relationship(Morpheme, backref='counterparts')
    
@implementer(IPage)
class Page(Base, IdNameDescriptionMixin):
    pk = Column(Integer, primary_key=True)
    
class UnitValueSentence(Base, PolymorphicBaseMixin):

    """Association between values and sentences given as explanation of a value."""

    __table_args__ = (UniqueConstraint('unitvalue_pk', 'sentence_pk'),)

    unitvalue_pk = Column(Integer, ForeignKey('unitvalue.pk'), nullable=False)
    sentence_pk = Column(Integer, ForeignKey('sentence.pk'), nullable=False)
    description = Column(Unicode())

    unitvalue = relationship(UnitValue, innerjoin=True, backref='sentence_assocs')
    sentence = relationship(Sentence, innerjoin=True, backref='unitvalue_assocs', order_by=Sentence.id)