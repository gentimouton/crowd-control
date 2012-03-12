from client.av import Charactor
from client.events_client import CreepPlaceEvent

class Creep(Charactor):
    """ Representation of a remote enemy monster. """
        
    def __init__(self, evManager, cname, cell, facing, atk, hp):
        
        Charactor.__init__(self, cell, facing, cname, atk, hp, evManager)
        
        ev = CreepPlaceEvent(self)# ask view to display the new creep
        self._em.post(ev)
        
    