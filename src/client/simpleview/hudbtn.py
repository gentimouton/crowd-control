from client.tools import load_image
import pygame

class AbstractHudBtn(pygame.sprite.Sprite):
    """ Abstract class for clickable HUD buttons """
    
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        __screen = pygame.display.get_surface()
        assert(__screen != None,
               "display.get_surface() requires to have display.setmode() before") 
        # default behavior, can be changed with setters below
        self.top, self.left = 50, 150
        self.width, self.height = 50, 50
        
        
    def setpos(self, topleft):
        self.top, self.left = topleft
        
    def setimg(self, imgname):
        self.image, self.rect = load_image(imgname, (self.width, self.height))
        self.rect.topleft = self.top, self.left
        
    def setdims(self, dims):
        self.width, self.height = dims 
        
        
    def isinside(self, pos):
        """ return whether the given coords are inside the spr """
        x, y = pos
        return (x <= self.left + self.width 
                and x >= self.left 
                and y >= self.top 
                and y <= self.top + self.height)
    
    def onclicked(self):
        raise NotImplementedError("onclicked() should be implemented")
