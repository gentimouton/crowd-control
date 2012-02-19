from common.events import TickEvent
        
class AiDirector():
    
    def __init__(self, evManager):
        self._em = evManager
        # callbacks
        self._em.reg_cb(TickEvent, self.on_tick)
        
        
    def on_tick(self, event):
        pass