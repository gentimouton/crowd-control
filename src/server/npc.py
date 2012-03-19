from random import randint
from server.charactor import SCharactor
from server.config import config_get_maxhp, config_get_baseatk
import logging

log = logging.getLogger('server')

class SCreep(SCharactor):

    def __init__(self, mdl, sched, nw, cname, cell, facing):
        """ Starting state is idle. """

        hp, atk = config_get_maxhp(), config_get_baseatk()
        SCharactor.__init__(self, cname, cell, facing, hp, atk)
        
        self.cell = cell
        self.cell.add_creep(self)
        
        self._mdl = mdl
        self._sched = sched
        self._nw = nw
        self._sched.schedule_action(500, self.name, self.update) # trigger a move in 500 ms
        
        self.state = 'idle'
        
        creepinfo = self.serialize()
        self._nw.bc_creepjoin(self.name, creepinfo)


    
    #################### OVERRIDES FROM CHARACTOR ############################
     
    
    def move(self, newcell, facing):
        """ move the creep to the given cell. 
        Return whether the creep should keep moving or not.
        The creep should stop moving when it reaches the entrance.
        """

        # remove from old cell and add to new cell
        oldcell = self.cell
        oldcell.rm_creep(self)
        newcell.add_creep(self)
        self.cell = newcell
        self.facing = facing
        self._nw.bc_move(self.name, newcell.coords, facing)
        
        # check if game over
        if newcell == self._mdl.world.get_entrance(): # TODO: FT ugly or not?
            self._mdl.stopgame(self.name)
            return False
        else:
            return True



    def get_target(self):
        """ return an avatar in the cell the creep is facing. """
        
        target_cell = self.cell.get_adjacent_cell(self.facing)
        if target_cell: #only attack walkable cells
            avs = target_cell.get_avs()
            if avs: # pick a random av
                av = avs[randint(0, len(avs) - 1)]
                return av
            
        return None



    def attack(self, defer):
        """ Attack a target (avatar or creep).
        No need to check if target is in range: update() did it. 
        """
        
        dmg = defer.rcv_dmg(self, self.atk) # takes care of broadcasting on network 
        return dmg
        
        
    def rcv_dmg(self, atker, dmg):
        """ Receive damage from an attacker. Return amount of dmg received. """
        
        self.hp -= dmg
        log.debug('Creep %s received %d dmg from %s' 
                  % (self.name, dmg, atker.name))
        self._nw.bc_attack(atker.name, self.name, dmg)

        # less than 0 HP => death
        if self.hp <= 0:
            self.die()
        
        return dmg
        
            
    
    def die(self):
        """ Notify all players when a creep dies. """
        
        # remove all scheduled actions
        self._sched.unschedule_actor(self.name)
        self.cell.rm_creep(self)
        
        #if creep has to do something when it dies, 
        #it should do it before having the model remove it
        self._mdl.rmv_creep(self.name)
        
        # broadcast on network
        self._nw.bc_death(self.name)
        
    


    ##################### STATE MACHINE ###############################
    
    def update(self):
        """ Handle creep's state machine and comm with AI director. """
        
        if self.state == 'idle': 
            # TODO: FT Make an AI config for each creep behavior.
            #cell = random.choice(self.cell.get_neighbors())
            # move to a neighbor cell closer to the map entrance
            direction, cell = self.cell.get_nextcell_inpath()
            target = self.get_target()
            
            if target: # only get players in that cell 
                self.attack(target)
                self.state = 'atking'
                atkduration = 200
                self._sched.schedule_action(atkduration, self.name, self.update) 
                
            else: # move if no one in next cell
                if self.move(cell, direction): # if I didn't reach the entrance
                    self.state = 'moving'
                    mvtduration = 100 
                    self._sched.schedule_action(mvtduration, self.name, self.update) 
                else: # reached entrance
                    return
                
        elif self.state == 'moving': # Dummy: after-move-delay
            self.state = 'idle'
            #duration = random.randint(2, 12) * 100# pretend to 'think' for 200-1200 ms
            duration = 1000 # think for 1 sec
            self._sched.schedule_action(duration, self.name, self.update) 

        elif self.state == 'atking': # Dummy: after-atk-delay
            self.state = 'idle'
            duration = 1000 # acd of 1 sec
            self._sched.schedule_action(duration, self.name, self.update) 

        
    
