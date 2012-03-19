from pygame.sprite import Sprite, RenderUpdates
import logging


log = logging.getLogger('client')


class IndexableSprite(Sprite):
    """ Sprite that can be fetched from a RenderUpdatesDict"""
    def __init__(self, key=None):
        Sprite.__init__(self)
        self.key = key
        
    def __str__(self):
        return str(self.key)
    
    
class RenderUpdatesDict(RenderUpdates):
    """ Group class that extends RenderUpdates to enable associating a spr 
    to a user name """
     
    def __init__(self, *sprites):
        RenderUpdates.__init__(self, *sprites)
        self.__dict = dict() 

    def __str__(self):
        return '%d items' % len(self.__dict)
        
    def add_internal(self, spr):
        """ add sprite to the group,
        and index it if it's an IndexableSprite """
        RenderUpdates.add_internal(self, spr)
        if isinstance(spr, IndexableSprite):
            self.__dict[spr.key] = spr
            
    def get_spr(self, key):
        try:
            return self.__dict[key]
        except KeyError:
            log.warn('Could not find sprite %s' % key)
            return None