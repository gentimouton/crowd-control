from client.config import config_get_scrollfontcolor, config_get_scrollfontsize, \
    config_get_hpbarfullcolor
from client.view.indexablespr import IndexableSprite
from common.constants import DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, \
    DIRECTION_RIGHT
from pygame import Rect
from pygame.font import Font
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
                
            
    def update_img(self, sprleft, sprtop):
        """ update the image from the model.
        Position the spr as told by the view. 
        This is called when the model changed,
        or when dmg have to be displayed. 
        """
        
        self.rect.center = sprleft, sprtop
        
        # place the oriented av spr
        charsurfbg = self.facing_sprites[self.char.facing]
        self.image = charsurfbg.copy()
        
        # add a 5-px thick hp bar, 4px per HP left
        # make a copy when char created, moved, or rcv_dmg
        color = config_get_hpbarfullcolor()
        if self.char.facing == DIRECTION_LEFT: # vertical, right side
            hpfullrect = Rect(self.w * 10 / 12, self.h / 8,
                              self.w / 12, 4 * self.char.hp)
        if self.char.facing == DIRECTION_RIGHT:# vertical, left side
            hpfullrect = Rect(self.w * 1 / 12, self.h / 8,
                              self.w / 12, 4 * self.char.hp)
        if self.char.facing == DIRECTION_UP:# horizontal
            hpfullrect = Rect(self.w / 8, self.h * 10 / 12,
                              4 * self.char.hp, self.h / 12)
        if self.char.facing == DIRECTION_DOWN:# horizontal
            hpfullrect = Rect(self.w / 8, self.h * 1 / 12,
                              4 * self.char.hp, self.h / 12)            
        
        self.image.fill(color, hpfullrect)
        # TODO: add a red bar too from config_get_hpbaremptycolor()
        # TODO: for vertical hp bars, green is at the top of red, whereas it should be at the bottom
        # TODO: add maxhp to the model, and display in % of HP instead of absolute number of HP
        
        
                
    def update(self, duration):
        """ This is called by the view every frame. """
        pass
                
        

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




#########################################################################


class ScrollingTextSprite(Sprite):
    """ A sprite making text scroll upwards and disappear after a while. """
    
    
    def __init__(self, txt, duration, centerpos, scroll_height, groups=None):
        """ start displaying the dmg at the given rect, 
        and for the given duration 
        """
        
        Sprite.__init__(self, groups)

        self.txt = txt
        fontsize = config_get_scrollfontsize()
        self.font = Font(None, fontsize) #default font
        color = config_get_scrollfontcolor()
        self.image = self.font.render(txt, True, color)
        self.rect = self.image.get_rect(center=centerpos) # center the rect
        
        self.timer = duration
        self.shiftspeed = scroll_height / duration # float, in pixels per millis
        
    
    def __str__(self):
        return '%s at %s - leaves in %dms' % (self.txt, self.rect, self.timer)
            
            
    def update(self, frame_dur):
        """ Update the position of the text:
        - scroll upwards as time goes by, 
        - follow the charactor that received the dmg
        - if the char dies, stop following
        frame_dur = how long it took between 2 ticks
        """
        
        if self.timer <= 0:
            self.kill()
            del self
        else:
            self.timer -= frame_dur
            shift = self.shiftspeed * frame_dur  
            self.rect.move_ip(0, -shift) # shift upwards
        
        
        
