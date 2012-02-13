from common.clock import Clock
from common.events import TickEvent
from server.config import config_get_fps
from server.events_server import SQuitEvent
import logging


class SClockController(Clock):
    """ sends tick events """

    log = logging.getLogger('server')

    def __init__(self, evManager):
        
        fps = config_get_fps()
        if fps == 0:
            fps = 100 #100 fps is the maximum timer resolution anyway
        Clock.__init__(self, fps)
        
        self._em = evManager
        self._em.reg_cb(SQuitEvent, self.stop)

        
        
            
    def on_tick(self, frame_num):
        event = TickEvent()
        self._em.post(event)
        
    
    def start(self):
        self.log.debug('Clock starts to at ' + str(self.fps) + ' fps')
        Clock.start(self)
        
        
