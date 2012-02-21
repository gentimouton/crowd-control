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
        if fps <= 0 or fps > 100:
            fps = 100 #100 fps is the maximum timer resolution anyway
        Clock.__init__(self, fps)
        
        self.avgworkdur = 0 # avg work duration per frame
        
        self._em = evManager
        self._em.reg_cb(SQuitEvent, self.stop)

            
    def on_tick(self, workduration, totalduration):
        """ Log how much time during a frame was spent working, 
        and send a tick event with the whole loop duration.
        """
        self.avgworkdur += workduration
        if self.elapsed_frames % 1000 == 999:
            self.avgworkdur = self.avgworkdur / 1000
            self.log.debug('Frames %d to %d worked on average %3.3f ms',
                           self.elapsed_frames - 999, self.elapsed_frames, self.avgworkdur)
            
        event = TickEvent(totalduration) #duration in millis
        self._em.post(event)
        
    
    def start(self):
        self.log.debug('Clock starts to at ' + str(self.fps) + ' fps')
        Clock.start(self)
        
        