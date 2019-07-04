from pyramid.config import Configurator
from pyramid.response import Response
from clld.web.app import menu_item
from functools import partial
from pyramid.httpexceptions import HTTPFound

# we must make sure custom models are known at database initialization!
# from cariban_morphemes.models import Morpheme
# from cariban_morphemes.interfaces import IMorpheme
from cariban_morphemes import models
from cariban_morphemes.interfaces import IConstruction, IDeclarativeType, IMainClauseVerb, IPage, ITVerb, ICognateset, ICognate
from clld.interfaces import IUnit

_ = lambda s: s
_('Unitparameter')
_('Unitparameters')
_('Sentence')
_('Sentences')
_('Phylogenys')

def notfound(request):
    raise HTTPFound(location='/')
    
def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['route_patterns'] = {
        'unitparameters': '/functions',
        'unitparameter': '/function/{id:[^/\.]+}',
        'units': '/morphemes',
        'unit': '/morpheme/{id:[^/\.]+}',
        'construction': '/construction/{id:[^/\.]+}',
        'sentences': '/examples',
        'sentence': '/example/{id:[^/\.]+}',
        'phylogenys': '/phylogenies',
        'phylogeny': '/phylogeny/{id:[^/\.]+}',
    }
    
    settings["clld.github_repos"] = "florianmatter/cariban_morphemes"

    config = Configurator(settings=settings)
    config.include('clld.web.app')
    config.include('clld_phylogeny_plugin')
    config.register_resource(
            'cognateset', models.Cognateset, ICognateset, with_index=True, with_detail=True)
    config.register_resource(
            'cognate', models.Cognate, ICognate, with_index=True)
    # config.register_resource(
#         'morpheme', models.Morpheme, IUnit, with_index=True, with_detail=True)
#     config.register_resource(
#         'tverb', models.TVerb, ITVerb, with_index=True, with_detail=True)
    config.register_resource(
        'construction', models.Construction, IConstruction, with_index=True, with_detail=True)
    config.register_resource(
        'page', models.Page, IPage, with_index=True, with_detail=True)
    config.register_resource(
        'declarativetype', models.DeclarativeType, IDeclarativeType, with_detail=True)
    config.register_resource(
        'mainclauseverb', models.MainClauseVerb, IMainClauseVerb, with_detail=True)
    config.add_route_and_view(
        '1+3',
        '/1+3',
        views.firstexcl,
        renderer='pages/1+3.mako')
    config.add_notfound_view(notfound)
    return config.make_wsgi_app()