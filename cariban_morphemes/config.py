from pycldf import Wordlist, Generic
cariban_data = Wordlist.from_metadata("../cariban_morpheme_data.json")
construction_data = Generic.from_metadata("../cariban_construction_data.json")
#This will contain a dict to look up the language IDs (and names) based on glottocodes -- the CLLD app uses custom language IDs, but the CLDF files use glottocodes.
LANG_DIC = {}
#This will contain a dict to look up full language names based on shorthand forms (e.g. maqui). This is only used to render markdown.
LANG_ABBREV_DIC = {}
for row in cariban_data["LanguageTable"]:
    if row["sampled"] == "y":
        LANG_DIC[row["glottocode"]] = {"ID": row["ID"], "name": row["Name"]}
        LANG_ABBREV_DIC[row["shorthand"]] = {"ID": row["ID"], "name": row["Name"]}
        
#Create shorthand lists for the paradigm generator function
FUNCTION_PARADIGMS = []
for entry in construction_data["ValueTable"]:
    for function in entry["Function"]:
        for construction in entry["Construction"]:
            function_entry = {
                "Function": function,
                "Construction": construction,
                "Morpheme": entry["Morpheme"]
            }
            FUNCTION_PARADIGMS.append(function_entry)