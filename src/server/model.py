from common.constants import DIRECTION_UP, DIRECTION_LEFT
from common.world import World
from server.av import SAvatar
from server.config import config_get_mapname, config_get_gmcmdprefix, \
    config_get_creepsperwave
from server.npc import SCreep
from server.sched import Scheduler
import logging




class SGame():
    
    log = logging.getLogger('server')

    def __init__(self, evManager, nw):
        self._em = evManager
        # link with network controller
        self._nw = nw
        self._nw.model = self
        
        # Players + creeps = charactors 
        self.players = dict()
        self.creeps = dict()
        
        # build world
        self.world = World(evManager, self.log)
        mapname = config_get_mapname()
        self.world.build_world(mapname, callbacks=[self._nw.on_worldbuilt])
        self.world.buildpath()

        # when server starts, the game is not ON yet
        self.gameon = False
        
        # scheduling of game actions
        self._sched = Scheduler(self._em, self.world)

        #self.startgame('nobody')
      

    def __str__(self):
        args = (self.world.mapname, len(self.players), len(self.creeps))
        return '%s, %d players, %d creeps' % args 
    


    

    ######################  attack  #####################################
    
    def on_attack(self, atkername, defername, atk):
        """ This function is called by the network controller only.
        Trigger the attacking charactor's function attack(defer)
        """
        
        # get charactors from names
        atker = self.get_charactor(atkername)
        defer = self.get_charactor(defername)
        # defer may be None if atker = client with outdated model and defer = creep already dead 
        
        if atker and defer: # both are still present
            dmg = atker.attack(defer)
            if dmg == None: # atker attacked cell where the defer was not
                self.log.debug('%s missed the cell of %s' % (atkername, defername))
                # TODO: FT broadcast a miss msg
            elif dmg != atk:
                self.log.warn('%s says it attacked %s for %d, but server computed'
                              + ' %d instead' % (atkername, defername, atk, dmg))
        else:
            self.log.debug('%s attacked %s who was dead already' % (atkername, defername))
            # Dont do anything else: the client rendered his attack locally already
            # so, no need for the other clients to know about the failed attack.
            
             
                
    def get_charactor(self, name):
        """ Return an SCharactor (SCreep or SAvatar) from its name """
        
        if name in self.players:
            return self.players[name]
        else: 
            try:
                return self.creeps[name]
            except KeyError: # char not found = player left or creep died
                return None


    ##########################  chat  #################################
    
            
    def on_chat(self, pname, txt):
        """ When a chat message is received, 
        parse eventual commands,
        or broadcast the text to all connected users.
        """
                
        self.log.debug(pname + ' says ' + txt)
        
        gmprefix = config_get_gmcmdprefix()
        if txt and txt[0:len(gmprefix)] == gmprefix: # command
            args = txt.split()
            cmd = args[0][1:] # remove the leading '/'
            gm_func_name = 'gm_' + cmd
            if hasattr(self, gm_func_name):
                getattr(self, gm_func_name)(pname, args[1:])
            
        else: # normal chat msg
            self._nw.bc_chat(pname, txt)


    ##################### death ################
    

    def rmv_creep(self, name):
        """ Remove a creep given its name. Called by Creep. """
        try:
            del self.creeps[name]
        except KeyError:
            self.log.warning('Tried to remove creep %s but failed.' % (name))


    ##############  join  ######################

            
    def on_playerjoin(self, pname):
        """ Create player's avatar, and send him the list of connected ppl.
        Send also the list of creeps in range.
        Do not include him in the list of connected people. 
        """
        
        if pname in self.players:
            # player was already connected, 
            # or his pname had not been removed when he disconnected
            self.log.warn('Player %s already was connected.' % pname)
            return
                
        # Build list of connected players with their coords and facing direction.
        onlineppl = dict()
        for (otherpname, otherplayer) in self.players.items():
            onlineppl[otherpname] = otherplayer.serialize()
        
        # Build list of creeps with their coords.
        creeps = dict()
        for cname, creep in self.creeps.items():
            creeps[cname] = creep.serialize()
        
        # build the new player on the entrance cell and facing upwards
        cell = self.world.get_entrance()
        facing = DIRECTION_UP
        player = SAvatar(self, self._nw, self._sched, pname, cell, facing)
        self.players[pname] = player
        
        # greet the new player
        myinfo = player.serialize() 
        self._nw.greet(self.world.mapname, pname, myinfo,
                         onlineppl, creeps)
        
        # notify the connected players of this arrival
        self._nw.bc_playerjoined(pname, myinfo)
            

    
    ##############  left  ######################

    def on_playerleft(self, pname):
        """ remove player's avatar from game state and notify everyone """
        
        try:
            av = self.players[pname]
            av.on_logout() # remove avatar from the world
            del self.players[pname]
        except KeyError:
            self.log.warn('Tried to remove player ' + pname + 
                          ', but it was not found in player list')
                
        
    ###########################  move  ##################################
    
    def on_move(self, pname, coords, facing):
        """ Make a player move. 
        The player object will check for cheats itself. 
        """

        player = self.players[pname]
        newcell = self.world.get_cell(coords) #None means non-walkable or out
        player.move(newcell, facing)
            
                   
    ##############  namechange  ######################

    def on_playernamechange(self, oldname, newname):
        """ Change player's name only if the new name is not taken already. """
                
        if newname in self.players: # newname is already taken
            reason = 'Name already taken.'
            self._nw.send_namechangefail(oldname, newname, reason)
            
        else: # name not taken already
            player = self.players[oldname]
            canchange, reason = player.change_name(newname)
            if canchange: # new name is not too long
                self.log.debug(oldname + ' changed name into ' + newname)
                self.players[newname] = player
                del self.players[oldname]
                self._nw.bc_namechange(oldname, newname)
            else: # could not change name (e.g. too long or too short)
                self._nw.send_namechangefail(oldname, newname, reason)
        


    #####################  skill  ###########################
    
    def on_playerskill(self, pname, skname):
        """ A player used a skill """

        # TODO: refactor/cleanup
        if skname in ['burst']:
            av = self.players[pname]
            av.skill_burst()
        else:
            self.log.warn('Skill %s not found for player %s' % (skname, pname))
        


    ######################### GM commands ##############################
    # TODO: FT this should be in a Commander

    def gm_nick(self, pname, args):
        """ change player name """
        if args: # check that the user provided a new name
            newname = args[0]
            self.on_playernamechange(pname, newname)
    
    def gm_rez(self, pname, args):
        """ rez the player's avatar """
        av = self.players[pname]
        av.resurrect()
        
    def gm_start(self, pname, args):
        """ start the game """
        if self.gameon:
            self.stopgame(pname)
        self.startgame(pname)

    def gm_stop(self, pname, args):
        """ stop the game """
        if self.gameon:
            self.stopgame(pname)
        
    def gm_hp(self, pname, args):
        """ change the player's hp (and mhp if specified).
        '/hp 1' changes hp to 1, 
        '/hp 1/2' changes both hp to 1 and mhp to 2,
        '/hp /2' changes mhp, and keeps sure that hp <= mhp,
        '/hp 1/2/...' is the same as '/hp 1/2'
        """ 
        if args:
            hp_strs = args[0].split('/') # len(hps) is 0 if no '/' found
            try:
                hp = int(hp_strs[0])
            except ValueError: # casting str to int failed
                hp = None # cases like '/hp not_a_number'
            try:
                if len(hp_strs) >= 2:
                    mhp = int(hp_strs[1])
                else:
                    mhp = None
            except ValueError: # casting str to int failed
                mhp = None # cases like '/hp not_a_number'
        else: # no args == full heal
            mhp = hp = None
        
        av = self.players[pname]
        av.update_hps(hp, mhp)
            
        

    ########################  game commands  ###################
    
    def startgame(self, pname):
        """ start the game: creeps arrive """
        
        self.gameon = True
        self.log.info('Game started by ' + pname)
        self._nw.bc_gameadmin(pname, 'start')

        numcreeps = config_get_creepsperwave()
        cell = self.world.get_lair()
        for x in range(numcreeps):
            cname = 'creep-%d' % x
            delay = x * 1000
            creep = SCreep(self, self._sched, delay, 
                           self._nw, cname, cell, DIRECTION_LEFT) #face left
            self.creeps[cname] = creep
            
            
    def stopgame(self, pname):
        """ stop the game: kill all creeps """
        
        self.gameon = False
        self.log.info('Game stopped by ' + pname)
        self._nw.bc_gameadmin(pname, 'stop')
        
        # kill all the creeps
        creepscopy = self.creeps.copy()
        for creep in creepscopy.values():
            creep.die() # this removes the creep from self.creeps
        
