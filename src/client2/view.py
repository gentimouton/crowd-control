from client2.events_client import CharactorMoveEvent, ModelBuiltMapEvent, \
    ClientTickEvent, CharactorPlaceEvent, QuitEvent, SendChatEvent, \
    CharactorRemoveEvent
from client2.widgets import ButtonWidget, InputFieldWidget, ChatLogWidget
from pygame.rect import Rect
from pygame.sprite import RenderUpdates, Sprite
import pygame


class IndexableSprite(Sprite):
    """ Sprite that can be fetched from a RenderUpdatesDict"""
    def __init__(self, key=None):
        Sprite.__init__(self)
        self.key = key
    
class RenderUpdatesDict(RenderUpdates):
    """ Group class that extends RenderUpdates to enable associating a spr 
    to a user name """
     
    def __init__(self, *sprites):
        RenderUpdates.__init__(self, *sprites)
        self.__dict = dict() 

    def add_internal(self, spr):
        """ add sprite to the group,
        and index it if it's an IndexableSprite """
        RenderUpdates.add_internal(self, spr)
        if isinstance(spr, IndexableSprite):
            self.__dict[spr.key] = spr
            
    def get_spr(self, key):
        return self.__dict[key]

        
###########################################################################

class MasterView:
    """ links to presentations of game world and HUD """
    
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        pygame.init() #calling init() multiple times does not mess anything
        self.window = pygame.display.set_mode((300, 380))
        pygame.display.set_caption('CC')
        
        self.background = pygame.Surface(self.window.get_size())
        self.background.fill((0, 0, 0)) #black
        self.window.blit(self.background, (0, 0))
     
        
        # add quit button and meh_btn at bottom-right 
        rect = Rect((231, 341), (69, 39)) 
        quitEvent = QuitEvent()
        quit_btn = ButtonWidget(evManager, "Quit", rect=rect,
                             onUpClickEvent=quitEvent)
        
        rect = Rect((231, 301), (69, 39)) 
        msgEvent = SendChatEvent('meh...') #ask to send 'meh' to the server
        meh_btn = ButtonWidget(evManager, "Meh.", rect=rect,
                                   onUpClickEvent=msgEvent)
        
        
        # chat box input
        rect = Rect((0, 361), (230, 19)) #bottom and bottom-left of the screen
        chatbox = InputFieldWidget(evManager, rect=rect)

        # chat window display
        rect = Rect((0, 301), (230, 60)) # just above the chat input field
        chatwindow = ChatLogWidget(evManager, numlines=3, rect=rect)
        
        pygame.display.flip()

        self.backSprites = RenderUpdates() # TODO: this should actually be the BG
        self.charactorSprites = RenderUpdatesDict()
        self.gui_sprites = RenderUpdates()   
        self.gui_sprites.add(quit_btn)
        self.gui_sprites.add(meh_btn)
        self.gui_sprites.add(chatbox)
        self.gui_sprites.add(chatwindow)

    
    def show_map(self, worldmap):
        """ blit the map on the screen.
        The pixel width and height of map cells is supposed to be constant.
        The map is always centered on the avatar (unless when avatar is near
        edges) and scrolls to follow the movement of the player's avatar.
        """
        
        # clear the screen first
        self.background.fill((0, 0, 0))
        self.window.blit(self.background, (0, 0))
        pygame.display.flip() 
        
        # iterate over cell rows and columns
        for i in range(worldmap.height):
            for j in range(worldmap.width):
                # TODO: distinguish between entrance and lair and normal cells
                cellrect = Rect(j * 100, i * 100, 99, 99)
                cell = worldmap.get_cell(i, j)
                
                cellspr = CellSprite(cell, self.backSprites)
                cellspr.rect = cellrect
                # cellspr = None # that was in shandy's code ... why?

    
    def add_charactor(self, charactor):
        """ Make a sprite and center the sprite based on cell location. """
        charactorSprite = CharactorSprite(charactor, self.charactorSprites)
        # center in middle of cell
        cell = charactor.cell
        cell_spr = self.get_cell_sprite(cell)
        charactorSprite.rect.center = cell_spr.rect.center

    def remove_charactor(self, charactor):
        char_spr = self.charactorSprites.get_spr(charactor)
        char_spr.kill() # remove from all sprite groups
        del char_spr
    
    def move_charactor(self, charactor):
        charactorSprite = self.charactorSprites.get_spr(charactor)
        cell_spr = self.get_cell_sprite(charactor.cell)
        charactorSprite.dest = cell_spr.rect.center

        
    
    def get_cell_sprite(self, cell):
        for s in self.backSprites:
            if isinstance(s, CellSprite) and s.cell == cell:
                return s


    def render_dirty_sprites(self):    
        # clear the window from all the sprites, replacing them with the bg
        self.backSprites.clear(self.window, self.background)
        self.charactorSprites.clear(self.window, self.background)
        self.gui_sprites.clear(self.window, self.background)
        
        # update all the sprites - calls update() on each sprite of the groups
        self.backSprites.update()
        self.charactorSprites.update()
        self.gui_sprites.update()
        
        # collect the display areas that have changed
        dirtyRectsB = self.backSprites.draw(self.window)
        dirtyRectsF = self.charactorSprites.draw(self.window)
        dirtyRectsG = self.gui_sprites.draw(self.window)
        
        # and redisplay those areas only
        dirtyRects = dirtyRectsB + dirtyRectsF + dirtyRectsG
        pygame.display.update(dirtyRects)



    def notify(self, event):
        """ Display the map when it has been built by the model.
        At clock ticks, draw what needs to be drawn.
        When the game is loaded, display it. 
        """
        
        if isinstance(event, ClientTickEvent):
            self.render_dirty_sprites()

        elif isinstance(event, ModelBuiltMapEvent):
            worldmap = event.worldmap
            self.show_map(worldmap)
            
        elif isinstance(event, CharactorPlaceEvent):
            self.add_charactor(event.charactor)
            
        elif isinstance(event, CharactorRemoveEvent):
            charactor = event.charactor
            self.remove_charactor(charactor)

            
        elif isinstance(event, CharactorMoveEvent):
            self.move_charactor(event.charactor)
            #coords = event.coords




