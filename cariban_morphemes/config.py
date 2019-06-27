import json

#This will contain a dict to look up full language names based on shorthand forms (e.g. maqui). This is only used to render markdown.
with open('lang_abbrev_dic.json') as json_file:
    LANG_ABBREV_DIC = json.load(json_file)

FUNCTION_PARADIGMS = []
with open('function_paradigms.json') as json_file:
    FUNCTION_PARADIGMS = json.load(json_file)
    
with open('lang_code_dic.json') as json_file:
    LANG_CODE_DIC = json.load(json_file)