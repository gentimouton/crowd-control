from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, MOUSEBUTTONUP
import pygame


class InputController():
    
    def __init__(self, view, mainctrler):
        self.GAME_OVER = 1 #constant
        self.view = view
        self.mc = mainctrler
        #if key pushed for more than 100ms, then send KEYDOWN event every 100ms
        # TODO: keyboard sensitivity should be configurable
        pygame.key.set_repeat(100, 100) 

    
    def process_events(self):
        """ Escape key or quit => stop the game
        left click => check if it's located in the HUD part 
        or the world part of the screen """
        for event in pygame.event.get():
            if event.type == QUIT: #window closed 
                return self.GAME_OVER
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return self.GAME_OVER
                else:
                    self.get_action_from_key(event.dict['key'],
                                             event.dict['unicode'])
            elif event.type == MOUSEBUTTONUP:
                if event.dict['button'] == 1: 
                    # 1= left click, 2 = middle, 3 = right 
                    self.view.process_click_event(event.dict['pos'])

                
            
                

    def get_action_from_key(self, key, char):
        """ translate key to a method from MainController """
        # carriage return to send to server, otherwise append to existing string
        if key == 13:
            self.mc.send_string_typed()
        elif key == 8:
            self.mc.remove_char_typed()
        else:
            self.mc.add_char_typed(char)
        
    
