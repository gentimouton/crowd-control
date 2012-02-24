from client.events_client import InputMoveRequest, QuitEvent, UpClickEvent, \
    DownClickEvent, MoveMouseEvent, UnicodeKeyPushedEvent, NonprintableKeyEvent, \
    InputAtkRequest
from common.constants import DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT, \
    DIRECTION_UP
from common.events import TickEvent
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_UP, K_DOWN, K_RIGHT, K_LEFT, \
    K_BACKSPACE, K_RETURN, MOUSEBUTTONUP, MOUSEBUTTONDOWN, MOUSEMOTION, K_RCTRL, \
    K_LCTRL
import pygame


class InputController:
    """ Every clock tick, the InputController looks at the events
    generated by keyboard and mouse and sends those events to the event manager
    """
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(TickEvent, self.on_tick)
        
        #non-printable keys used to detect when typing in a text input field
        self._nonprintable_keys = (K_RETURN, K_BACKSPACE)
        self._atk_keys = (K_RCTRL, K_LCTRL)
        
        #if key pushed for more than 150ms, then send KEYDOWN event every 50ms
        # TODO: should keyboard sensitivity be configurable?
        pygame.init() #calling init() multiple times does not mess anything
        pygame.key.set_repeat(150, 50) 
    

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
                                    
                elif pevent.key in self._atk_keys:
                    ev = InputAtkRequest()
                    
                elif pevent.key == K_UP:
                    ev = InputMoveRequest(DIRECTION_UP)
                elif pevent.key == K_DOWN:
                    ev = InputMoveRequest(DIRECTION_DOWN)
                elif pevent.key == K_LEFT:
                    ev = InputMoveRequest(DIRECTION_LEFT)
                elif pevent.key == K_RIGHT:
                    ev = InputMoveRequest(DIRECTION_RIGHT)

                elif pevent.key in self._nonprintable_keys: 
                    ev = NonprintableKeyEvent(pevent.key)
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

