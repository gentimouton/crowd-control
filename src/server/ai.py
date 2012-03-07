from collections import defaultdict
from common.constants import DIRECTION_LEFT
from common.events import TickEvent
from server.charactor import SCharactor
from server.config import config_get_aifps, config_get_ailatentframes
from server.events_server import SBcCreepArrivedEvent, SBcCreepMovedEvent, \
    SBcCreepDiedEvent, SBcAtkEvent, SCreepAtkEvent
from uuid import uuid4
import logging



class AiDirector():
    """ Created when server starts, 
    started by player command,
    stopped by player command or gameover.
    """
    
    log = logging.getLogger('server')

    
    def __init__(self, evManager, world):

        self._em = evManager
        self._em.reg_cb(TickEvent, self.on_tick)

        self.world = world
        
        self.creeps = dict()
        
        # action frames and delays
        self.timestep = int(1000 / config_get_aifps()) # in milliseconds
        self.isrunning = False
        
        
    
    
    def start(self):
        """ activate the AI director """
                 
        self.frameoverflow = 0 #how much time overflowed from previous frame
        # when overflow > timestep, we should increase the cursor to the next frame(s) 
        
        # Each frame of actionframes contains a mapping actor->callback(s)
        num_frames = config_get_ailatentframes()
        self.actionframes = [defaultdict(list) for x in range(num_frames)] # each slot for a timestep  
        self.actioncursor = 0 #loops over the actionframes
        
        # actions so distant in the future that they dont fit in actionframes
        self.distantactions = defaultdict(list) 
        
        # create dummy creeps
        cell = self.world.get_lair()
        for x in range(1):
            cname = str(uuid4())
            creep = SCreep(self._em, self, cname, cell, DIRECTION_LEFT) #face left
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
            
            
    def get_creeps(self):
        """ Return an iterable of all creeps. """
        return self.creeps
    
    
    def get_creep(self, cname):
        """ return the creep with that name. 
        Return None if not found. 
        """
        try: 
            return self.creeps[cname]
        except KeyError: # creep not found
            self.log.error("Creep %s not found" % cname)
            return None
        
         
    def rmv_creep(self, creep):
        """ Remove a creep who died. """
        cname = creep.name
        
        try:
            self.unschedule_actor(cname)
            del self.creeps[cname]
        except KeyError:
            self.log.warning('Tried to remove creep %s but failed.' % (cname))
        
        
        
#############################################################################


class SCreep(SCharactor):
    
    log = logging.getLogger('server')

    
    def __init__(self, evManager, aidir, cname, cell, facing):
        """ Starting state is idle. """
        SCharactor.__init__(self, cname, cell, facing, 10, 6) # 10 HP, 6 atk
        #self.cell.add_occ(self) # TODO: cell.add_creep, cell.add_player, ...
        # so that creeps can do cell.get_players and attack one
        
        self._em = evManager
        self.aidir = aidir                
        self.aidir.schedule_action(500, self.name, self.update) # trigger a move in 500 ms
        
        self.state = 'idle'
        
        ev = SBcCreepArrivedEvent(self.name, self.cell.coords, self.facing)
        self._em.post(ev)


    def __str__(self):
        args = self.name, str(self.cell.coord), self.hp, id(self)
        return '<SCreep %s at %s, hp=%d, id=%s>' % args

    
    #################### OVERRIDES FROM CHARACTOR ############################
     
    
    def move(self, cell, facing=DIRECTION_LEFT):
        """ move the creep to the given cell. """
        self.cell = cell
        self.facing = facing
        ev = SBcCreepMovedEvent(self.name, self.cell.coords, facing)
        self._em.post(ev)
        
        
    def rcv_atk(self, atker):
        """ when a player attacks, take damage. """
        dmg = atker.atk # TODO: should be reduced by self.def or self.armor
        self.hp -= dmg
        self.log.debug('Creep %s received %d dmg' % (self.name, dmg))
        
        ev = SBcAtkEvent(atker.name, self.name, dmg)
        self._em.post(ev)
        
        # less than 0 HP => death
        if self.hp <= 0:
            self.die()
            
    
    def die(self):
        """ Notify all players when a creep dies. """
        self.aidir.rmv_creep(self)
        ev = SBcCreepDiedEvent(self.name)
        self._em.post(ev)
        
    
    def attack(self, defer):
        """ Notify model of creep attack. """
        # TODO: why is creep death direct network broadcast, 
        # but creep atk goes through model?
        ev = SCreepAtkEvent(self.name, defer, self.atk)
        self._em.post(ev)




    ##################### STATE MACHINE ###############################
    
    def update(self):
        """ Handle creep's state machine and comm with AI director. """
        if self.state == 'idle': 
            # Dummy: Always move to a random neighbor cell. 
            # TODO: Make an AI config for each creep behavior.
            #cell = random.choice(self.cell.get_neighbors())
            direction, cell = self.cell.get_nextcell_inpath()
            occupant = cell.get_occ()
            if occupant: # TOOD: this attacks other creeps. 
                # TODO: should check for players in that cell instead.
                self.attack(occupant)
                self.state = 'atking'
                atkduration = 10000
                self.aidir.schedule_action(atkduration, self.name, self.update) 
            else: # move if no one in next cell
                self.move(cell, direction) 
                self.state = 'moving'
                mvtduration = 100 
                self.aidir.schedule_action(mvtduration, self.name, self.update) 
        
        elif self.state == 'moving': # Dummy: after-move-delay
            self.state = 'idle'
            #duration = random.randint(2, 12) * 100# pretend to 'think' for 200-1200 ms
            duration = 2000 # think for 2 secs
            self.aidir.schedule_action(duration, self.name, self.update) 

        elif self.state == 'atking': # Dummy: after-atk-delay
            self.state = 'idle'
            duration = 2000 # acd of 2 secs
            self.aidir.schedule_action(duration, self.name, self.update) 

        
    
