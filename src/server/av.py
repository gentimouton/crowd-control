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
        # place in cell
        self.cell = cell
        self.cell.add_av(self)
        
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
        cell = self.cell
        if cell: # i'm still alive
            cell.rm_av(self)
            cell = None
        self._nw.bc_playerleft(self.name)

        
    #################### OVERRIDES FROM CHARACTOR ############################

    
    def move(self, newcell, facing):
        """ Check that move is legal, then move avatar in that cell. """
        # TODO: FT also check if newcell is within reach of oldcell  
        
        if newcell: # walkable cell
            # remove from old cell and add to new cell 
            # old and new cells could be the same cell if only facing changed
            oldcell = self.cell
            oldcell.rm_av(self)
            newcell.add_av(self)
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
        
        else: # target cell is not the defer's cell
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
        """ Remove me from my cell, broadcast my death to all players,
        and schedule my resurrection at the entrance. 
        """
        
        self.log.debug('Player %s died' % self.name)
        self.cell.rm_av(self)
        self.cell = None
        self._nw.bc_death(self.name)
        self.resurrect() # TODO: should resurrect in 2 seconds instead -> scheduler


    def resurrect(self):
        """ Return avatar to entrance with full HP,
        and broadcast the resurrection to everyone. 
        """
        
        self.log.debug('Player %s resurrected' % self.name)
        self.hp = 10
        # return  to entrance cell
        newcell = self._mdl.world.get_entrance()
        newcell.add_av(self)
        self.cell = newcell
        # broadcast
        avinfo = self.serialize()
        self._nw.bc_resurrect(self.name, avinfo)

        
        
