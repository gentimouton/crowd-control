from common.events import TickEvent
from server.config import config_get_fps
from server.events_server import SQuitEvent
from time import sleep
import logging

class SClockController():
    """ sends run events """

    log = logging.getLogger('server')

    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(SQuitEvent, self.stop)

        self.fps = config_get_fps()
        if self.fps == 0:
            self.fps = 100 #100 fps is the maximum timer resolution anyway
            
        self.keep_going = True
        
        self.log.debug('Clock starts to tick at '+ str(self.fps) + ' fps')
        
        
    def stop(self, event):
        """ stop the while loop from running """
        self.keep_going = False
            

    def run(self):
        """ When all actions are done, wait for a few milliseconds. 
        This makes the frequency *at most* as fast as the specified frame rate.
        Irregular frames: those with more work will take longer than those with fewer. 
        """
        
        elapsed_frames = 0
        
        while self.keep_going:
            sleep(1. / self.fps)
            event = TickEvent()
            self._em.post(event)
            elapsed_frames += 1
        
        
        
