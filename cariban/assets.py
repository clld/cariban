import pathlib

from clld.web.assets import environment

import cariban


environment.append_path(
    str(pathlib.Path(cariban.__file__).parent.joinpath('static')), url='/cariban:static/')
environment.load_path = list(reversed(environment.load_path))
