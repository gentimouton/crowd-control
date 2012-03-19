from client.view.indexablespr import IndexableSprite
from common.constants import DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, \
    DIRECTION_RIGHT
from pygame import Rect
from pygame.sprite import Sprite
import pygame




class CharactorSprite(IndexableSprite):
    """ The representation of a Charactor. """
    
    facing_sprites = {}
    
    def __init__(self, char, sprdims, bgcolor, groups=None):
        self.key = char # must be set before adding the spr to group(s)
        Sprite.__init__(self, groups)
        
        self.char = char

        # build the various sprite orientations
        self.w, self.h = sprdims
        if not self.facing_sprites: # TODO: FT make this cleaner
            self.facing_sprites = build_facingsprites(bgcolor, self.w, self.h) 
        
        # no need to build the img yet: 
        # it will happen when view calls update_img
        # this rect will be updated in update_img
        self.rect = Rect(0, 0, self.w, self.h) 
        
        
    def update_img(self, charleft, chartop):
        """ update the image from the model.
        Position the spr as told by the view. 
        Unlike update, this is only called when the model changed. """
        
        charsurfbg = self.facing_sprites[self.char.facing]
        
        # add a 5-px thick hp bar, 4px per HP left
        # make a copy when char created, moved, or rcv_dmg
        self.image = charsurfbg.copy()
        green = (0, 255, 0)
        greenrect = Rect(self.w / 10, self.h / 10,
                         4 * self.char.hp, self.h / 10 + 5)
        self.image.fill(green, greenrect)
        self.rect.center = charleft, chartop
        
            
    def update(self):
        """ Eventually move the spr and update its orientation.
        movement could be smoother and last for longer than 1 frame.
        """
        
        #charsurf = self.facing_sprites[self.char.facing]
        #self.image = charsurf
        
        

###############  sprite builders

def build_facingsprites(bgcolor, w, h):
    """ Given width and height of the cell,
    return a dict {DIRECTION_XXX: sprite for that direction} 
    """
    
    facing_sprites = {}
    dirs = [DIRECTION_UP, DIRECTION_DOWN, DIRECTION_RIGHT, DIRECTION_LEFT]
    
    for d in dirs:
        spr = pygame.Surface((w, h))
        spr = spr.convert_alpha()
        spr.fill((0, 0, 0, 0)) #make transparent
        # triangular shape to show char.facing
        vertices = get_vertices(d, w, h)
        pygame.draw.polygon(spr, bgcolor, vertices)
        
        facing_sprites[d] = spr
        
    return facing_sprites

    
def get_vertices(facing, w, h):
    """ Get a list of triangle vertices from the character's facing
    and the width and height of the cell. 
    """
    
    vert = []
    
    if facing == DIRECTION_UP:
        vert = [(0, h), (w, h), (int(w / 2), 0)]
    elif facing == DIRECTION_DOWN:
        vert = [(0, 0), (w, 0), (int(w / 2), h)]
    elif facing == DIRECTION_LEFT:
        vert = [(w, 0), (w, h), (0, int(h / 2))]
    elif facing == DIRECTION_RIGHT:
        vert = [(0, 0), (0, h), (w, int(h / 2))]
    
    return vert



