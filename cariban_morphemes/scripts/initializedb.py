from __future__ import unicode_literals
import sys

from clld.scripts.util import initializedb, Data
from clld.db.meta import DBSession
from clld.db.models import common

from pycldf import Wordlist
from clld.lib.bibtex import EntryType
import cariban_morphemes
from cariban_morphemes import models

from clld_glottologfamily_plugin.util import load_families
import clld_cognacy_plugin

cariban_data = Wordlist.from_metadata("../cariban_data.json")

def main(args):
    data = Data()

    dataset = common.Dataset(id=cariban_morphemes.__name__, domain='cariban_morphemes.clld.org')
    DBSession.add(dataset)
    
    # add languages in the sample to data["Language"]
    for row in cariban_data['LanguageTable']:
        data.add(
            common.Language,
            row['ID'],
            id=row['ID'],
            name=row['Name'],
            latitude=float(row['Latitude']) if row['Latitude'] is not None else None,
            longitude=float(row['Longitude']) if row['Longitude'] is not None else None,
            # glottocode=row['ID'],
        )
    
    #add sources to data["Sources"]
    for src in cariban_data.sources.items():
            for invalid in ['isbn', 'part', 'institution']:
                if invalid in src:
                    del src[invalid]
            data.add(
                common.Source,
                src.id,
                id=src.id,
                name=src.get('author', src.get('editor')),
                description=src.get('title', src.get('booktitle')),
                bibtex_type=getattr(EntryType, src.genre, EntryType.misc),
    **src)
    
    # #trying to add morphemes as units instead of values of parameters
    # for row in cariban_data['FormTable']:
    #     # print("Adding unit {0} with ID {1} for language {2}".format(row['Form'],row['ID'],row['Language_ID']))
    #     data.add(common.Unit,
    #     row['ID'],
    #     language=data['Language'][row['Language_ID']],
    #     name=row['Form'],
    #     id=row['ID']
    #     )
    #     # print("Adding unitparameter {0} with ID {1}".format(row['Parameter_ID'],row['ID']))
    #     data.add(common.UnitParameter,
    #     row['ID'],
    #     id=row['ID'],
    #     name=row['Parameter_ID']
    #     )
    #     # print("Adding unitvalue {0} with ID {1} for unitparameter {2}, unit {3}".format(row['Form'], row['ID'], data['UnitParameter'][row['ID']], data['Unit'][row['ID']]))
    #     data.add(common.UnitValue,
    #     row['ID'],
    #     id=row['ID'],
    #     name=row['Form'],
    #     unit=data['Unit'][row['ID']],
    #     unitparameter=data['UnitParameter'][row['ID']]
    #     )
    #     # print("\n")
        
    
    #adding morphemes as valuesets (with single values) and cognacy sets as parameters; not ideal
    for row in cariban_data['FormTable']:
        if row['Language_ID'] == "cari1283":
            data.add(common.Parameter,row['Cognateset_ID'],name=row['Form'],id=row['Cognateset_ID'])
    
    for row in cariban_data['FormTable']:
        if row['Language_ID'] != "cari1283":
            data.add(common.ValueSet,
                row['ID'],
                id=row['ID'],
                language=data['Language'][row['Language_ID']],
                parameter=data['Parameter'][row['Cognateset_ID']],
            )
            data.add(common.Value,
                row['ID'],
                valueset=data['ValueSet'][row['ID']],
                name=row['Form']
            )
                
    for row in cariban_data['ExampleTable']:
        data.add(common.Sentence,
        row['ID'],
        id=row['ID'],
        name=row['Name'],
        description=row['Translated_Text'],
        analyzed=" ".join(row['Analyzed_Word']),
        gloss=" ".join(row['Gloss']),
        language=data['Language'][row['Language_ID']],
        source=row['Source']
        )
        #see what morphemes this example illustrates; separated by "; "
        if row['Illustrates_Morpheme'].split("; ") != ['']:
            for illustrated in row['Illustrates_Morpheme'].split("; "):
                data.add(common.ValueSentence,
                '{0}-{1}'.format(illustrated,row['ID']),
                sentence=data['Sentence'][row['ID']],
                value=data['Value'][illustrated],
                )
        # if row['Illustrates_Morpheme_Parameter'].split(";") != ['']:
        #     for illustrated in row['Illustrates_Morpheme_Parameter'].split(";"):
        #         data.add(models.UnitValueSentence,
        #         '{0}-{1}'.format(illustrated,row['ID']),
        #         sentence=data['Sentence'][row['ID']],
        #         unitvalue=data['UnitValue'][illustrated],
        #         )
        
                    
def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodiucally whenever data has been updated.
    """

# main("hihi")
if __name__ == '__main__':  # pragma: no cover
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)
