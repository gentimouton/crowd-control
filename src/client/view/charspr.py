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
    
    dmg_color = (0, 0, 0) # black # TODO: from config file


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
        
        self.font = Font(None, 30) #default font, 30 pixels high # TODO: from config file
        self.dmg_duration = 30 # in frames; TODO: hardcoded, and should be in millis 
        self.dmg_timer = 0 # when 0, stop displaying 
        # TODO: should be a list of (dmg, timer); 
        # TODO: when the list is empty, it means dmg_displaying is False (no need for that boolean anymore)
        self.dmg_rcved = None # store the number to display
        self.dmg_displaying = False # not currently displaying dmg
        # TODO: should allow multiple damages to be displayed at the same time
        # TODO: dmg should scroll upwards then disappear 
        
            
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
        
        # eventually display dmg
        if self.dmg_displaying:
            txt = str(self.dmg_rcved)
            txtimg = self.font.render(txt, True, self.dmg_color)
            centerpos = self.image.get_width() / 2, 5 # centered horizontally, 5 px from top
            txtpos = txtimg.get_rect(center = centerpos)
            self.image.blit(txtimg, txtpos)
            
        
         
    def start_displaying_dmg(self, dmg):
        """ start the timer displaying dmg on top of the charactor.
        Will stop by itself after the timer is over.
        TODO: Can only display ONE dmg at a time. 
        """
        self.dmg_rcved = dmg
        self.dmg_displaying = True
        self.dmg_timer = self.dmg_duration
        
                
    def update(self):
        """ Eventually move the spr and update its orientation.
        movement could be smoother and last for longer than 1 frame.
        This is called by the view every frame.
        """
        
        if self.dmg_displaying: # still has to display dmg
            self.dmg_timer -= 1 # reduce by 1 every frame

            if self.dmg_timer <= 0: # done displaying
                self.dmg_displaying = False
                self.dmg_rcved = None # just in case
                sprleft, sprtop = self.rect.center
                self.update_img(sprleft, sprtop)
                
        

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



