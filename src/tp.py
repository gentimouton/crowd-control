if __name__ == "__main__":
    
    from pygame.sprite import Sprite
    from pygame.surface import Surface
    from pygame.locals import KEYDOWN, RLEACCEL, SRCALPHA
    from pygame.font import Font
    
    class TxtSpr(Sprite):
        def __init__(self, color, initial_position):
            Sprite.__init__(self)
            size = 50, 50
            self.image = Surface(size)
            self.image.fill(color)
            self.rect = self.image.get_rect()
            self.rect.topleft = initial_position
        
    pygame.init()

    flags = pygame.HWSURFACE | pygame.DOUBLEBUF
    screen = pygame.display.set_mode((300, 300), flags)

    dipslayinfo = pygame.display.Info()
    print(str(dipslayinfo))
    
    bg = Surface((200, 200))
    bg.fill((255, 0, 0))    
    bg = bg.convert()
    screen.blit(bg, (50, 50))

    font = Font(None, 25)
    txt = 'qwertyuiop'
    txtimg = font.render(txt, 0, (255, 255, 255))    
    print('txtimg colorkey: ' + str(txtimg.get_colorkey()))
    print('txtimg flags: ' + str(txtimg.get_flags()))
    
    b = Surface((100, 100), SRCALPHA)
    b.fill((111, 111, 111, 128))
    b.blit(txtimg, (10, 10))
    b = b.convert_alpha()
    print('b colorkey: ' + str(b.get_colorkey()))
    print('b flags: ' + str(b.get_flags()))
    screen.blit(b, (25, 25))
    
    
    c = Surface((100, 100))
    colkey = (255, 0, 255)
    c.set_colorkey(colkey, RLEACCEL)
    c.fill(colkey) # make the surface bg invisible
    print('c colorkey: ' + str(c.get_colorkey()))
    print('c flags: ' + str(c.get_flags()))
    
    #c2 = Surface((100, 100))
    #c2.fill((111, 111, 111))
    #c2.set_alpha(128, RLEACCEL) # semi-transparent gray bg
    #c.blit(c2, (0, 0))
    txtimg2 = txtimg.convert(c)
    print('txtimg2 colorkey: ' + str(txtimg2.get_colorkey()))
    print('txtimg2 flags: ' + str(txtimg2.get_flags()))
    c.blit(txtimg2, (10, 10))
    c = c.convert()
    screen.blit(c, (125, 25))
        
    pygame.display.update()
    
    while pygame.event.poll().type != KEYDOWN:
        pygame.time.delay(10)

