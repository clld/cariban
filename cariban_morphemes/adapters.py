from zope.interface import implementer
from clld_phylogeny_plugin.interfaces import ITree
from clld_phylogeny_plugin.tree import Tree

@implementer(ITree)
class CaribanTree(Tree):
    def get_marker(self, valueset):
        print(valueset)
        return "1", "blue"
        
    def render(self):
        print("HIIII MOM")
        return Markup(render(
            self.__template__, {'obj': self}, request=getattr(self, 'req', None)))

def includeme(config):
    # config.registry.registerUtility(CaribanTree, ITree)
    pass
