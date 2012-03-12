from server.charactor import Charactor
import logging


class SCreep(Charactor):
    
    log = logging.getLogger('server')

    
    def __init__(self, mdl, sched, nw, cname, cell, facing):
        """ Starting state is idle. """
        Charactor.__init__(self, cname, cell, facing, 10, 6) # 10 HP, 6 atk
        
        self._mdl = mdl
        self._sched = sched     
        self._nw = nw           
        self._sched.schedule_action(500, self.name, self.update) # trigger a move in 500 ms
        
        self.state = 'idle'
        
        creepinfo = self.serialize()
        self._nw.bc_creepjoin(self.name, creepinfo)


    
    #################### OVERRIDES FROM CHARACTOR ############################
     
    
    def move(self, newcell, facing):
        """ move the creep to the given cell. """
        # remove from old cell and add to new cell
        oldcell = self.cell
        oldcell.rm_occ(self)
        newcell.add_occ(self)
        self.cell = newcell
        self.facing = facing
        self._nw.bc_move(self.name, newcell.coords, facing)
        

    def attack(self, defer):
        """ Attack a target (avatar or creep).
        No need to check if target is in range: update() did it. 
        """
        dmg = defer.rcv_dmg(self, self.atk) # takes care of broadcasting on network 
        return dmg
        
        
    def rcv_dmg(self, atker, dmg):
        """ Receive damage from an attacker. Return amount of dmg received. """
        self.hp -= dmg
        self.log.debug('Creep %s received %d dmg from %s' 
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
        
        #if creep has to do something when it dies, 
        #it should do it before having the model remove it
        self._mdl.rmv_creep(self.name)
        
        # broadcast on network
        self._nw.bc_death(self.name)
        
    



    ##################### STATE MACHINE ###############################
    
    def update(self):
        """ Handle creep's state machine and comm with AI director. """
        if self.state == 'idle': 
            # TODO: Make an AI config for each creep behavior.
            #cell = random.choice(self.cell.get_neighbors())
            # move to a neighbor cell closer to the map entrance
            direction, cell = self.cell.get_nextcell_inpath()
            occupant = cell.get_occ()
            if occupant: # TODO: should only get *players* in that cell instead.. 
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

        
    
