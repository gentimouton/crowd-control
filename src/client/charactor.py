from client.events_client import RemoteCharactorMoveEvent, CharactorRcvDmgEvt, \
    CharactorRemoveEvent
import logging

class Charactor():
    """ A local or remote entity representing players or creeps. 
    It is located on a cell, and can move to another cell.
    """
    
    log = logging.getLogger('client')

    def __init__(self, cell, facing, name, atk, hp, evManager):
        self._em = evManager
        
        self.name = name
        
        self.facing = facing # which direction the charactor is facing        
        self.cell = cell
        self.cell.add_occ(self) # need to have self.cname fixed
        
        self.atk = atk
        self.hp = hp
        
      
    def __str__(self):
        return '%s at %s, %d hp' % (self.name, self.cell.coords, self.hp)
              

    def changename(self, newname):
        """ Update my name. """
        self.name = newname
        
        
    def move_absolute(self, destcell):
        """ move to the specified destination.
        During a split second, the charactor is in no cell. 
        """ 
        if destcell:
            self.cell.rm_occ(self)
            self.cell = destcell
            self.cell.add_occ(self)
            ev = RemoteCharactorMoveEvent(self, destcell.coords)
            self._em.post(ev)
            
        else: #illegal move
            self.log.warning('Illegal move from ' + self.name)
            #TODO: FT should report to server of potential cheat/hack
            pass
        
        
    def rcv_dmg(self, dmg):
        """ Receive damage: notify the view to update the display. """
        self.hp -= dmg
        # no need to check if hp < 0: death comes from the server only 
        ev = CharactorRcvDmgEvt(self, dmg)
        self._em.post(ev)
        
        
    def rmv(self):
        """ tell the view to remove this charactor's spr """ 
        if self.cell:
            self.cell.rm_occ(self) # TODO: FT should be a weakref instead?
        ev = CharactorRemoveEvent(self)
        self._em.post(ev)

 
        
        
        
        
