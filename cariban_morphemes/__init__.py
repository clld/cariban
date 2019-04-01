from pyramid.config import Configurator

# we must make sure custom models are known at database initialization!
# from cariban_morphemes.models import Morpheme
# from cariban_morphemes.interfaces import IMorpheme
from cariban_morphemes import models

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('clld.web.app')
    # config.register_resource(
    #     'morpheme', Morpheme, IMorpheme, with_index=True)
    return config.make_wsgi_app()