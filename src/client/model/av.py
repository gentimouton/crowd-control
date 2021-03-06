from client.events_client import LocalAvatarPlaceEvent, OtherAvatarPlaceEvent, \
    SendMoveEvt, SendAtkEvt, LocalAvRezEvt, CharactorDeathEvt, RemoteCharactorRezEvt, \
    RemoteCharactorMoveEvent, CharactorRemoveEvent, SendSkillEvt, LocalDmgsEvt
from client.model.charactor import Charactor
from random import randint
from time import time
import logging



log = logging.getLogger('client')
    
    
class Avatar(Charactor):
    """ An entity controlled by a player. One avatar per player. """
            
    def __init__(self, name, cell, facing, atk, hp, maxhp, atk_cd, islocal, evManager):
        
        Charactor.__init__(self, cell, facing, name, atk, hp, maxhp, evManager)
           
        self.cell = cell
        self.cell.add_av(self)
        
        self.islocal = islocal #whether the avatar is controlled by the client
        
        if islocal:
            # dont limit the speed of remote avatars  
            self.atk_ts = time() # timestamp of last movement
            self.atk_cd = atk_cd # cooldown of movement, in millis; 
            ev = LocalAvatarPlaceEvent(self, cell)
        else: #avatar from someone else
            ev = OtherAvatarPlaceEvent(self, cell)
        self._em.post(ev)
        

    def __str__(self):
        return '%s, hp=%d' % (self.name, self.hp)
    
    
    
    ###################  attack  #####################
    
    def atk_local(self):
        """ Attack a charactor in a cell nearby, 
        and send action + amount of damage to the server.
        Dont update locally/dead-reckon the target: 
        it will be updated by the server reply. 
        """
        
        target = self.get_target()
        if target: # found a target
            # send the atk event to the server
            # and notify the view to display the dmg
            dmg = self.atk # TODO: minus target def
            # notify view
            dmgs = {target: dmg}
            ev = LocalDmgsEvt(dmgs)
            self._em.post(ev)
            # send on nw
            ev = SendAtkEvt(target.name, dmg) 
            self._em.post(ev)
        
        else:
            pass # TODO: FT display a "miss"
        
        
    def get_target(self):
        """ return a creep in the cell the avatar is facing. """
        
        target_cell = self.cell.get_adjacent_cell(self.facing)
            
        if target_cell: #only attack walkable cells
            targets = target_cell.get_creeps()
            if targets: # pick a random target from the list (could be the weakest)
                target = targets[randint(0, len(targets) - 1)]
                return target
        return None



    ######################  death  #################

    def die(self):
        """ kill an avatar: hide it until the server resurrects it. """
        
        self.cell.rm_av(self) # TODO: FT should be a weakref instead?
        ev = CharactorDeathEvt(self)
        self._em.post(ev)
        
    
    def rmv(self):
        """ tell the view to remove this charactor's spr """ 
        self.cell.rm_av(self) # TODO: FT should be a weakref instead?
        ev = CharactorRemoveEvent(self)
        self._em.post(ev)
        

    ############  move  ###########################
    
    
    def move_relative(self, direction, strafing, rotating):
        """ If possible, start moving towards that direction 
        (change facing first, then start changing cell). 
        If not, only change facing.
        If strafing is True, move without changing facing; move cooldown.
        If strafing is False and rotating True, change facing without moving.
        Rotating has no cooldown.
        """
        
        dest_cell = self.cell.get_adjacent_cell(direction) # None if non-walkable
        
        if strafing: 
            if dest_cell: # walkable: move to cell without changing facing
                self.cell.rm_av(self)
                self.cell = dest_cell
                self.cell.add_av(self)
            else: # strafing to non-walkable cell == not moving at all
                return # dont send a move event
        
        elif rotating:
            if self.facing != direction: # do nothing if rotating to current direction
                self.facing = direction
            
        else: # no strafing and no rotating
            if dest_cell: # and dest is walkable, 
                # then walk
                self.cell.rm_av(self)
                self.cell = dest_cell
                self.cell.add_av(self)
                self.facing = direction
                #self.move_ts = now
            elif self.facing != direction: # turn while facing a wall
                self.facing = direction # then change facing
            else: # if same facing as before, do nothing
                return 
                
                
        # send to view and server that I moved
        ev = SendMoveEvt(self, self.cell.coords, self.facing)
        self._em.post(ev)

          
    def move_absolute(self, destcell, facing):
        """ move to the specified destination with the given facing. """ 
        
        self.facing = facing
        
        if destcell:
            self.cell.rm_av(self)
            self.cell = destcell
            self.cell.add_av(self)
            ev = RemoteCharactorMoveEvent(self)
            self._em.post(ev)
            
        else: #illegal move
            log.debug('Illegal move from ' + self.name)
            #TODO: FT should report to server of potential cheat/hack
            
    
    
    
    ##################  resurrect  #######################
               
    def resurrect(self, newcell, facing, hp, atk):
        """ resurrect charactor: update it from the given char info. """
        
        self.facing = facing
        self.hp = hp
        self.atk = atk
    
        # update location
        # no need to rm_occ because die() removed me already from my cell
        self.cell = newcell
        self.cell.add_av(self)
        
        if self.islocal: # notify the view if I just resurrected
            ev = LocalAvRezEvt(self)
            self._em.post(ev)
        else: # remote avatar
            ev = RemoteCharactorRezEvt(self) # self stores the new position
            self._em.post(ev)
                


    ######################  skill  #################

    def localcast_burst(self):
        """ Cast the skill 'burst' locally.  
        Display animation and damage locally, 
        but the model update will come from a server msg. 
        """
        
        creeps_dmgs = self._get_bursted_creeps()
        ev = LocalDmgsEvt(creeps_dmgs)
        self._em.post(ev)
        
        # send over the network
        ev = SendSkillEvt('burst')
        self._em.post(ev)


    def remotecast_burst(self):
        """ Server said a remote char casted the skill burst.
        Update the model.
        If another char casted the skill, display the dmg.
        """

        fromremotechar = not self.islocal
        creeps_dmgs = self._get_bursted_creeps()
        
        # model update - actual dmg will be computed by the charactor
        for creep in creeps_dmgs.keys():
            creep.rcv_dmg(self.atk, fromremotechar)
        
    
    def _get_bursted_creeps(self):
        """ Burst inflicts 100% atk on all creeps in neighbor+current cells.
        """
              
        cells = self.cell.get_neighbors() # distance = 1 from current cell
        cells.append(self.cell) # also attack the current cell
        creeps_dmgs = {} # {creep:dmg}
        for cell in cells:
            for creep in cell.get_creeps():
                dmg = self.atk # TODO: minus creep.def
                creeps_dmgs[creep] = dmg
                
        return creeps_dmgs
                