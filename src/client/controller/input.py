from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, MOUSEBUTTONUP, K_RETURN, \
    K_BACKSPACE, K_DOWN, K_UP
import pygame



class InputController():
    
    def __init__(self, view, mainctrler):
        self.GAME_OVER = 1 #constant
        self.view = view
        self.mc = mainctrler
        #if key pushed for more than 400ms, then send KEYDOWN event every 25ms
        # TODO: keyboard sensitivity should be configurable
        pygame.key.set_repeat(400, 25) 

    
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
                    self.run_action_from_key(event.dict['key'],
                                             event.dict['unicode'])
            elif event.type == MOUSEBUTTONUP:
                if event.dict['button'] == 1: 
                    # 1= left click, 2 = middle, 3 = right 
                    self.view.process_click_event(event.dict['pos'])

                
            
                

    def run_action_from_key(self, key, unicodechar):
        """ translate key to a method from MainController """
        # carriage return to send to server, otherwise append to existing string
        if key == K_RETURN:
            self.mc.validate()
        elif key == K_BACKSPACE: 
            self.mc.backspace()
        elif key == K_UP:
            self.mc.go_up()
        elif key == K_DOWN:
            self.mc.go_down()
        elif unicodechar == '': 
            # K_LSHIFT, K_F1, K_PAGEUP, K_UP ... should not be added
            return
        else: # a visible character should be printed 
            self.mc.add_char_typed(unicodechar)
        
    
