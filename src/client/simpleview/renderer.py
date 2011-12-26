"""
renders world and HUD
- on screen with sprites 
- in sound with ogg mixer
"""
from client.config import config_get_screencaption, config_get_screenwidth, \
    config_get_screenheight
from client.simpleview.hudbtn import HudBtn
import pygame.sprite


class Renderer():
    def __init__(self):
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
        # hud - create a dummy button
        btn1 = HudBtn()
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(btn1)

        
        
    def render(self):
        """ fetch state, update sprites, and render world and HUD on screen"""
        # background
        self.screen.blit(self.bg, (0, 0)) 
        # HUD 
        self.all_sprites.draw(self.screen)
        # game world
        #TODO
        # reveal the scene - this is the last thing to do 
        pygame.display.flip()

        
