from client2.events import CharactorMoveEvent, ModelBuiltMapEvent, TickEvent, \
    CharactorPlaceEvent, QuitEvent, SendChatEvent
from client2.widgets import ButtonWidget, InputFieldWidget, ChatLogWidget
from pygame.rect import Rect
from pygame.sprite import RenderUpdates
import pygame




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

        self.backSprites = pygame.sprite.RenderUpdates()
        self.frontSprites = pygame.sprite.RenderUpdates()
        self.gui_sprites = RenderUpdates()   
        self.gui_sprites.add(quit_btn)
        self.gui_sprites.add(meh_btn)
        self.gui_sprites.add(chatbox)
        self.gui_sprites.add(chatwindow)

    
    def show_map(self, gameMap):
        # clear the screen first
        self.background.fill((11, 11, 0))
        self.window.blit(self.background, (0, 0))
        pygame.display.flip()

        # use this squareRect as a cursor and go through the
        # columns and rows and assign the rect 
        # positions of the SectorSprites
        squareRect = Rect((-99, 1, 100, 100))

        column = 0
        for sector in gameMap.sectors:
            if column < 3:
                squareRect = squareRect.move(100, 0)
            else:
                column = 0
                squareRect = squareRect.move(-(100 * 2), 100)
            column += 1
            newSprite = SectorSprite(sector, self.backSprites)
            newSprite.rect = squareRect
            newSprite = None

    
    def show_charactor(self, charactor):
        sector = charactor.sector
        charactorSprite = CharactorSprite(self.frontSprites)
        sectorSprite = self.get_sector_sprite(sector)
        charactorSprite.rect.center = sectorSprite.rect.center

    
    def move_charactor(self, charactor):
        charactorSprite = self.get_charactor_sprite(charactor)

        sector = charactor.sector
        sectorSprite = self.get_sector_sprite(sector)

        charactorSprite.moveTo = sectorSprite.rect.center

    
    def get_charactor_sprite(self, charactor):
        #there will be only one
        for s in self.frontSprites:
            return s
        return None

    
    def get_sector_sprite(self, sector):
        for s in self.backSprites:
            if isinstance(s, SectorSprite) and s.sector == sector:
                return s


    def render_dirty_sprites(self):    
        # clear the window from all the sprites, replacing them with the bg
        self.backSprites.clear(self.window, self.background)
        self.frontSprites.clear(self.window, self.background)
        self.gui_sprites.clear(self.window, self.background)
        # update all the sprites - calls update() on each sprite of the groups
        self.backSprites.update()
        self.frontSprites.update()
        self.gui_sprites.update()
        # collect the display areas that have changed
        dirtyRectsB = self.backSprites.draw(self.window)
        dirtyRectsF = self.frontSprites.draw(self.window)
        dirtyRectsG = self.gui_sprites.draw(self.window)
        # and redisplay those areas only
        dirtyRects = dirtyRectsB + dirtyRectsF + dirtyRectsG
        pygame.display.update(dirtyRects)


    def notify(self, event):
        """ At the beginning, display the map.
        At clock ticks, draw what needs to be drawn.
        When the game is loaded, display it. 
        """
        
        if isinstance(event, TickEvent):
            self.render_dirty_sprites()

        elif isinstance(event, ModelBuiltMapEvent):
            gameMap = event.map
            self.show_map(gameMap)
            
        elif isinstance(event, CharactorPlaceEvent):
            self.show_charactor(event.charactor)

        elif isinstance(event, CharactorMoveEvent):
            self.move_charactor(event.charactor)






class SectorSprite(pygame.sprite.Sprite):
    """ The representation of a map cell """
    def __init__(self, sector, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.image = pygame.Surface((99, 99))
        self.image.fill((139, 119, 101))

        self.sector = sector




class CharactorSprite(pygame.sprite.Sprite):
    """ representation of a character """
    
    def __init__(self, group=None):
        pygame.sprite.Sprite.__init__(self, group)

        charactorSurf = pygame.Surface((64, 64))
        charactorSurf = charactorSurf.convert_alpha()
        charactorSurf.fill((0, 0, 0, 0)) #make transparent
        pygame.draw.circle(charactorSurf, (255, 140, 0), (32, 32), 32)
        self.image = charactorSurf
        self.rect = charactorSurf.get_rect()

        self.moveTo = None

    
    def update(self):
        if self.moveTo:
            self.rect.center = self.moveTo
            self.moveTo = None



            
            
