from common.constants import DIRECTION_LEFT
from server.charactor import SCharactor
import logging


class SCreep(SCharactor):
    
    log = logging.getLogger('server')

    
    def __init__(self, mdl, sched, nw, cname, cell, facing):
        """ Starting state is idle. """
        SCharactor.__init__(self, cname, cell, facing, 10, 6) # 10 HP, 6 atk
        #self.cell.add_occ(self) # TODO: cell.add_creep, cell.add_player, ...
        # so that creeps can do cell.get_players and attack one
        
        self._mdl = mdl
        self._sched = sched     
        self._nw = nw           
        self._sched.schedule_action(500, self.name, self.update) # trigger a move in 500 ms
        
        self.state = 'idle'
        
        self._nw.bc_creepjoin(self.name, self.cell.coords, self.facing)


    
    #################### OVERRIDES FROM CHARACTOR ############################
     
    
    def move(self, cell, facing=DIRECTION_LEFT): # TODO: facing should always be specified, not DIR_LEFT 
        """ move the creep to the given cell. """
        self.cell = cell
        self.facing = facing
        self._nw.bc_creepmoved(self.name, self.cell.coords, facing)
        
        
    def rcv_atk(self, atker):
        """ when a player attacks, take damage. 
        Return the amount of dmg received. 
        """
        dmg = atker.atk # TODO: should be reduced by self.def or self.armor
        self.hp -= dmg
        self.log.debug('Creep %s received %d dmg' % (self.name, dmg))
        
        self._nw.bc_atk(atker.name, self.name, dmg)

        # less than 0 HP => death
        if self.hp <= 0:
            self.die()
        
        return dmg
        
            
    
    def die(self):
        """ Notify all players when a creep dies. """
        self._sched.unschedule_actor(self.name)
        #if creep explodes, it should do so before having the model remove it
        self._mdl.rmv_creep(self.name)
        # broadcast on network
        self._nw.bc_creepdied(self.name)
        
    
    def attack(self, defer):
        """ Attack a target.
        No need to check if target is in range: update() did it. 
        """
        return defer.rcv_atk(self)
        



    ##################### STATE MACHINE ###############################
    
    def update(self):
        """ Handle creep's state machine and comm with AI director. """
        if self.state == 'idle': 
            # TODO: Make an AI config for each creep behavior.
            #cell = random.choice(self.cell.get_neighbors())
            # move to a neighbor cell closer to the map entrance
            direction, cell = self.cell.get_nextcell_inpath()
            occupant = cell.get_occ()
            if occupant: # TODO: should only get players in that cell instead.. 
                self.attack(occupant)
                self.state = 'atking'
                atkduration = 200
                self._sched.schedule_action(atkduration, self.name, self.update) 
            else: # move if no one in next cell
                self.move(cell, direction) 
                self.state = 'moving'
                mvtduration = 100 
                self._sched.schedule_action(mvtduration, self.name, self.update) 
        
        elif self.state == 'moving': # Dummy: after-move-delay
            self.state = 'idle'
            #duration = random.randint(2, 12) * 100# pretend to 'think' for 200-1200 ms
            duration = 2000 # think for 2 secs
            self._sched.schedule_action(duration, self.name, self.update) 

        elif self.state == 'atking': # Dummy: after-atk-delay
            self.state = 'idle'
            duration = 2000 # acd of 2 secs
            self._sched.schedule_action(duration, self.name, self.update) 

        
    
