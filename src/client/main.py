from client.config import load_config, config_get_fps
from client.controller.input import InputController
from client.controller.maincontroller import MainController
from client.controller.network import NetworkController
from client.model.chatlog import ChatLog
from client.simpleview.simpleview import SimpleView
import pygame


def main():    
    #init
    load_config() #config contains all the constants for the game
    pygame.init()
    view = SimpleView()
    chatlog = ChatLog()
    
    mc = MainController(chatlog)
    nwctrler = NetworkController(mc)
    mc.setnwctrler(nwctrler)
    ictrler = InputController(view, mc)
    
    clock = pygame.time.Clock()
    elapsed_frames = 0
    fps = config_get_fps()
    
    game_on = True
    while game_on:
        
        # passive wait (TODO: really?)
        clock.tick(fps)
        
        # process user inputs
        game_state = ictrler.process_events() 
        if game_state == ictrler.GAME_OVER:
            game_on = False
        
        # pull network msgs every frame, push less frequently
        nwctrler.pull()
        if elapsed_frames % nwctrler.push_frame_mod == 0:
            nwctrler.push()
        
        # run game mechanics on game state every frame
        #world.update_state()
        
        # render the world + HUD every frame
        view.render()
        
        elapsed_frames += 1


    
if __name__ == '__main__': main()
