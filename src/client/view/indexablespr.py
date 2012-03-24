from pygame.sprite import Sprite, LayeredUpdates
import logging


log = logging.getLogger('client')


class IndexableSprite(Sprite):
    """ Sprite that can be fetched from a IndexedLayeredUpdates"""
    def __init__(self, key, layer=None, *groups):
        self.key = key # Sprite init calls the group's add_internal
        self._layer = layer
        Sprite.__init__(self, *groups)
        
    def __str__(self):
        return str(self.key)
    
    
class IndexedLayeredUpdates(LayeredUpdates):
    """ Group class that extends LayeredUpdates to enable associating a spr 
    to a user name """
     
    def __init__(self, *sprites):
        LayeredUpdates.__init__(self, *sprites)
        self.__dict = dict() 

    def __str__(self):
        return '%d items' % len(self)
        
    def add_internal(self, spr, layer=None):
        """ add sprite to the group,
        and index it if it's an IndexableSprite """
        LayeredUpdates.add_internal(self, spr, layer)
        if isinstance(spr, IndexableSprite):
            self.__dict[spr.key] = spr
        else:
            log.warning('Added a non-IndexableSprite to IndexedLayeredUpdates')
    
    def remove_internal(self, spr):
        """ remove a sprite from the group """
        try:
            LayeredUpdates.remove_internal(self, spr)
            key = spr.key
            del self.__dict[key]
        except (KeyError, AttributeError): # spr was not an IndexableSprite
            pass
    
        
    def get_spr(self, key):
        try:
            return self.__dict[key]
        except KeyError:
            log.warn('Could not find sprite %s' % key)
            return None
