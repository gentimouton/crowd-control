from client.tools import load_image
import pygame

class HudBtn(pygame.sprite.Sprite):
    """
    clickable buttons of the HUD
    """
    
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('star.png', (100,100))
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.topleft = 50, 50
        
    def isinside(self, xy):
        """ return whether the given coords are inside the spr """
        x,y = xy
        return x <= 50+100 and x >= 50 and y >= 50 and y <= 50+100
    
    def clicked(self):
        print("clicked")