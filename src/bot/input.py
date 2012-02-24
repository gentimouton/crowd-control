from bot.config import config_get_fps, config_get_movefreq
from client.events_client import ModelBuiltMapEvent, InputMoveRequest
from common.constants import DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, \
    DIRECTION_RIGHT
from common.events import TickEvent
import random


class BotInputController():
    """ Send random inputs now and then. """  
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(ModelBuiltMapEvent, self.start)
        self.moves = [DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT]
        self.mvtimer = int(config_get_fps())
        
        
    def start(self, event):
        """ Start sending events when the map is built """
        self._em.reg_cb(TickEvent, self.on_tick)
        
        
    def on_tick(self, event):
        """ Move every now and then """
                
        if self.mvtimer <= 0:
            self.mvtimer = int(config_get_fps() / config_get_movefreq())
            ev = InputMoveRequest(random.choice(self.moves))
            self._em.post(ev)
        
        else:
            self.mvtimer -= 1
            
            
