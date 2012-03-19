from client.model.av import Charactor
from client.events_client import CreepPlaceEvent, RemoteCharactorMoveEvent, \
    CharactorRemoveEvent

class Creep(Charactor):
    """ Representation of a remote enemy monster. """
        
    def __init__(self, evManager, cname, cell, facing, atk, hp):
        
        Charactor.__init__(self, cell, facing, cname, atk, hp, evManager)
        
        # place in cell
        self.cell = cell
        self.cell.add_creep(self)
        
        ev = CreepPlaceEvent(self)# ask view to display the new creep
        self._em.post(ev)
    
          
    def move_absolute(self, destcell, facing):
        """ move to the specified destination. """
        
        self.facing = facing
 
        if destcell:
            self.cell.rm_creep(self)
            self.cell = destcell
            self.cell.add_creep(self)
            ev = RemoteCharactorMoveEvent(self)
            self._em.post(ev)
            
        else: #ignore illegal creep moves
            pass # because most likely due to lag or missed packets
        
        
    def die(self):
        """ kill a creep: just remove it for now. """
        self.rmv()
        
    
    def rmv(self):
        """ tell the view to remove this charactor's spr """ 
        if self.cell:
            self.cell.rm_creep(self) # TODO: FT should be a weakref instead?
        ev = CharactorRemoveEvent(self)
        self._em.post(ev)
        
        