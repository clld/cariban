from pyramid.config import Configurator
from clld.web.app import menu_item
from functools import partial

# we must make sure custom models are known at database initialization!
# from cariban_morphemes.models import Morpheme
# from cariban_morphemes.interfaces import IMorpheme
from cariban_morphemes import models
from cariban_morphemes.interfaces import IConstruction

_ = lambda s: s
_('Parameter')
_('Parameters')
_('Unit')
_('Units')
_('Unitparameter')
_('Unitparameters')

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['route_patterns'] = {
        'unitparameters': '/functions',
        'unitparameter': '/function/{id:[^/\.]+}',
        'units': '/morphemes',
        'unit': '/morpheme/{id:[^/\.]+}',
        'construction': '/construction/{id:[^/\.]+}',
        'parameters': '/cognatesets',
        'parameter': '/cognateset/{id:[^/\.]+}',
    }

    config = Configurator(settings=settings)
    config.include('clld.web.app')
    config.register_resource(
        'construction', models.Construction, IConstruction, with_index=True, with_detail=True)
    return config.make_wsgi_app()