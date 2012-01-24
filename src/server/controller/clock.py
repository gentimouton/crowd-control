from server.config import config_get_fps
from server.events_server import ServerTickEvent, SQuitEvent
from time import sleep

class SClockController():
    """ sends tick events """
    
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        self.fps = config_get_fps()
        self.keep_going = True
        
    
    def tick(self):
        """ tick the clock at the given frame rate """
        while self.keep_going:
            sleep(1. / self.fps)
            event = ServerTickEvent()
            self.evManager.post(event)
            
        
        
        
    def notify(self, event):
        if isinstance(event, SQuitEvent):
            # stop the while loop from running
            self.keep_going = False
