from collections import defaultdict
from common.constants import DIRECTION_LEFT
from common.events import TickEvent
from server.events_server import SBroadcastCreepArrivedEvent, SBcCreepMoveEvent, \
    SBcCreepDiedEvent
from uuid import uuid4
import logging
        
class AiDirector():

    log = logging.getLogger('server')

    
    def __init__(self, evManager, world):

        self._em = evManager
        self._em.reg_cb(TickEvent, self.on_tick)

        self.world = world
        
        self.creeps = dict()
        
        # action frames and delays
        self.timestep = 100 #in milliseconds; means that AI logic runs at 10Hz
        self.isrunning = False
        
        
        
    def buildpath(self):  
        """ starting from entrance (d=0) assign d+1 recursively to neighbor cells as the cell's distance to entrance """
        def recursive_dist_fill(cell, d):
            assert(cell.is_walkable()) #if cell is not walkable, it should not be reached by the algorithm
            if(cell.get_dist_from_entrance() > d):
                cell.set_dist_from_entrance(d)
                for neighborcell in self._get_adjacent_walkable_cells(cell):
                    recursive_dist_fill(neighborcell, d + 1)
            return
        recursive_dist_fill(self.cellgrid(self.get_entrance_coords()), 0)
        return
    
    
    
    def start(self):
        """ activate the AI director """
                 
        self.frameoverflow = 0 #how much time overflowed from previous frame
        # when overflow > timestep, we should increase the cursor to the next frame(s) 
        
        # Each frame of actionframes contains a mapping actor->callback(s) 
        self.actionframes = [defaultdict(list) for x in range(5)] # each slot for a timestep  
        self.actioncursor = 0 #loops over the actionframes
        
        # actions so distant in the future that they dont fit in actionframes
        self.distantactions = defaultdict(list) 
        
        # create dummy creeps
        for x in range(1):
            cname = str(uuid4())
            creep = Creep(self._em, self, cname, DIRECTION_LEFT) #face right
            self.creeps[cname] = creep
            
        self.isrunning = True
        
        
        
    def stop(self):
        self.isrunning = False
        self.creeps.clear()
        
        
        
    def schedule_action(self, millis, actor, callback):
        """ Add an entity's callback to be called in millis +/- timestep ms."""
        if millis < len(self.actionframes) * self.timestep:
            # if millis < timestep, schedule for next frame (not this current frame)
            index = self.actioncursor + max(1, int(millis / self.timestep))
            index = index % len(self.actionframes)            
            frame = self.actionframes[index]
            frame[actor].append(callback)
                
        else: # adding far-future actions should happen rarely
            # so it's OK if it costs a tiny bit
            timed_cb = millis, callback
            self.distantactions[actor].append(timed_cb)
    
    def unschedule_actor(self, actor):
        """ Remove the actor's actions from the current actionframes 
        and from the distant actions.
        """
        for frame in self.actionframes:
            frame.pop(actor, None) #remove actor's actions from the frame
        self.distantactions.pop(actor, None) # None prevents raising a KeyError if not found
        
        
        
    def on_tick(self, event):
        """ Iterate over the near-future frames (= actionframes). 
        When reaching the last frame, 
        try to schedule the distant-future actions within the near-future frames,
        and restart iterating at the beginning of the near-future frames.
        """
        
        if not self.isrunning: # when turned off, dont do anything
            return
        
        self.frameoverflow += event.duration
        
        while self.frameoverflow >= self.timestep: #current frame's time is over
            
            # call the callbacks scheduled for this frame;
            # frame is a dict of (actor, callbacks for this actor)
            frame = self.actionframes[self.actioncursor]
            while frame: # until frame is empty dict
                actor, callbacks = frame.popitem() # pick a random (actor, callbacks) 
                for cb in callbacks: # call all the callbacks for that actor
                    cb()
            # now, frame is empty
            
            
            # last frame of the near-future: add far-future actions if they fit
            if self.actioncursor == len(self.actionframes) - 1:
                self.actioncursor = 0
                
                # set aside the far-future actions
                oldcbs = self.distantactions.copy()
                self.distantactions.clear()
                
                # try to insert all the far-future actions in the near-future frames
                for actor, timed_cbs in oldcbs.items():
                    for millis, cb in timed_cbs:
                        newmillis = millis - len(self.actionframes) * self.timestep
                        self.schedule_action(newmillis, actor, cb)
            
            else: #usual near-future frame
                self.actioncursor += 1
            
            self.frameoverflow -= self.timestep
            
            
            
    def rmv_creep(self, creep):
        """ Remove a creep who died. """
        cname = creep.cname
        
        try:
            self.unschedule_actor(cname)
            del self.creeps[cname]
            ev = SBcCreepDiedEvent(cname)
            self._em.post(ev)
        except KeyError:
            self.log.warning('Tried to remove creep %s but failed.' % (cname))
        
        
        
#############################################################################


class Creep():
        
    def __init__(self, evManager, aidir, cname, facing):
        """ Default state is idle. Move in 500ms. """
        self._em = evManager
        self.aidir = aidir
        
        self.cname = cname
        self.cell = self.aidir.world.get_lair()
        self.facing = facing # direction the creep is facing when created

        self.state = 'idle'
        self.hp = 10 # TODO: hardcoded
                
        self.aidir.schedule_action(500, self.cname, self.update) # trigger a move in 500 ms
        ev = SBroadcastCreepArrivedEvent(self.cname, self.cell.coords, self.facing)
        self._em.post(ev)


    def __str__(self):
        return '<Creep %s %s>' % (self.cname, id(self))


    def update(self):
        """ Handle creep's state machine and comm with AI director. """
        if self.state == 'idle': 
            # Dummy: Always move to a random neighbor cell. TODO: Could also attack.
            #cell = random.choice(self.cell.get_neighbors())
            cell = self.cell.get_nextcell_inpath()
            self.move(cell)
            self.state = 'moving'
            mvtduration = 100 
            self.aidir.schedule_action(mvtduration, self.cname, self.update) 
        
        elif self.state == 'moving': # Dummy: after-move-delay
            self.state = 'idle'
            #duration = random.randint(2, 12) * 100# pretend to 'think' for 200-1200 ms
            duration = 2000 # think for 2 secs
            self.aidir.schedule_action(duration, self.cname, self.update) 

        
    def move(self, cell):
        """ move the creep to the given cell. """
        self.cell = cell
        ev = SBcCreepMoveEvent(self.cname, self.cell.coords, self.facing)
        self._em.post(ev)
        
        
    def rcv_atk(self, atk):
        """ when a player attacks, take damage. """
        self.hp -= atk 
        
        # TODO: should atk be reduced by def in 1) percentage or 2) absolute value?
        if self.hp <= 0:
            self.die()
        return atk
    
    
    def die(self):
        """ when a creep dies. """
        self.aidir.rmv_creep(self)
