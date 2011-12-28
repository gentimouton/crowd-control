import os.path, pygame
from pygame.locals import RLEACCEL


#return loaded img surface and its rect 
def load_image(name, destsize):
    fullname = os.path.join("img/", name)
    try:
        image = pygame.image.load(fullname)
    except: 
        pygame.error
        print("Cannot load image: ", fullname)
        raise SystemExit
    image = image.convert()
    colorkey = image.get_at((0,0)) #the color of top left pixel is considered the transparent color 
    image.set_colorkey(colorkey, RLEACCEL)
    image = pygame.transform.scale(image, destsize)

    return image, image.get_rect()