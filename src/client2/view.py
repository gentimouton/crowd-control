from client2.events_client import CharactorMoveEvent, ModelBuiltMapEvent, \
    ClientTickEvent, CharactorPlaceEvent, QuitEvent, SendChatEvent, \
    CharactorRemoveEvent
from client2.widgets import ButtonWidget, InputFieldWidget, ChatLogWidget
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
        rect = pygame.Rect((231, 341), (69, 39)) 
        quitEvent = QuitEvent()
        quit_btn = ButtonWidget(evManager, "Quit", rect=rect,
                             onUpClickEvent=quitEvent)
        
        rect = pygame.Rect((231, 301), (69, 39)) 
        msgEvent = SendChatEvent('meh...') #ask to send 'meh' to the server
        meh_btn = ButtonWidget(evManager, "Meh.", rect=rect,
                                   onUpClickEvent=msgEvent)
        
        
        # chat box input
        rect = pygame.Rect((0, 361), (230, 19)) #bottom and bottom-left of the screen
        chatbox = InputFieldWidget(evManager, rect=rect)

        # chat window display
        rect = pygame.Rect((0, 301), (230, 60)) # just above the chat input field
        chatwindow = ChatLogWidget(evManager, numlines=3, rect=rect)
        
        pygame.display.flip()

        self.charactorSprites = RenderUpdatesDict()
        self.gui_sprites = RenderUpdates()   
        self.gui_sprites.add(quit_btn)
        self.gui_sprites.add(meh_btn)
        self.gui_sprites.add(chatbox)
        self.gui_sprites.add(chatwindow)

    
    def show_map(self, worldmap):
        """ Build the bg from the map cells, and blit it.
        The pixel width and height of map cells is supposed to be constant.
        
        TODO: 
        The map is always centered on the avatar (unless when avatar is near
        edges) and scrolls to follow the movement of the player's avatar.
        """
        
        self.cellsprs = dict() # maps model.Cell to view.CellSprite
        
        # make bg: iterate over cell rows and columns
        for i in range(worldmap.width):
            for j in range(worldmap.height):
                cellrect = pygame.Rect(i * 100, j * 100, 99, 99)
                cell = worldmap.get_cell(i, j)
                cellspr = CellSprite(cell, cellrect)
                self.cellsprs[cell] = cellspr
                
                self.background.blit(cellspr.image, cellspr.rect)
        
        # display the bg
        self.window.blit(self.background, (0, 0))
        pygame.display.flip() 
        
    
    def add_charactor(self, charactor):
        """ Make a sprite and center the sprite 
        based on the cell location of the charactor.
        """
        charspr = CharactorSprite(charactor, self.charactorSprites)
        # center in middle of cell
        cell_spr = self.get_cell_sprite(charactor.cell)
        charspr.rect.center = cell_spr.rect.center


    def remove_charactor(self, charactor):
        char_spr = self.charactorSprites.get_spr(charactor)
        char_spr.kill() # remove from all sprite groups
        del char_spr
    
    def move_charactor(self, charactor):
        # TODO: surface.scroll the bg instead of moving the charactor
        charactorSprite = self.charactorSprites.get_spr(charactor)
        cell_spr = self.get_cell_sprite(charactor.cell)
        charactorSprite.dest = cell_spr.rect.center
        

        
    
    def get_cell_sprite(self, cell):
        try:
            return self.cellsprs[cell]
        except KeyError:
            print('Cell', cell, 'not found in the cell dict of the view.')  



    def render_dirty_sprites(self):    
        # clear the window from all the sprites, replacing them with the bg
        #self.backSprites.clear(self.window, self.background)
        self.charactorSprites.clear(self.window, self.background)
        self.gui_sprites.clear(self.window, self.background)
        
        # update all the sprites - calls update() on each sprite of the groups
        self.charactorSprites.update()
        self.gui_sprites.update()
        
        # collect the display areas that have changed
        dirtyRectsF = self.charactorSprites.draw(self.window)
        dirtyRectsG = self.gui_sprites.draw(self.window)
        
        # and redisplay those areas only
        dirtyRects = dirtyRectsF + dirtyRectsG
        pygame.display.update(dirtyRects)



    def notify(self, event):
        """ Display the map when it has been built by the model.
        At clock ticks, draw what needs to be drawn.
        When the game is loaded, display it. 
        """
        
        if isinstance(event, ClientTickEvent):
            self.render_dirty_sprites()

        elif isinstance(event, ModelBuiltMapEvent):
            # called only once at the beginning, when model.map has been built 
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
    """ The representation of a map cell. 
    Used to draw the map background.
     """
    
    dims = width, height = 99, 99 # in pixels
    # rgb cell colors
    walkable_cell_color = 139, 119, 101 
    nonwalkable_cell_color = 0, 0, 0 
    entrance_cell_color = 139, 0, 101 
    lair_cell_color = 139, 119, 0 
    
    
    def __init__(self, cell, rect, group=()):
        Sprite.__init__(self, group)

        # fill self.image filled with the appropriate color
        self.image = pygame.Surface(self.dims)
        if cell.isentrance:
            color = self.entrance_cell_color
        elif cell.islair:
            color = self.lair_cell_color
        elif cell.iswalkable:
            color = self.walkable_cell_color
        else: # non-walkable
            color = self.nonwalkable_cell_color
        self.image.fill(color) 
        self.rect = rect
        
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
        """ movement could be smoother and last for longer than 1 frame """
        if self.dest:
            self.rect.center = self.dest
            self.dest = None



            
            
