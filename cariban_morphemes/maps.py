from clld.web.maps import Map

class LanguoidsMap(Map):
    def get_options(self):
        return {'show_labels': True, 'max_zoom': 10}

def includeme(config):
    config.register_map('languages', LanguoidsMap)