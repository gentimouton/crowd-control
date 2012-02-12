from client.config import config_get_fps
from client.events_client import MoveMyCharactorRequest, QuitEvent, \
    UpClickEvent, DownClickEvent, MoveMouseEvent, UnicodeKeyPushedEvent, \
    NonprintableKeyEvent
from common.constants import DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT, \
    DIRECTION_UP
from common.events import TickEvent
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_UP, K_DOWN, K_RIGHT, K_LEFT, \
    K_BACKSPACE, K_RETURN, MOUSEBUTTONUP, MOUSEBUTTONDOWN, MOUSEMOTION
from pygame.time import Clock
import logging
import pygame


class InputController:
    """ Every clock tick, the InputController looks at the events
    generated by keyboard and mouse and sends those events to the event manager
    """
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(TickEvent, self.on_tick)
        #non-printable keys to detect when typing in a text input field
        self._nonprintable_keys = (K_RETURN, K_BACKSPACE)
    

    def on_tick(self, tickevent):
        """ every clock tick, handle input events from keyboard and mouse """

        for pevent in pygame.event.get():
            ev = None
            
            # click on the window's X to close it
            if pevent.type == QUIT:
                ev = QuitEvent()
                
            # keyboard events
            elif pevent.type == KEYDOWN:
                if pevent.key == K_ESCAPE:
                    ev = QuitEvent()
                elif pevent.key in self._nonprintable_keys: 
                    ev = NonprintableKeyEvent(pevent.key)
                elif pevent.key == K_UP:
                    ev = MoveMyCharactorRequest(DIRECTION_UP)
                elif pevent.key == K_DOWN:
                    ev = MoveMyCharactorRequest(DIRECTION_DOWN)
                elif pevent.key == K_LEFT:
                    ev = MoveMyCharactorRequest(DIRECTION_LEFT)
                elif pevent.key == K_RIGHT:
                    ev = MoveMyCharactorRequest(DIRECTION_RIGHT)
                elif pevent.unicode is not '': 
                    # visible chars: letters, numbers, punctuation, space
                    ev = UnicodeKeyPushedEvent(pevent.key, pevent.unicode)
                    
            # click events
            elif pevent.type == MOUSEBUTTONDOWN and pevent.button == 1:
                ev = DownClickEvent(pevent.pos)
            elif pevent.type == MOUSEBUTTONUP and pevent.button == 1:
                ev = UpClickEvent(pevent.pos)
            elif pevent.type == MOUSEMOTION:
                ev = MoveMouseEvent(pevent.pos)
                    
            if ev:
                self._em.post(ev)


    


###########################################################################


class ClockController:
    """ Each clock tick sends a TickEvent """
    log = logging.getLogger('client')
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(QuitEvent, self.on_quit)
        self.keep_going = True


    def run(self):
        """ keep the clock running """
        clock = Clock()
        while self.keep_going:
            clock.tick(config_get_fps())
            event = TickEvent()
            self._em.post(event)
            

    def on_quit(self, qevent):
        """ stop the while loop from running """
        self.keep_going = False



            
