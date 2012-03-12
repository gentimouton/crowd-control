from client.charactor import Charactor
from client.events_client import LocalAvatarPlaceEvent, OtherAvatarPlaceEvent, \
    SendMoveEvt, SendAtkEvt, RemoteCharactorMoveEvent, LocalAvRezEvt
from random import randint



    
    
class Avatar(Charactor):
    """ An entity controlled by a player.
    Right now, the mapping is 1-to-1: one avatar per player. 
    """
    
    def __init__(self, name, cell, facing, atk, hp, islocal, evManager):
        
        Charactor.__init__(self, cell, facing, name, atk, hp, evManager)
        
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
            self.cell.rm_occ(self)
            self.cell = dest_cell
            self.cell.add_occ(self)
            self.facing = direction
            # send to view and server that I moved
            ev = SendMoveEvt(self, dest_cell.coords, direction)
            self._em.post(ev)

        else: #move is not possible: TODO: FT give (audio?) feedback 
            pass 

    
    def atk_local(self):
        """ Attack a charactor in the vicinity, 
        and send action + amount of damage to the server. 
        """
        target_cell = self.cell.get_adjacent_cell(self.facing)
        if target_cell: #only attack walkable cells
            occs = target_cell.get_occs()
            if occs:
                # pick an occupant randomly (could be a player or a creep)
                occ = occs[randint(0, len(occs) - 1)]
                occ.rcv_dmg(self.atk)
                self.log.info('Local: I atk %s for %d dmg' % (occ.name, self.atk))
                ev = SendAtkEvt(occ.name, self.atk) 
                self._em.post(ev)
            else:# dont attack if the cell has no occupant
                pass # TODO: FT show a 'miss' animation
        

       
    def resurrect(self, newcell, facing, hp, atk):
        """ resurrect charactor: update it from the given char info. """
        # move to new cell if possible
        if newcell:
            self.cell.rm_occ(self)
            self.cell = newcell
            self.cell.add_occ(self)
            ev = RemoteCharactorMoveEvent(self, newcell.coords)
            self._em.post(ev)
            if self.islocal: # notify the view
                ev = LocalAvRezEvt(self)
                self._em.post(ev)
        else: # cell non walkable or out of map  
            self.log.warn('%s should have resurrected, but cell not found.'
                          % self.name)
        
        # update other attributes
        self.facing = facing
        self.hp = hp
        self.atk = atk

        