###########################################################################


class CellSprite(Sprite):
    """ The representation of a map cell """
    
    dims = width, height = 99, 99 # in pixels
    # rgb cell colors
    walkable_cell_color = 139, 119, 101 
    nonwalkable_cell_color = 0, 0, 0 
    entrance_cell_color = 139, 0, 101 
    lair_cell_color = 139, 119, 0 
    
    
    def __init__(self, cell, group=None):
        Sprite.__init__(self, group)

        # self.image filled with a color
        self.image = pygame.Surface(self.dims)
        if hasattr(cell, 'isentrance') and cell.isentrance:
            color = self.entrance_cell_color
        elif hasattr(cell, 'islair') and cell.islair:
            color = self.lair_cell_color
        elif cell.iswalkable:
            color = self.walkable_cell_color
        else: # non-walkable
            color = self.nonwalkable_cell_color
        self.image.fill(color) 

        self.cell = cell

        


###########################################################################



class CharactorSprite(IndexableSprite):
    """ The representation of a character """
    
    def __init__(self, charactor, groups=None):
        self.key = charactor # must be set before adding the spr to group(s)
        Sprite.__init__(self, groups)
        
        charactorSurf = pygame.Surface((64, 64))
        charactorSurf = charactorSurf.convert_alpha()
        charactorSurf.fill((0, 0, 0, 0)) #make transparent
        pygame.draw.circle(charactorSurf, (255, 140, 0), (32, 32), 32)
        self.image = charactorSurf
        self.rect = charactorSurf.get_rect()

        self.charactor = charactor
        self.dest = None

    
    def update(self):
        """ TODO: movement could be smoother and last for longer than 1 frame """
        if self.dest:
            self.rect.center = self.dest
            self.dest = None



            
            
