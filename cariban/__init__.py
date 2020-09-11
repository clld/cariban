from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound

from cariban import models
from cariban import views
from cariban.interfaces import IConstruction, IDeclarativeType, IMainClauseVerb, IPage, ITVerb, ICognateset, ICognate

_ = lambda s: s
_('Unitparameter')
_('Unitparameters')
_('Sentence')
_('Sentences')
_('Phylogenys')
_('Unit')
_('Units')


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
        'cognateset': '/cognateset/{id:[^/\.]+}',
        'phylogenys': '/phylogenies',
        'phylogeny': '/phylogeny/{id:[^/\.]+}',
    }
    
    settings["clld.github_repos"] = "clld/cariban"

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
