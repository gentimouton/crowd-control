from server.config import config_get_fps
from server.events_server import ServerTickEvent, SQuitEvent
from time import sleep
import logging

class SClockController():
    """ sends run events """

    log = logging.getLogger('server')

    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        self.fps = config_get_fps()
        if self.fps == 0:
            self.fps = 100 #100 fps is the maximum timer resolution anyway
            
        self.keep_going = True
        
        self.log.debug('Clock starts to tick at '+ str(self.fps) + ' fps')
        
        
    
    def run(self):
        """ Tick the clock at the given frame rate """
        
        elapsed_frames = 0
        
        while self.keep_going:
            sleep(1. / self.fps)
            event = ServerTickEvent()
            self.evManager.post(event)
            elapsed_frames += 1
        
        
        
    def notify(self, event):
        if isinstance(event, SQuitEvent):
            # stop the while loop from running
            self.keep_going = False
