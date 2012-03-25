from client.config import config_get_scrollfontcolor, config_get_scrollfontsize, \
    config_get_hpbarfullcolor, config_get_hpbaremptycolor
from client.view.indexablespr import IndexableSprite
from common.constants import DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, \
    DIRECTION_RIGHT
from pygame import Rect
from pygame.font import Font
from pygame.sprite import Sprite
import pygame
from math import log




class CharactorSprite(IndexableSprite):
    """ The representation of a Charactor. """
    

    def __init__(self, char, sprdims, bgcolor, layer=None, *groups):
        
        IndexableSprite.__init__(self, char, layer, *groups)
        
        self.char = char

        # build the various sprite orientations
        self.w, self.h = sprdims
        self.alive_facing_sprites = build_facingsprites(bgcolor, self.w, self.h)
        self.dead_facing_sprites = build_facingsprites((111, 111, 111), self.w, self.h)
        
        # no need to build the img yet: 
        # it will happen when view calls update_img
        # this rect will be updated in update_img
        self.rect = Rect(0, 0, self.w, self.h) 
                
            
    def update_img(self, sprleft, sprtop):
        """ Position the spr as told by the view. 
        This is called when the model changed,
        or when dmg have to be displayed. 
        """

        self.rect.center = sprleft, sprtop
        
        mhp, hp = self.char.maxhp, self.char.hp
        char = self.char
        facing = char.facing
        
        # if alive, place the oriented av spr and add hp bar if alive
        if hp > 0:             
            charsurfbg = self.alive_facing_sprites[facing]
            img = charsurfbg.copy()
            
            # hpbar is updated when char is created, moves, or rcv_dmg
            thickness = max(1, log(mhp)) # logarithmically thicker with more hpmax 
            
            # get 'red' and 'green' bar sizes
            def barsizes(sprsize):
                # sprsize can take values in self.h and self.w
                # e for empty 'red' bar, f for full 'green' bar
                # when horizontal bar, padding of 1/8 of the spr size on the sides, 
                # and padding of 1/12 of the spr size below.     
                totalsize = int(6 / 8 * sprsize) 
                fullsize = int(hp / mhp * 6 / 8 * sprsize)
                #emptysize = (mhp - hp) / mhp * 6 / 8 * sprsize
                emptysize = totalsize - fullsize
                return emptysize, fullsize
            
            myw, myh = self.w, self.h
            if facing == DIRECTION_LEFT: # vertical, right side
                emptysize, fullsize = barsizes(myh)
                erect = Rect(myw * 11 / 12 - thickness, myh / 8,
                             thickness, emptysize)
                frect = Rect(erect.left, erect.bottom, thickness, fullsize)
            elif facing == DIRECTION_RIGHT:# vertical, left side
                emptysize, fullsize = barsizes(myh)
                erect = Rect(myw / 12, myh / 8, thickness, emptysize)
                frect = Rect(erect.left, erect.bottom, thickness, fullsize)
            elif facing == DIRECTION_UP:# horizontal, upwards
                emptysize, fullsize = barsizes(myw)
                frect = Rect(myw / 8, myh * 11 / 12 - thickness,
                             fullsize, thickness)
                erect = Rect(frect.right, frect.top, emptysize, thickness)
            elif facing == DIRECTION_DOWN:# horizontal, downwards
                emptysize, fullsize = barsizes(myw)
                frect = Rect(myw / 8, myh / 12, fullsize, thickness)
                erect = Rect(frect.right, frect.top, emptysize, thickness)
                
            ecolor = config_get_hpbaremptycolor() # red bar
            fcolor = config_get_hpbarfullcolor() # green bar
            img.fill(ecolor, erect)
            img.fill(fcolor, frect)
            self.image = img
        
        else: # display in gray if dead
            charsurfbg = self.dead_facing_sprites[facing]
            self.image = charsurfbg.copy()
        
        
    def update(self, duration):
        """ This is called by the view every frame. 
        If dirty, update the image based on the model.
        if self.dirty == 1, LayeredDirty.draw sets it to 0.  
        """
        pass        
        

###############  sprite builders

def build_facingsprites(bgcolor, w, h):
    """ Given width and height of the cell,
    return a dict {DIRECTION_XXX: sprite for that direction} 
    """
    
    facing_sprites = {}
    dirs = [DIRECTION_UP, DIRECTION_DOWN, DIRECTION_RIGHT, DIRECTION_LEFT]
    
    for d in dirs:
        spr = pygame.Surface((w, h), pygame.SRCALPHA)
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
        
        
        
