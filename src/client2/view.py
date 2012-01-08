from client2.events import CharactorMoveEvent, MapBuiltEvent, TickEvent, \
    CharactorPlaceEvent, QuitEvent
from client2.widgets import ButtonWidget
from pygame.locals import *
from pygame.sprite import RenderUpdates
import pygame




class MasterView:
    """ links to presentations of game world and HUD """
    
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        pygame.init() #calling this multiple times has no effect
        self.window = pygame.display.set_mode((300, 350))
        pygame.display.set_caption('CC')
        
        self.background = pygame.Surface(self.window.get_size())
        self.background.fill((0, 0, 0)) #black
        self.window.blit(self.background, (0, 0))
        
        # add quit button at bottom 
        rect = pygame.Rect((151, 301), (99, 49)) #bottom-right of the screen
        self.gui_sprites = RenderUpdates()
        quitEvent = QuitEvent()
        bquit = ButtonWidget(evManager, "Quit", rect=rect,
                             onUpClickEvent=quitEvent)
        
        pygame.display.flip()

        self.backSprites = pygame.sprite.RenderUpdates()
        self.frontSprites = pygame.sprite.RenderUpdates()
        self.backSprites.add(bquit)

    
    def show_map(self, gameMap):
        # clear the screen first
        self.background.fill((11, 11, 0))
        self.window.blit(self.background, (0, 0))
        pygame.display.flip()

        # use this squareRect as a cursor and go through the
        # columns and rows and assign the rect 
        # positions of the SectorSprites
        squareRect = pygame.Rect((-99, 1, 100, 100))

        column = 0
        for sector in gameMap.sectors:
            if column < 3:
                squareRect = squareRect.move(100, 0)
            else:
                column = 0
                squareRect = squareRect.move(-(100 * 2), 100)
            column += 1
            newSprite = CellSprite(sector, self.backSprites)
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
            if isinstance(s, CellSprite) and s.sector == sector:
                return s


    
    def notify(self, event):
        if isinstance(event, TickEvent):
            #Draw Everything
            self.backSprites.clear(self.window, self.background)
            self.frontSprites.clear(self.window, self.background)

            self.backSprites.update()
            self.frontSprites.update()

            dirtyRects1 = self.backSprites.draw(self.window)
            dirtyRects2 = self.frontSprites.draw(self.window)
            
            dirtyRects = dirtyRects1 + dirtyRects2
            pygame.display.update(dirtyRects)


        elif isinstance(event, MapBuiltEvent):
            gameMap = event.map
            self.show_map(gameMap)

        elif isinstance(event, CharactorPlaceEvent):
            self.show_charactor(event.charactor)

        elif isinstance(event, CharactorMoveEvent):
            self.move_charactor(event.charactor)






class CellSprite(pygame.sprite.Sprite):
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



            
            
