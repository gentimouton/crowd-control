from common.constants import DIRECTION_RIGHT
from server.charactor import Charactor
import logging



class SAvatar(Charactor):
    """ represents a player in the game world.
    On the server-side, it mostly only checks 
    the moves and commands sent by the real players. 
    """
    
    log = logging.getLogger('server')


    def __init__(self, mdl, nw, pname, cell, facing):
        Charactor.__init__(self, pname, cell, facing, 10, 6)
        self._mdl = mdl
        self._nw = nw
        
        
    def change_name(self, newname):
        """ Change charactor name. Return whether name could be changed.
        If name could not be changed, explain why.
        """ 
        if len(newname) > 0 and len(newname) < 9:
            self.name = newname
            return True, None
        else:
            return False, 'Only names from 1 to 8 characters are allowed.'
        
        
    def on_logout(self):
        """ When player leaves, remove avatar from the cell it was on."""
        # pickle/persist the avatar state should happen here
        self.cell.rm_occ(self)
        self._nw.bc_playerleft(self.name)

        
    #################### OVERRIDES FROM CHARACTOR ############################

    
    def move(self, newcell, facing):
        """ Check that move is legal, then move avatar in that cell. """
        # TODO: FT also check if newcell is within reach of oldcell  
        if newcell: # walkable cell
            # remove from old cell and add to new cell
            oldcell = self.cell
            oldcell.rm_occ(self)
            newcell.add_occ(self)
            self.cell = newcell
            self.facing = facing
            self._nw.bc_move(self.name, newcell.coords, facing)
        
        else: # cell is not walkable or outside of the map
            self.log.warn('Possible cheat: %s walks in non-walkable cell %s'
                          % (self.name, self.cell.coords))
        

        
    def attack(self, defer):
        """ When a player attacks, 
        check he's in a cell neighbor of and facing the target. 
        """
        atkercell = self.cell
        targetcell = atkercell.get_adjacent_cell(self.facing)
        
        if targetcell == defer.cell:
            dmg = defer.rcv_dmg(self, self.atk) # will do the broadcasting to everyone
            self.log.debug('Player %s attacked %s for %d dmg' 
                           % (self.name, defer.name, dmg))
            return dmg
        
        else:
            return None
        
    
    def rcv_dmg(self, atker, dmg):
        """ Receive damage from an attacker. Return amount of dmg received. """
        self.hp -= dmg
        self.log.debug('Player %s received %d dmg from %s' 
                       % (self.name, dmg, atker.name))
        
        self._nw.bc_attack(atker.name, self.name, dmg)
        
        # less than 0 HP => death
        if self.hp <= 0:
            self.die()
        
        return dmg


    def die(self):
        """ broadcast the death to all players
        and resurrect at entrance. 
        """
        self.log.info('Player %s should die' % self.name)
        self._nw.bc_death(self.name)
        
        # av is sent back to entrance with full hp
        self.hp = 10 
        self.warp(self._mdl.world.get_entrance()) # same facing as when died

    
    def warp(self, newcell, facing=None):
        """ Teleport to given cell with given facing. """
        if newcell: # walkable cell
            # remove from old cell and add to new cell
            oldcell = self.cell
            oldcell.rm_occ(self)
            newcell.add_occ(self)
            self.cell = newcell
            
            if facing: #update facing only if provided
                self.facing = facing
            # broadcast
            avinfo = self.serialize()
            self._nw.bc_warp(self.name, avinfo)
        
        else: # cell is not walkable or outside of the map
            self.log.warn('Cell %s can not be warped to by avatar %s'
                          % (self.cell.coords, self.name))
        
        
        
