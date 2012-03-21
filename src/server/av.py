from server.charactor import SCharactor
from server.config import config_get_walkcd, config_get_runcd, config_get_maxhp, \
    config_get_baseatk, config_get_rezcd
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

    
    def __init__(self, mdl, nw, pname, cell, facing):
        """ Create an Avatar """
        
        maxhp, atk = config_get_maxhp(), config_get_baseatk()
        SCharactor.__init__(self, pname, cell, facing, maxhp, atk)
        self._mdl = mdl
        self._nw = nw
        
        # place in cell
        self.cell = cell
        self.cell.add_av(self)
        
        # skill durations and cooldowns
        self.MOVE_TXT = {
                         config_get_walkcd(): 'walking',
                         config_get_runcd(): 'running'
                         }
        self.move_ts = 0 # timestamp of last movement; can move right away (no cooldown)
        self.move_cd = config_get_walkcd() # start by walking
        
        self.death_ts = 0 # can resurrect right away
        self.rez_cd = config_get_rezcd() # minimum duration between death and rez
        
   
    def serialize(self):
        """ Serialize first from char then eventually override with avatar attrs. 
        SCharactor returns coords, facing, atk, and hp. 
        SAvatar returns move_cd.
        """
        
        chardic = SCharactor.serialize(self)
        move_cd_txt = self.move_cd, self.MOVE_TXT[self.move_cd]
        avdic = {'move_cd_txt': move_cd_txt}
        chardic.update(avdic) # merge avdic and chardic; pick avdic's values if key conflicts 
        return chardic
        
    
    ######################  atack  ###########################
                
    def attack(self, defer):
        """ When a player attacks, 
        check he's in a cell neighbor of and facing the target. 
        """
        
        atkercell = self.cell
        targetcell = atkercell.get_adjacent_cell(self.facing)
        
        if targetcell == defer.cell:
            dmg = defer.rcv_dmg(self, self.atk) # will do the broadcasting to everyone
            log.debug('Player %s attacked %s for %d dmg' 
                           % (self.name, defer.name, dmg))
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
        self.death_ts = time()
        self._nw.bc_death(self.name)
        # self.resurrect() # TODO: FT should resurrect in 2 seconds instead -> scheduler


    #########################  move  ##############################
    
        
    def move(self, newcell, facing):
        """ Check that move is legal, then move avatar in that cell. """
        # TODO: FT also check if newcell is within reach of oldcell (anti speed-hack)
        
        now = time()
        if (now - self.move_ts) * 1000 < self.move_cd:
            log.warn('Player %s has lots of jitter or speed hacks his movement' 
                      % self.name)
            
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
        

    
    def toggle_movespeed(self):
        """ If av is not running, decrease move cooldown (to run).
        If av is already running, increase move cooldown (to walk).
        """
        
        if self.move_cd == config_get_walkcd(): # was walking
            self.move_cd = config_get_runcd() # now running
        else: # was running
            self.move_cd = config_get_walkcd() # now walking
            
        # no need to send serialize(self), only the move_cd is enough
        txt = self.MOVE_TXT[self.move_cd]
        self._nw.bc_movespeed(self.name, self.move_cd, txt)

        
        
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
        """ Return avatar to entrance with full HP,
        and broadcast the resurrection to everyone. 
        """
        
        now = time()
        
        if now - self.death_ts <= self.rez_cd: # can resurrect
            self.hp = config_get_maxhp()
            
            newcell = self._mdl.world.get_entrance() # back to entrance
            newcell.add_av(self)
            self.cell = newcell
        
            self.move_cd = config_get_walkcd() # return to walking speed
            log.debug('Player %s resurrected' % self.name)
            
            avinfo = self.serialize()
            self._nw.bc_resurrect(self.name, avinfo) # broadcast
        
        else: # must wait
            log.debug('Player %s must wait to rez' % self.name)
            
        
