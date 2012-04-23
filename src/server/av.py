from server.charactor import SCharactor
from server.config import config_get_maxhp, config_get_baseatk, config_get_rezcd, \
    config_get_atkcd
from time import time
import logging


log = None

class SAvatar(SCharactor):
    """ represents a player in the game world.
    On the server-side, it mostly only checks 
    the moves and commands sent by the real players. 
    """
    
    global log
    log = logging.getLogger('server')
    # TODO: RFCTR should globalize model and network too

    
    def __init__(self, mdl, nw, sched, pname, cell, facing):
        """ Create an Avatar """
        
        maxhp, atk = config_get_maxhp(), config_get_baseatk()
        SCharactor.__init__(self, pname, cell, facing, maxhp, atk)
        self._mdl = mdl
        self._nw = nw
        self._sched = sched
        
        # place in cell
        self.cell = cell
        self.cell.add_av(self)
        
        self.atk_ts = 0 # timestamp of last atk; can atk right away (no cooldown)
        self.atk_cd = config_get_atkcd()
                
        
   
    def serialize(self):
        """ Serialize first from char then eventually override with avatar attrs. 
        SCharactor returns coords, facing, atk, and hp. 
        SAvatar returns move_cd.
        """
        
        chardic = SCharactor.serialize(self)
        atk_cd = self.atk_cd
        avdic = {'atk_cd': atk_cd}
        chardic.update(avdic) # merge avdic and chardic; pick avdic's values if key conflicts 
        return chardic
        
    
    ######################  attack  ###########################
                
    def attack(self, defer):
        """ When a player attacks, 
        check he's in a cell neighbor of and facing the target. 
        """
        
        now = time()
        if (now - self.atk_ts) * 1000 < self.atk_cd:
            log.warn('Player %s has lots of jitter or speed hacks his attack' 
                      % self.name)
        
        atkercell = self.cell
        targetcell = atkercell.get_adjacent_cell(self.facing)
        
        if targetcell == defer.cell:
            dmg = defer.rcv_dmg(self, self.atk) # will do the broadcasting to everyone
            log.debug('Player %s attacked %s for %d dmg' 
                           % (self.name, defer.name, dmg))
            self.atk_ts = now
            return dmg
        
        else: # target cell is not the defer's cell
            return None
        
    
    def rcv_dmg(self, atker, dmg):
        """ Receive damage from an attacker. Return amount of dmg received. """
        self.hp -= dmg
        log.debug('Player %s received %d dmg from %s' 
                  % (self.name, dmg, atker.name))
        
        self._nw.bc_attack(atker.name, self.name, dmg)
        
        # less than 0 HP => death
        if self.hp <= 0:
            self.die()
        
        return dmg
    
       
    ####################  death  ############################

    def die(self):
        """ Remove me from my cell, broadcast my death to all players,
        and schedule my resurrection at the entrance. 
        """
        
        log.debug('Player %s died' % self.name)
        self.cell.rm_av(self)
        self._nw.bc_death(self.name)
        # schedule rez after rez cooldown
        rez_cd = config_get_rezcd() # duration between death and rez
        self._sched.schedule_action(rez_cd, self.name, self.resurrect) 


        
         
    #########################  move  ##############################
    
        
    def move(self, newcell, facing):
        """ Check that move is legal, then move avatar in that cell. """
        # TODO: FT also check if newcell is within reach of oldcell (anti speed-hack)
        
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
            log.warn('Possible cheat: %s walks in non-walkable cell %s'
                          % (self.name, self.cell.coords))
        


        
        
    ###################  namechange  ###############################
    
    def change_name(self, newname):
        """ Change charactor name. Return whether name could be changed.
        If name could not be changed, explain why.
        """ 
        if len(newname) > 0 and len(newname) < 9:
            self.name = newname
            return True, None
        else:
            return False, 'Only names from 1 to 8 characters are allowed.'
        
    
    ###########################  left  ###########################
    
    def on_logout(self):
        """ When player leaves, remove avatar from the cell it was on."""
        # pickle/persist the avatar state should happen here
        cell = self.cell
        if cell: # i'm still alive
            cell.rm_av(self)
            cell = None
        self._nw.bc_playerleft(self.name)

     

    ####################  resurrect  ####################
    
    def resurrect(self):
        """ Return avatar to entrance with some HP,
        and broadcast the resurrection to everyone.
        Rez works even when av is still alive. 
        """
        
        self.hp = int(self.maxhp / 5)
        
        self.cell.rm_av(self)
        newcell = self._mdl.world.get_entrance() # back to entrance
        newcell.add_av(self)
        self.cell = newcell
    
        log.debug('Player %s resurrected' % self.name)
        
        avinfo = self.serialize()
        self._nw.bc_resurrect(self.name, avinfo) # broadcast
    
            
        
