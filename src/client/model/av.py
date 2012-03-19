from client.model.charactor import Charactor
from client.events_client import LocalAvatarPlaceEvent, OtherAvatarPlaceEvent, \
    SendMoveEvt, SendAtkEvt, LocalAvRezEvt, CharactorDeathEvt, RemoteCharactorRezEvt, \
    RemoteCharactorMoveEvent, CharactorRemoveEvent, ChangedMoveSpeedEvt
from random import randint
from time import time
import logging



log = logging.getLogger('client')
    
    
class Avatar(Charactor):
    """ An entity controlled by a player. One avatar per player. """
            
    def __init__(self, name, cell, facing, atk, hp, move_cd, islocal, evManager):
        
        Charactor.__init__(self, cell, facing, name, atk, hp, evManager)
           
        self.cell = cell
        self.cell.add_av(self)
        
        self.islocal = islocal #whether the avatar is controlled by the client
        
        if islocal:
            # dont limit the speed of remote avatars  
            self.move_ts = time() # timestamp of last movement
            self.move_cd = move_cd # cooldown of movement, in millis; 
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
            ev = SendAtkEvt(target, target.name, self.atk) 
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
        self.cell = None
        ev = CharactorDeathEvt(self)
        self._em.post(ev)
        
    
    def rmv(self):
        """ tell the view to remove this charactor's spr """ 
        if self.cell:
            self.cell.rm_av(self) # TODO: FT should be a weakref instead?
        ev = CharactorRemoveEvent(self)
        self._em.post(ev)
        

    ############  move  ###########################
    
    
    def move_relative(self, direction, strafing):
        """ If possible, start moving towards that direction 
        (change facing first, then start changing cell). 
        If not, only change facing.
        If strafing is True, move without changing facing.
        """
        
        # check that move cooldown is over 
        now = time()
        move_delay = (now - self.move_ts) * 1000
        if move_delay < self.move_cd:
            return # if still in cooldown, dont do anything
        
        dest_cell = self.cell.get_adjacent_cell(direction) # None if non-walkable
        
        if strafing: 
            if dest_cell: # walkable: move to cell without changing facing 
                self.cell.rm_av(self)
                self.cell = dest_cell
                self.cell.add_av(self)
            else: # strafing to non-walkable cell == not moving at all
                return # dont send a move event
        
        else: # no strafing
            if self.facing == direction: # if facing dest,
                if dest_cell: # and dest is walkable, then move to it
                    self.cell.rm_av(self)
                    self.cell = dest_cell
                    self.cell.add_av(self)
                else: # dest is not walkable: pushing the wall is not moving 
                    return # dont send a move event
            else: # only change dir
                self.facing = direction                
        
        self.move_ts = now
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
            
    
    def update_movespeed(self, move_cd, move_txt):
        """ Update the move cooldown of the avatar. 
        Only useful for local av. Dont send any event if cooldown unchanged. 
        """
        
        if self.islocal:
            self.move_cd = move_cd
            ev = ChangedMoveSpeedEvt(move_txt)
            self._em.post(ev)
    
    
    ##################  resurrect  #######################
               
    def resurrect(self, newcell, facing, hp, atk, move_cd, move_txt):
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
            # update move speed only if different from before death
            if self.move_cd != move_cd:
                self.update_movespeed(move_cd, move_txt)
        else: # remote avatar
            ev = RemoteCharactorRezEvt(self) # self stores the new position
            self._em.post(ev)
                
