from client.config import load_config, config_get_fps
from client.controller.input import InputController
from client.controller.maincontroller import MainController
from client.controller.network import NetworkController
from client.model.chatlog import ChatLog
from client.simpleview.simpleview import SimpleView
import pygame
from pygame.locals import TIMER_RESOLUTION


def main():    
    #init
    load_config() #config contains all the constants for the game
    pygame.init()
    
    # model: game mechanics and state
    chatlog = ChatLog()
    
    # view and controllers
    mc = MainController(chatlog)
    view = SimpleView(chatlog, mc)    
    nwctrler = NetworkController(mc)
    mc.setnwctrler(nwctrler)
    ictrler = InputController(view, mc)
    
    clock = pygame.time.Clock()
    elapsed_frames = 0
    fps = config_get_fps()
    cpu_timer_res = pygame.locals.TIMER_RESOLUTION
    if 1000 / fps < cpu_timer_res:
        print("Warning:", fps, "fps is higher than the ",
               "CPU timer resolution of", cpu_timer_res, "ms")
    
    game_on = True
    while game_on:
        
        """ clock.tick() uses SDL_Delay function which is not accurate 
        on every platform, but does not use much cpu, see
        http://pygame.org/docs/ref/time.html#Clock.tick """
        frame_delay = clock.tick(fps)
        
        # process user inputs
        game_state = ictrler.process_events() 
        if game_state == ictrler.GAME_OVER:
            game_on = False
        
        # pull network msgs every frame, push less frequently
        nwctrler.pull()
        nwctrler.push()

        
        # run game mechanics on game state every frame
        #world.update_state()
        
        # render the world + HUD every frame
        view.render(frame_delay)
        
        elapsed_frames += 1


    
if __name__ == '__main__': main()
