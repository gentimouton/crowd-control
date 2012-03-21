from pygame.sprite import DirtySprite, LayeredDirty
import logging


log = logging.getLogger('client')


class IndexableSprite(DirtySprite):
    """ Sprite that can be fetched from a RenderUpdatesDict"""
    def __init__(self, key, *groups):
        self.key = key # Sprite init calls the group's add_internal
        DirtySprite.__init__(self, *groups)
        
    def __str__(self):
        return str(self.key)
    
    
class RenderUpdatesDict(LayeredDirty):
    """ Group class that extends RenderUpdates to enable associating a spr 
    to a user name """
     
    def __init__(self, *sprites):
        LayeredDirty.__init__(self, *sprites)
        self.__dict = dict() 

    def __str__(self):
        return '%d items' % len(self.__dict)
        
    def add_internal(self, spr, layer=0):
        """ add sprite to the group,
        and index it if it's an IndexableSprite """
        LayeredDirty.add_internal(self, spr, layer)
        if isinstance(spr, IndexableSprite):
            self.__dict[spr.key] = spr
            
    def get_spr(self, key):
        try:
            return self.__dict[key]
        except KeyError:
            log.warn('Could not find sprite %s' % key)
            return None
