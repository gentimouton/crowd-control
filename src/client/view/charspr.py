from client.view.indexablespr import IndexableSprite
from common.constants import DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, \
    DIRECTION_RIGHT
from pygame import Rect
from pygame.sprite import Sprite
import pygame
from pygame.font import Font





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
        green = (0, 255, 0)
        greenrect = Rect(self.w / 10, self.h / 10,
                         4 * self.char.hp, self.h / 10 + 5)
        self.image.fill(green, greenrect)
        # TODO: add a red bar too
        # TODO: rotate the display based on charactor's facing
        
            
        
                
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
    
    
    def __init__(self, txt, duration, centerpos, scroll_height, color, groups=None):
        """ start displaying the dmg at the given rect, 
        and for the given duration 
        """
        
        Sprite.__init__(self, groups)

        self.txt = txt
        self.font = Font(None, 30) #default font, 30 pixels high # TODO: from config file
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
            self.rect.move_ip(0, - shift) # shift upwards
        
        
        
