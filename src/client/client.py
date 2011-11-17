from config import load_config, config_get_fps, config_get_screencaption, \
    config_get_screenheight, config_get_screenwidth
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
import pygame
from doolclient import Client

def main():
    
    #init
    load_config() #config contains all the constants for the game
    pygame.init()
    pygame.display.set_caption(config_get_screencaption())
    pygame.mouse.set_visible(1) #1 == visible, 0==invisible
    res = (config_get_screenwidth(), config_get_screenheight()) #res = 800*600px
    screen = pygame.display.set_mode(res)
    # graphics of BG
    bg = pygame.Surface(screen.get_size()) 
    bg = bg.convert()
    bg.fill((222, 204, 199)) #greyish

    #Put Text On The Background, Centered
    if pygame.font:
        font = pygame.font.Font(None, 36)
        text = font.render("Pummel The Chimp, And Win $$$", 1, (10, 10, 10))
        textpos = text.get_rect(centerx=bg.get_width()/2)
        bg.blit(text, textpos)

    #Display The Background
    screen.blit(bg, (0, 0))
    pygame.display.flip()

    #network and game objects
    nwclient = Client('localhost',8080)
    
    clock = pygame.time.Clock()
    elapsed_frames = 0
    
    #Main Loop
    while 1:
        clock.tick(config_get_fps()) #number of frames per second 
        pygame.display.set_caption(config_get_screencaption() + " --- FPS: " + str(clock.get_fps()))
        
        #Handle Input Events
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return
        
        # updates
        nwclient.Loop()
        if elapsed_frames % 30 == 1:
            nwclient.send_msg("wraaaaa")
        # draws
        screen.blit(bg,(0,0)) #bg is grey with text
        # TODO: display eventual sprites
        pygame.display.flip() #reveal the scene - this is the last thing to do in the loop
        elapsed_frames += 1


    
if __name__ == '__main__': main()
