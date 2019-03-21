from pyramid.config import Configurator

# we must make sure custom models are known at database initialization!
from cariban_morphemes import models


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('clld.web.app')
    return config.make_wsgi_app()
