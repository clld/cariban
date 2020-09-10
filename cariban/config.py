import pathlib

from clldutils.jsonlib import load

import cariban

REPOS_DIR = pathlib.Path(cariban.__file__).parent.parent

LANG_ABBREV_DIC = load(REPOS_DIR / 'lang_abbrev_dic.json')
FUNCTION_PARADIGMS = load(REPOS_DIR / 'function_paradigms.json')
LANG_CODE_DIC = load(REPOS_DIR / 'lang_code_dic.json')