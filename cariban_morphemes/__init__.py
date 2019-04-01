from pyramid.config import Configurator

# we must make sure custom models are known at database initialization!
# from cariban_morphemes.models import Morpheme
# from cariban_morphemes.interfaces import IMorpheme
from cariban_morphemes import models

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['route_patterns'] = {
        'unitparameters': '/functions',
        'unitparameter': '/function/{id:[^/\.]+}',
        'units': '/morphemes',
        'unit': '/morpheme/{id:[^/\.]+}',
        'parameters': '/cognatesets',
        'parameter': '/cognateset/{id:[^/\.]+}',

    }
    config = Configurator(settings=settings)
    config.include('clld.web.app')
    return config.make_wsgi_app()