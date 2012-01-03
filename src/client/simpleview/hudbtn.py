from client.tools import load_image
from pygame.sprite import Sprite


class HudBtn(Sprite):
    """ Abstract class for clickable HUD buttons """
    
    def __init__(self, imgname, topleft, widtheight, *groups):
        Sprite.__init__(self, *groups)
        self.image, self.rect = load_image(imgname, widtheight)
        self.width, self.height = widtheight
        self.top, self.left = topleft
        self.rect.topleft = self.left, self.top
        
    def set_topleft(self, topleft):
        self.left, self.top = topleft
        self.rect.topleft = self.left, self.top
        
    def set_img(self, imgname):
        self.image, self.rect = load_image(imgname, (self.width, self.height))
        self.rect.topleft = self.left, self.top 
        
    def set_widtheight(self, widtheight):
        self.width, self.height = widtheight 
        
        
    def isinside(self, pos):
        """ return whether the given coords are inside the spr """
        x, y = pos
        return (x <= self.left + self.width 
                and x >= self.left 
                and y >= self.top 
                and y <= self.top + self.height)
    
    def onclicked(self):
        raise NotImplementedError("onclicked() should be implemented")
