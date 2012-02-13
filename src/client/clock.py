
from client.events_client import QuitEvent
from common.clock import Clock
from common.events import TickEvent
import logging


class CClockController(Clock):
    """ Each clock tick sends a TickEvent """
    log = logging.getLogger('client')
    
    
    def __init__(self, evManager, fps):
        
        if fps == 0:
            fps = 100 #100 fps is the maximum timer resolution anyway
        Clock.__init__(self, fps)
        
        self._em = evManager
        self._em.reg_cb(QuitEvent, self.on_quit)


    
    def start(self):
        self.log.debug('Clock starts to tick at ' + str(self.fps) + ' fps')
        Clock.start(self)
        
            

    def on_quit(self, qevent):
        """ stop the while loop from running """
        Clock.stop(self)



    def on_tick(self, frame_num):
        event = TickEvent()
        self._em.post(event)
            
