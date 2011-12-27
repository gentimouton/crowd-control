from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, MOUSEBUTTONUP
import pygame


class InputController():
    
    def __init__(self, view, mainctrler):
        self.GAME_OVER = 1 #constant
        self.view = view
        self.mc = mainctrler

    
    def process_events(self):
        """ Escape key or quit => stop the game
        left click => check if it's located in the HUD part 
        or the world part of the screen """
        for event in pygame.event.get():
            if event.type == QUIT:
                return self.GAME_OVER
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return self.GAME_OVER
            elif event.type == MOUSEBUTTONUP:
                if event.dict['button'] == 1: 
                    # 1= left click, 2 = middle, 3 = right 
                    self.view.process_click_event(event.dict['pos'])
            elif event.type == KEYDOWN:
                self.get_action_from_key(event.dict['key'])
            
                

    def get_action_from_key(self, key):
        """ translate key to a method from MainController """
        # carriage return to send to server, otherwise append to existing string
        if key == 13:
            self.mc.send_string_typed()
        else:
            self.mc.add_char_typed(chr(key))
        
    
