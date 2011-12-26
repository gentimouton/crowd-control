from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, MOUSEBUTTONUP
import pygame


class InputController():
    
    def __init__(self, vc):
        self.GAME_OVER = 1 #constant
        self.vc = vc

    
    def process_events(self):
        """ Escape key or quit => stop the game
        left click => check if it's located in the HUD part 
        or the world part of the screen
        """
        for event in pygame.event.get():
            if event.type == QUIT:
                return self.GAME_OVER
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return self.GAME_OVER
            elif event.type == MOUSEBUTTONUP:
                if event.dict['button'] == 1: 
                    # 1= left click, 2 = middle, 3 = right 
                    self.vc.process_click_event(event.dict['pos'])
            elif event.type == KEYDOWN:
                self.get_action_from_key(event.dict['key'])
                

    def get_action_from_key(self,key):
        """
        translate key to main controller methods
        """
        print(key)
        
        