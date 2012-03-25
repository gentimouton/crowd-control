from bot.config import config_get_fps, config_get_movefreq
from client.events_client import MBuiltMapEvt, InputMoveRequest
from common.constants import DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, \
    DIRECTION_RIGHT
from common.events import TickEvent
import random


class BotInputController():
    """ Send random inputs now and then. """  
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(MBuiltMapEvt, self.start)
        self.moves = [DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT]
        fps = config_get_fps()
        self.mvtimer = fps
        self.mvdelay = fps / config_get_movefreq()
        
    def start(self, event):
        """ Start sending events when the map is built """
        self._em.reg_cb(TickEvent, self.on_tick)
        
        
    def on_tick(self, event):
        """ Move every now and then """
            
        if self.mvtimer <= 0:
            self.mvtimer = self.mvdelay
            ev = InputMoveRequest(random.choice(self.moves))
            self._em.post(ev)
        
        else:
            self.mvtimer -= 1
            
            
#####################################################################            


if __name__ == "__main__":
    import unittest
    from bot.config import load_bot_config
    
    # load config only once (not for each test)
    load_bot_config()
    
    class MockEvMgr():
        callbacks = {} # map events to callbacks
        posted = [] # tracks posted events
        def post(self, ev):
            self.posted.append(ev)
        def reg_cb(self, evt, cb):
            self.callbacks[evt] = cb
        
    class TestBotConfig(unittest.TestCase):
        
        def setUp(self):
            self.em = MockEvMgr()
        
        def test_all(self):
            # check that things start OK
            bot = BotInputController(self.em)
            bot.start(None)
            bot.on_tick(None)            
            
        def tearDown(self):
            pass
        
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBotConfig)
    unittest.TextTestRunner(verbosity=2).run(suite)
      