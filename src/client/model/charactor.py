from client.events_client import CharactorRcvDmgEvt

class Charactor():
    """ A local or remote entity representing players or creeps. 
    It is located on a cell, and can move to another cell.
    """
    
    def __init__(self, cell, facing, name, atk, hp, evManager):
        self._em = evManager
        
        self.name = name
        
        self.facing = facing # which direction the charactor is facing     
        
        self.atk = atk
        self.hp = hp
        
      
    def __str__(self):
        return '%s at %s, %d hp' % (self.name, self.cell.coords, self.hp)
              

    def changename(self, newname):
        """ Update my name. """
        
        self.name = newname
        
        
        
    def rcv_dmg(self, dmg, fromremotechar):
        """ Receive damage: notify the view to update the display. 
        fromremotechar = whether the attack originates from another char or not.
        """
        
        self.hp -= dmg
        # no need to check if hp < 0: death comes from the server only 
        ev = CharactorRcvDmgEvt(self, dmg, fromremotechar)
        self._em.post(ev)
        
               
        
