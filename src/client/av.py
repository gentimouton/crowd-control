from client.charactor import Charactor
from client.events_client import LocalAvatarPlaceEvent, OtherAvatarPlaceEvent, \
    SendMoveEvt, SendAtkEvt, LocalAvRezEvt, CharactorDeathEvt, RemoteCharactorRezEvt, \
    RemoteCharactorMoveEvent, CharactorRemoveEvent
from random import randint



    
    
class Avatar(Charactor):
    """ An entity controlled by a player.
    Right now, the mapping is 1-to-1: one avatar per player. 
    """
    
    def __init__(self, name, cell, facing, atk, hp, islocal, evManager):
        
        Charactor.__init__(self, cell, facing, name, atk, hp, evManager)
           
        self.cell = cell
        self.cell.add_av(self)
        
        self.islocal = islocal #whether the avatar is controlled by the client
        
        if islocal:
            ev = LocalAvatarPlaceEvent(self, cell)
        else: #avatar from someone else
            ev = OtherAvatarPlaceEvent(self, cell)
        self._em.post(ev)
        

    def __str__(self):
        return '%s, hp=%d' % (self.name, self.hp)
    
    
    def move_relative(self, direction):
        """ If possible, move towards that direction. """

        dest_cell = self.cell.get_adjacent_cell(direction)
        if dest_cell:
            self.cell.rm_av(self)
            self.cell = dest_cell
            self.cell.add_av(self)
            self.facing = direction
        
            # send to view and server that I moved
            ev = SendMoveEvt(self, dest_cell.coords, direction)
            self._em.post(ev)

        else: #move is not possible: TODO: FT give (audio?) feedback 
            pass 

          
    def move_absolute(self, destcell):
        """ move to the specified destination.
        During a split second, the charactor is in no cell. 
        """ 
        if destcell:
            self.cell.rm_av(self)
            self.cell = destcell
            self.cell.add_av(self)
            ev = RemoteCharactorMoveEvent(self, destcell.coords)
            self._em.post(ev)
            
        else: #illegal move
            self.log.debug('Illegal move from ' + self.name)
            #TODO: FT should report to server of potential cheat/hack
            pass
        
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
            ev = SendAtkEvt(self, target, target.name, self.atk) 
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
        
           
    def resurrect(self, newcell, facing, hp, atk):
        """ resurrect charactor: update it from the given char info. """
        
        # move to new cell if possible
        if newcell:
            self.facing = facing
            self.hp = hp
            self.atk = atk
        
            # update location
            # no need to rm_occ because die() removed me already from my cell
            self.cell = newcell
            self.cell.add_av(self)
            ev = RemoteCharactorRezEvt(self) # self stores the new position
            self._em.post(ev)
            
            if self.islocal: # notify the view if I just resurrected
                ev = LocalAvRezEvt(self)
                self._em.post(ev)
                
        else: # cell non walkable or out of map  
            self.log.warn('%s should have resurrected, but cell not found.'
                          % self.name)
        

        
