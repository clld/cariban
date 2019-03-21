from clldutils.path import Path
from clld.web.assets import environment

import cariban_morphemes


environment.append_path(
    Path(cariban_morphemes.__file__).parent.joinpath('static').as_posix(),
    url='/cariban_morphemes:static/')
environment.load_path = list(reversed(environment.load_path))
