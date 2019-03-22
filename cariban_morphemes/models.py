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
# import cariban_morphemes
# from cariban_morphemes import interfaces
import clld
from clld.db.meta import Base, CustomModelMixin, PolymorphicBaseMixin
from clld.db.models.common import (
    Language,
    Parameter,
    Value,
    ValueSet,
    Contribution,
    Unit,
    UnitValue,
    UnitParameter,
    Sentence,
    UnitDomainElement,
    IdNameDescriptionMixin,
)

#from clld.db.models.common import Language


# -----------------------------------------------------------------------------
# specialized common mapper classes
# -----------------------------------------------------------------------------
@implementer(clld.interfaces.ILanguage)
class cariban_morphemesLanguage(CustomModelMixin, Language):
   pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)

class UnitValueSentence(Base, PolymorphicBaseMixin):

    """Association between values and sentences given as explanation of a value."""

    __table_args__ = (UniqueConstraint('unitvalue_pk', 'sentence_pk'),)

    unitvalue_pk = Column(Integer, ForeignKey('unitvalue.pk'), nullable=False)
    sentence_pk = Column(Integer, ForeignKey('sentence.pk'), nullable=False)
    description = Column(Unicode())

    unitvalue = relationship(UnitValue, innerjoin=True, backref='sentence_assocs')
    sentence = relationship(Sentence, innerjoin=True, backref='unitvalue_assocs', order_by=Sentence.id)

# @implementer(interfaces.IMorpheme)
# class Morpheme(Unit, IdNameDescriptionMixin):
#     pk = Column(Integer, ForeignKey('unit.pk'), primary_key=True)
#     pass
    # pk = Column(Integer, ForeignKey('unit.pk'), primary_key=True)
    
# @implementer(clld.interfaces.IUnitParameter)
# class Meaning(CustomModelMixin, UnitParameter):
#     pk = Column(Integer, ForeignKey('unitparameter.pk'), primary_key=True)