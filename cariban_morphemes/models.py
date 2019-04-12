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
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from clld import interfaces
from cariban_morphemes.interfaces import IConstruction
from clld.db.meta import Base, CustomModelMixin, PolymorphicBaseMixin
from clld.db.models import UnitParameter, Unit, Value, Parameter, ValueSet, UnitValue, Sentence, IdNameDescriptionMixin, HasSourceMixin

@implementer(interfaces.IUnitParameter)
class Meaning(CustomModelMixin, UnitParameter):
    pk = Column(Integer, ForeignKey('unitparameter.pk'), primary_key=True)
    form = Column(String)
    
@implementer(interfaces.IParameter)
class CognateSet(CustomModelMixin, Parameter, HasSourceMixin):
    pk = Column(Integer, ForeignKey('parameter.pk'), primary_key=True)

@implementer(IConstruction)
class Construction(Base, PolymorphicBaseMixin, IdNameDescriptionMixin):
    pk = Column(Integer, ForeignKey('contribution.pk'), primary_key=True)

@implementer(interfaces.IUnit)
class Morpheme(CustomModelMixin, Unit):
    pk = Column(Integer, ForeignKey('unit.pk'), primary_key=True)
    construction_pk = Column(Integer, ForeignKey("construction.pk"))
    construction = relationship(Construction, backref='morphemes')

@implementer(interfaces.IValue)
class Counterpart(CustomModelMixin, Value):
    pk = Column(Integer, ForeignKey('value.pk'), primary_key=True)
    morpheme_pk = Column(Integer, ForeignKey('morpheme.pk'))
    morpheme = relationship(Morpheme, backref='counterparts')
    
class UnitValueSentence(Base, PolymorphicBaseMixin):

    """Association between values and sentences given as explanation of a value."""

    __table_args__ = (UniqueConstraint('unitvalue_pk', 'sentence_pk'),)

    unitvalue_pk = Column(Integer, ForeignKey('unitvalue.pk'), nullable=False)
    sentence_pk = Column(Integer, ForeignKey('sentence.pk'), nullable=False)
    description = Column(Unicode())

    unitvalue = relationship(UnitValue, innerjoin=True, backref='sentence_assocs')
    sentence = relationship(Sentence, innerjoin=True, backref='unitvalue_assocs', order_by=Sentence.id)