from client.config import config_get_screencaption, config_get_screenwidth, \
    config_get_screenheight
from client.simpleview.hudbtn import AbstractHudBtn
import pygame.sprite


class SimpleRenderer():
    """ render world and HUD
    - on screen with sprites 
    - in sound with ogg mixer """
    # TODO: renderer should be split into a HudRenderer and a WorldRenderer,
    #each with its own sprites
     
     
    def __init__(self, chatlog):
        """define how the HUD should look like, 
        and prepare the game-world rendering """
        self.chatlog = chatlog
        #create screen
        pygame.display.set_caption(config_get_screencaption())
        pygame.mouse.set_visible(1) #1 == visible, 0==invisible
        resolution = (config_get_screenwidth(), config_get_screenheight()) 
        self.__screen = pygame.display.set_mode(resolution)
        # defaultbg = background template
        self.__defaultbg = self._make_bg(self.__screen)
        self.bg = self.__defaultbg.copy() #the running bg  
        self.bg = self.__defaultbg.copy()
        # HUD sprites
        self.hudsprs = pygame.sprite.Group()
        btn1 = AbstractHudBtn('square.png', (50,50), (100, 100))
        self.hudsprs.add(btn1)
        # world sprites
        self.worldsprs = pygame.sprite.Group()
        
        
    def _make_bg(self, screen):
        """ make a default empty background """
        bg = pygame.Surface(screen.get_size()) 
        bg = bg.convert()
        #see http://pygame.org/docs/ref/surface.html#Surface.convert
        bg.fill((255, 204, 153))
        return bg
 
        
    def render(self):
        """ fetch state, update sprites, and render world and HUD on screen"""
        # background
        self.bg = self.__defaultbg.copy()
        
        # chat
        lastmsg = self.chatlog.get_last_msg()
        if lastmsg == {}:
            txt = ''
        else:
            txt = lastmsg['author'] + ' says: ' + lastmsg['txt']
        font = pygame.font.Font(None, 36)
        # If antialiasing is not used, the return image will always be 
        # an 8bit image with a two color palette. 
        # If the background is transparent a colorkey will be set.
        # see http://pygame.org/docs/ref/font.html#Font.render
        txtsurf = font.render(txt, False, (10, 10, 10))
        textpos = txtsurf.get_rect(centerx=self.bg.get_width()/2)
        self.bg.blit(txtsurf, textpos)
        self.__screen.blit(self.bg, (0, 0))
        
        # draw game world on top of the bg
        self.worldsprs.draw(self.__screen)

        # add HUD sprs on top of everything
        self.hudsprs.draw(self.__screen)
        

        # reveal the scene - this is the last thing to do 
        pygame.display.flip()

        
