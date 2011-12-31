from client.config import config_get_screencaption, config_get_screenwidth, \
    config_get_screenheight
import pygame


class SimpleRenderer():
    """ render world and HUD
    - on screen with sprites 
    - in sound with ogg mixer """
    # TODO: renderer should be split into a HudRenderer and a WorldRenderer,
    #each with its own sprites
     
     
    def __init__(self, worldsprites, hudsprites, chatlog):
        """define how the HUD should look like, 
        and prepare the game-world rendering """
        self.chatlog = chatlog
        # world and hud sprites point to the sprites from simpleview
        self.worldsprites = worldsprites
        self.hudsprites = hudsprites
        
        #create screen
        pygame.display.set_caption(config_get_screencaption())
        pygame.mouse.set_visible(1) #1 == visible, 0==invisible
        resolution = config_get_screenwidth(), config_get_screenheight() 
        self.__screen = pygame.display.set_mode(resolution)
        # defaultbg = background template
        self.__defaultbg = self._make_bg(self.__screen)
        self.bg = self.__defaultbg.copy() #the running bg
  
        
        
    def _make_bg(self, screen):
        """ make a default empty background """
        bg = pygame.Surface(screen.get_size()) 
        bg = bg.convert()
        #see http://pygame.org/docs/ref/surface.html#Surface.convert
        bg.fill((255, 204, 153))
        return bg

    def build_hud(self):        
        btn1 = self.hudsprites.sprites()[0] 
        #TODO: hudprites should be a dict instead of array
        btn1.setpos((50, 50))
        btn1.setdims((100, 100))
        btn1.setimg('square.png')
        self.alivehudsprites = pygame.sprite.Group()
        self.alivehudsprites.add(btn1)

        
    def render(self, frame_period):
        """ fetch state, update sprites, and render world and HUD on screen"""
        fps = str(int(1000 / frame_period))
        caption = str(config_get_screencaption()) + " -- " + fps + " fps"
        pygame.display.set_caption(caption)
        
        # background
        self.bg = self.__defaultbg.copy()
        self.render_chat()
        self.__screen.blit(self.bg, (0, 0))
        
        # draw game world on top of the bg
        self.worldsprites.draw(self.__screen)
        
        # add HUD sprites on top of everything
        btn1 = self.hudsprites.sprites()[0]
        if self.chatlog.is_helloed():
            btn1.remove(self.alivehudsprites)
        else:
            btn1.add(self.alivehudsprites)
        self.alivehudsprites.draw(self.__screen)
        
        # reveal the scene - this is the last thing to do 
        pygame.display.flip()

        
    def render_chat(self):
        """ render the chat window on top of the bg """
        lines = self.chatlog.get_complete_log()
        font = pygame.font.Font(None, 25)
        for i in range(len(lines)):
            line = lines[i]
            txt = line['author'] + ' says: ' + line['txt']
            txtsurf = font.render(txt, False, (0, 0, 0))# no antialiasing, black
            # TODO: position the text
            txtbottom = self.__screen.get_size()[1] - 20 * i - 50
            txtleft = 10
            textpos = txtsurf.get_rect(bottom=txtbottom, left=txtleft)
            self.bg.blit(txtsurf, textpos)
        
