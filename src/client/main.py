from config import load_config, config_get_fps, config_get_screencaption, \
    config_get_screenheight, config_get_screenwidth, config_get_host, \
    config_get_port
from network import Client
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
import pygame

def main():
    
    #init
    load_config() #config contains all the constants for the game
    pygame.init()
    pygame.display.set_caption(config_get_screencaption())
    pygame.mouse.set_visible(1) #1 == visible, 0==invisible
    resolution = (config_get_screenwidth(), config_get_screenheight()) 
    screen = pygame.display.set_mode(resolution)
    
    # graphics of BG
    bg = pygame.Surface(screen.get_size()) 
    bg = bg.convert()
    bg.fill((222, 204, 199)) #greyish

    #Put Text On The Background, Centered
    if pygame.font:
        font = pygame.font.Font(None, 32)
        text = font.render("Hello \o/", 1, (10, 150, 210), (255,255,255))
        textpos = text.get_rect(centerx=bg.get_width() / 2)
        bg.blit(text, textpos)

    #Display The Background
    screen.blit(bg, (0, 0))
    pygame.display.flip()

    #network and game objects
    nwclient = Client(config_get_host(), config_get_port())
    
    clock = pygame.time.Clock()
    elapsed_frames = 0
    
    #Main Loop
    while 1:
        clock.tick(config_get_fps()) #number of frames per second
        ttl = config_get_screencaption() + " - FPS: " + str(clock.get_fps()) 
        pygame.display.set_caption(ttl)
        
        #Handle Input Events
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return
        
        # updates
        nwclient.push_and_pull()
        if elapsed_frames % 90 == 1:
            nwclient.send_msg("greeee")
        # draws
        screen.blit(bg, (0, 0)) #bg is grey with text
        # TODO: display all sprites
        
        #reveal the scene - this is the last thing to do in the loop
        pygame.display.flip() 
        elapsed_frames += 1


    
if __name__ == '__main__': main()
