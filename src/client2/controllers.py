from client2.constants import DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT, \
    DIRECTION_UP
from client2.events import CharactorMoveRequest, TickEvent, QuitEvent, \
    ClickEvent
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_UP, K_DOWN, K_RIGHT, K_LEFT, \
    MOUSEBUTTONUP, K_BACKSPACE
from pygame.time import Clock
import pygame

#------------------------------------------------------------------------------
class InputController:
    """InputController takes Pygame events generated by the
    keyboard and uses them to control the model, by sending Requests
    or to control the Pygame display directly, as with the QuitEvent
    """
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

    #----------------------------------------------------------------------
    def notify(self, event):
        if isinstance(event, TickEvent):
            #Handle Input Events
            for event in pygame.event.get():
                ev = None
                # click on the window's X to close it
                if event.type == QUIT:
                    ev = QuitEvent()
                # keyboard events
                elif event.type == KEYDOWN: 
                    direction = None    
                    if event.key == K_ESCAPE:
                        ev = QuitEvent()
                    elif event.key == K_BACKSPACE:
                        ev = BackspaceKeyPushedEvent()
                    elif event.key == K_UP:
                        direction = DIRECTION_UP
                    elif event.key == K_DOWN:
                        direction = DIRECTION_DOWN
                    elif event.key == K_LEFT:
                        direction = DIRECTION_LEFT
                    elif event.key == K_RIGHT:
                        direction = DIRECTION_RIGHT
                    if direction:
                        ev = CharactorMoveRequest(direction)
                    elif event.unicode is not '': # visible characters
                        ev = UnicodeKeyPushedEvent(event.key, event.unicode)
                # click events
                elif event.type == MOUSEBUTTONUP and event.dict['button'] == 1:
                    ev = ClickEvent(event.dict['pos'])
                        
                if ev:
                    self.evManager.post(ev)


#------------------------------------------------------------------------------
class CPUSpinnerController:
    """..."""
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        self.keepGoing = True

    #----------------------------------------------------------------------
    def run(self):
        clock = Clock()
        while self.keepGoing:
            clock.tick(100) #100 fps max to save cpu
            event = TickEvent()
            self.evManager.post(event)
            
    #----------------------------------------------------------------------
    def notify(self, event):
        if isinstance(event, QuitEvent):
            #this will stop the while loop from running
            self.keepGoing = False

