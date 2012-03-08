from server.charactor import SCharactor
import logging



class SAvatar(SCharactor):
    """ represents a player in the game world.
    On the server-side, it mostly only checks 
    the moves and commands sent by the real players. 
    """
    
    log = logging.getLogger('server')


    def __init__(self, mdl, nw, pname, cell, facing):
        SCharactor.__init__(self, pname, cell, facing, 10, 6)
        self._mdl = mdl
        self._nw = nw
        
        
    def on_logout(self):
        """ When player leaves, remove avatar from the cell it was on."""
        # pickle/persist the avatar state should happen here
        self.cell.rm_occ(self)
        
        
    #################### OVERRIDES FROM CHARACTOR ############################

    
    def move(self, cell, facing):
        self.cell = cell
        self.facing = facing
        # TODO: should ask for movement broadcast
        
    def attack(self, defer):
        """ When a player attacks, 
        check he's in a cell neighbor and facing the target. 
        """
        atkercell = self.cell
        targetcell = atkercell.get_adjacent_cell(self.facing)
        if targetcell == defer.cell: 
            self.log.debug(self.name + ' attacked ' + defer.name)
            return defer.rcv_atk(self) # rcv_atk in charge of broadcasting 
        else:
            return None
        
    
    def rcv_atk(self, atker):
        dmg = atker.atk
        self.hp -= dmg
        self.log.debug('Player %s received %d dmg' % (self.name, dmg))
        
        self._nw.bc_atk(atker.name, self.name, dmg)
        
        # less than 0 HP => death
        if self.hp <= 0:
            self.die()
            
    def die(self):
        self.log.info('Player %s should die' % self.name)
        self.hp = 10 # TODO: should really die instead

