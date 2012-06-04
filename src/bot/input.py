from bot.config import config_get_fps, config_get_movefreq, config_get_atkfreq
from client.events_client import MBuiltMapEvt, InputMoveRequest, InputAtkRequest
from common.constants import DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, \
    DIRECTION_RIGHT, DIRECTIONS
from common.events import TickEvent
import random


class BotInputController():
    """ Bot AI: Simulate user inputs based on the current model. """  
    
    def __init__(self, evManager, model):
        self._em = evManager
        self._em.reg_cb(MBuiltMapEvt, self.start)
        self.model = model # TODO: move this into a model-dependent AI component 
        self.moves = [DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT]
        fps = config_get_fps()
        self.mvtimer = 0
        self.mvdelay = fps / config_get_movefreq()
        self.atktimer = 0
        self.atkdelay = fps / config_get_atkfreq()
        
        
    def start(self, event):
        """ Start sending events when the map is built """
        self._em.reg_cb(TickEvent, self.on_tick)
        
        
    def on_tick(self, event):
        """ Move every now and then. 
        Attack if a creep is in range.
        """
            
        if self.mvtimer > 0: # currently moving
            self.mvtimer -= 1
        elif self.atktimer > 0: # currently attacking
            self.atktimer -= 1
        else: # If creep nearby, attack it. Otherwise, move.
            # TODO: move this part in an AI component that depends on the model
            me = self.model.avs[self.model.myname]
            mycell = me.cell
            dest = mycell.get_adjacent_cell(me.facing)
            if dest: # cell is not a wall: move
                if dest.get_creeps():
                    self.atktimer = self.atkdelay
                    ev = InputAtkRequest()
                    self._em.post(ev)
                else:
                    self.mvtimer = self.mvdelay
                    ev = InputMoveRequest(me.facing)
                    self._em.post(ev)
            else: # cell is a wall: go in a direction without wall
                directions = list(DIRECTIONS) # make a copy to randomize
                random.shuffle(directions)
                for direction in directions:
                    cell = mycell.get_adjacent_cell(direction)
                    if cell:# found a direction: stop the loop
                        break;
                self.mvtimer = self.mvdelay
                ev = InputMoveRequest(direction, rotating=True)
                self._em.post(ev)


            
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
