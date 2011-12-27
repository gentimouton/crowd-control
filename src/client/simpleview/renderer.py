from client.config import config_get_screencaption, config_get_screenwidth, \
    config_get_screenheight
from client.simpleview.hudbtn import AbstractHudBtn
import pygame.sprite


class SimpleRenderer():
    """ render world and HUD
    - on screen with sprites 
    - in sound with ogg mixer """
    
    def __init__(self):
        """define how the HUD should look like, 
        and prepare the game-world rendering """
        #create screen 
        pygame.display.set_caption(config_get_screencaption())
        pygame.mouse.set_visible(1) #1 == visible, 0==invisible
        resolution = (config_get_screenwidth(), config_get_screenheight()) 
        self.screen = pygame.display.set_mode(resolution)
        # screen background
        self.bg = pygame.Surface(self.screen.get_size()) 
        self.bg = self.bg.convert() #see http://pygame.org/docs/ref/surface.html#Surface.convert
        self.bg.fill((222, 204, 199)) #greyish
        self.screen.blit(self.bg, (0, 0))
        # HUD sprites
        self.hudsprs = pygame.sprite.Group()
        btn1 = AbstractHudBtn('square.png', (50,50), (100, 100))
        self.hudsprs.add(btn1)
        # world sprites
        self.worldsprs = pygame.sprite.Group()
        
        
    def render(self):
        """ fetch state, update sprites, and render world and HUD on screen"""
        # background
        self.screen.blit(self.bg, (0, 0)) 
        # HUD 
        self.hudsprs.draw(self.screen)
        # game world
        self.worldsprs.draw(self.screen)
        # reveal the scene - this is the last thing to do 
        pygame.display.flip()

        
