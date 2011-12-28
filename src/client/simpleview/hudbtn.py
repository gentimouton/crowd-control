from client.tools import load_image
import pygame

class AbstractHudBtn(pygame.sprite.Sprite):
    """ Abstract class for clickable HUD buttons """
    
    def __init__(self, imgname, topleft, dims):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image(imgname, dims)
        __screen = pygame.display.get_surface()
        self.area = __screen.get_rect()
        self.rect.topleft = topleft
        self.top, self.left = topleft
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
