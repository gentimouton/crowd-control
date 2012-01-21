from client2.events import CharactorMoveEvent, ModelBuiltMapEvent, TickEvent, \
    CharactorPlaceEvent, QuitEvent, SendChatEvent, NetworkReceivedCharactorMoveEvent, \
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

    
    def show_map(self, gmap):
        """ blit the map on the screen.
        The pixel width and height of map cells is supposed to be constant.
        The map is always centered on the avatar (unless when avatar is near
        edges) and scrolls to follow the movement of the player's avatar.
        """
        
        # clear the screen first
        self.background.fill((11, 11, 0))
        self.window.blit(self.background, (0, 0))
        pygame.display.flip() 
        
        # iterate over cell rows and columns
        for i in range(gmap.width):
            for j in range(gmap.height):
                # TODO: distinguish between entrance and lair and normal cells
                cellrect = Rect(i * 100, j * 100, 99, 99)
                cellspr = CellSprite(gmap.get_cell(j, i), self.backSprites)
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
        
        if isinstance(event, TickEvent):
            self.render_dirty_sprites()

        elif isinstance(event, ModelBuiltMapEvent):
            gameMap = event.map
            self.show_map(gameMap)
            
        elif isinstance(event, CharactorPlaceEvent):
            self.add_charactor(event.charactor)
            
        elif isinstance(event, CharactorRemoveEvent):
            charactor = event.charactor
            self.remove_charactor(charactor)

            
        elif isinstance(event, CharactorMoveEvent):
            self.move_charactor(event.charactor)
            #coords = event.coords

        elif isinstance(event, NetworkReceivedCharactorMoveEvent):
            #self.move_charactor(event.charactor)
            print('should move ', event.author, 'to', event.dest)



###########################################################################


class CellSprite(Sprite):
    """ The representation of a map cell """
    def __init__(self, cell, group=None):
        Sprite.__init__(self, group)
        self.image = pygame.Surface((99, 99))
        self.image.fill((139, 119, 101))
        
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



            
            
