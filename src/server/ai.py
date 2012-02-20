from common.events import TickEvent
from server.events_server import SBroadcastCreepArrivedEvent, \
    SBroadcastCreepMoveEvent
from uuid import uuid4
import random
        
class AiDirector():
    
    def __init__(self, evManager, world):
        self.world = world
        self._em = evManager
        # callbacks
        self._em.reg_cb(TickEvent, self.on_tick)
        
        # action frames and delays
        self.timestep = 100 #in milliseconds; means that AI logic runs at 10Hz
        self.frameoverflow = 0 #how much time overflowed from previous frame
        # when overflow > timestep, we should increase the cursor to the next frame(s) 
        
        # Each frame of actionq contains a set of entity callbacks 
        self.actionq = [set() for x in range(50)] # each slot for a timestep  
        self.actioncursor = 0 #loops over the actionq
        self.distantactions = set() # slot for actions so distant in the future that they dont fit in actionq
        
        # create a dummy creep
        self.creeps = dict()
        creepid = int(uuid4())
        creep = Creep(self._em, self, creepid)
        self.creeps[creepid] = creep
        
        
    def add_action(self, millis, callback):
        """ Add an entity's callback to be called in millis +/- timestep ms."""
        if millis < len(self.actionq) * self.timestep:
            index = self.actioncursor + int(millis / self.timestep)
            # if millis < timestep, do it next frame
            index = max(1, index % len(self.actionq)) 
            self.actionq[index].add(callback)
        else: # far-future action
            self.distantactions.add({'millis':millis, 'cb':callback})
            
        
    def on_tick(self, event):
        """ """
        self.frameoverflow += event.duration
        
        while self.frameoverflow >= self.timestep: #current frame's time is over
            # call this frame's entities
            for callback in self.actionq[self.actioncursor]:
                callback()
            
            # done with all entities for this frame    
            self.actionq[self.actioncursor].clear()
            
            # last frame of the queue: add distant events if they need to
            if self.actioncursor == len(self.actionq) - 1:
                self.actioncursor = 0
                # set aside the far-future actions
                oldcbs = self.distantactions
                self.distantactions.clear()
                # try to insert all the far-future actions in actionq
                for item in oldcbs:
                    millis, cb = item.millis, item.cb
                    newmillis = millis - len(self.actionq) * self.timestep
                    self.add_action(newmillis, cb)
            
            else: #usual frame
                self.actioncursor += 1
            
            self.frameoverflow -= self.timestep
            
            
            
#############################################################################


class Creep():
    
    def __init__(self, evManager, aidir, creepid):
        """ Default state is idle. Move in 500ms. """
        self._em = evManager
        self.aidir = aidir
        self.creepid = creepid
        
        self.state = 'idle'
        self.cell = self.aidir.world.get_lair()
        self.aidir.add_action(500, self.update) # trigger a move in 500 ms
        self._em.post(SBroadcastCreepArrivedEvent(self.creepid))


    def update(self):
        """ Handle creep's state machine and comm with AI director. """
        if self.state == 'idle': # Dummy: Always move to a random neighbor cell. TODO: Could also attack.
            cell = random.choice(self.cell.get_neighbors())
            self.move(cell)
            self.state = 'moving'
            self.aidir.add_action(1000, self.update) # movement lasts for 1000 ms
        
        elif self.state == 'moving': # Dummy: after-move-delay
            self.state = 'idle'
            self.aidir.add_action(200, self.update) # pretend to 'think' for 200 ms
        
        
    def move(self, cell):
        self.cell = cell
        self._em.post(SBroadcastCreepMoveEvent(self.creepid, self.cell.coords))
