from client.config import load_config, config_get_fps
from client.controller.inputcontroller import InputController
from client.simpleview.viewcontroller import SimpleViewCtrler
from client.simpleview.renderer import Renderer
import pygame


def main():    
    #init
    load_config() #config contains all the constants for the game
    pygame.init()
    # TODO: simply initiate a SimpleView() that handles a ViewController and a TopDownRenderer
    rdr = Renderer()
    vc = SimpleViewCtrler(rdr)
    ictrler = InputController(vc)

    #nwctrler = NetworkController()
    clock = pygame.time.Clock()
    elapsed_frames = 0
    
    #Main Loop
    game_on = True
    while game_on:
        clock.tick(config_get_fps()) 
        if ictrler.process_events() == ictrler.GAME_OVER:
            game_on = False
        
        # handle network messages
        # nwctrler.pull()
        
        # run game mechanics on game state every frame
        #model.update()
        
        # draw every frame
        rdr.render()
        
        elapsed_frames += 1


    
if __name__ == '__main__': main()
