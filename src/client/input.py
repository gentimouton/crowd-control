from client.events_client import InputMoveRequest, QuitEvent, UpClickEvent, \
    DownClickEvent, MoveMouseEvent, UnicodeKeyPushedEvent, NonprintableKeyEvent, \
    InputAtkRequest
from common.constants import DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT, \
    DIRECTION_UP
from common.events import TickEvent
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_UP, K_DOWN, K_RIGHT, K_LEFT, \
    K_BACKSPACE, K_RETURN, MOUSEBUTTONUP, MOUSEBUTTONDOWN, MOUSEMOTION, K_RCTRL, \
    K_LCTRL, KMOD_LSHIFT, KMOD_RSHIFT
import pygame


class InputController:
    """ Every clock tick, the InputController looks at the events
    generated by keyboard and mouse and sends those events to the event manager
    """
    
    # map an arrow key to a game direction
    _key2dir = {    
                K_UP:      DIRECTION_UP,
                K_DOWN:    DIRECTION_DOWN,
                K_LEFT:    DIRECTION_LEFT,
                K_RIGHT:   DIRECTION_RIGHT
                }
    
    #non-printable keys used to detect when typing in a text input field
    _nonprintable_keys = [K_RETURN, K_BACKSPACE]
    _atk_keys = [K_RCTRL, K_LCTRL]     
    _straf_keys = [KMOD_LSHIFT, KMOD_RSHIFT]
        
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(TickEvent, self.on_tick)
        
        #if key pushed for more than 100ms, then send KEYDOWN event every 25ms
        pygame.init() #calling init() multiple times does not mess anything
        pygame.key.set_repeat(100, 25) 
    

    def on_tick(self, tickevent):
        """ every clock tick, handle input events from keyboard and mouse """

        for pevent in pygame.event.get():
            ev = None
            
            # click on the window's X to close it
            if pevent.type == QUIT:
                ev = QuitEvent()
                
            # keyboard events
            elif pevent.type == KEYDOWN:
                key, unicode = pevent.key, pevent.unicode
                
                if key == K_ESCAPE:
                    ev = QuitEvent()
                                    
                elif key in self._atk_keys:
                    ev = InputAtkRequest()
                    
                elif key in self._key2dir:
                    mods = pygame.key.get_mods()
                    # check for strafing keys ON
                    straf = False
                    for k in self._straf_keys:
                        if mods & k:
                            straf = True
                            break
                    # send input msg 
                    ev = InputMoveRequest(self._key2dir[key], straf)

                elif key in self._nonprintable_keys: 
                    ev = NonprintableKeyEvent(key)
                elif unicode is not '': 
                    # visible chars: letters, numbers, punctuation, space, tab
                    ev = UnicodeKeyPushedEvent(key, unicode)
                    
            # click events
            elif pevent.type == MOUSEBUTTONDOWN and pevent.button == 1:
                ev = DownClickEvent(pevent.pos)
            elif pevent.type == MOUSEBUTTONUP and pevent.button == 1:
                ev = UpClickEvent(pevent.pos)
            elif pevent.type == MOUSEMOTION:
                ev = MoveMouseEvent(pevent.pos)
                    
            if ev:
                self._em.post(ev)

