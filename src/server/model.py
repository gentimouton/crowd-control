from common.constants import DIRECTION_UP, DIRECTION_LEFT
from common.world import World
from server.av import SAvatar
from server.config import config_get_mapname
from server.npc import SCreep
from server.sched import Scheduler
from uuid import uuid4
import logging


        

###############################################################################




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

      

    def __str__(self):
        args = (self.world.mapname, len(self.players), len(self.creeps))
        return '%s, %d players, %d creeps' % args 
    
    
    def get_charactor(self, name):
        """ Return a SCharactor (SCreep or SAvatar) from its name """
        if name in self.players:
            return self.players[name]
        else: 
            try: 
                return self.creeps[name]
            except KeyError: # creep not found
                self.log.error("Creep %s not found" % name)
                return None
        

    def rmv_creep(self, name):
        """ remove a creep from its name """
        try:
            del self.creeps[name]
        except KeyError:
            self.log.warning('Tried to remove creep %s but failed.' % (name))


    ############### (dis)connection and name changes ##########################
        
    # notifying for pausing/resuming the game could also fit in there
                    
            
            
    def on_playerjoined(self, pname):
        """ Create player's avatar, and send him the list of connected ppl.
        Send also the list of creeps in range.
        Do not include him in the list of connected people. 
        """
        
        if pname in self.players:
            # player was already connected, 
            # or his pname had not been removed when he disconnected
            self.log.error('Player %s already was connected.' % pname)
            return
                
        self.log.info(pname + ' joined')

        # Build list of connected players with their coords and facing direction.
        onlineppl = dict()
        for (otherpname, otherplayer) in self.players.items():
            onlineppl[otherpname] = otherplayer.get_serializablepos()
        
        # Build list of creeps with their coords.
        creeps = dict()
        for cname, creep in self.creeps.items():
            creeps[cname] = creep.get_serializablepos()
        
        # build the new player on the entrance cell and facing upwards
        cell = self.world.get_entrance()
        facing = DIRECTION_UP
        player = SAvatar(self, self._nw, pname, cell, facing)
        self.players[pname] = player
        
        # send_greet the new player 
        self._nw.greet(self.world.mapname, pname, cell.coords, facing,
                         onlineppl, creeps)
        
        # notify the connected players of this arrival
        self._nw.bc_playerjoined(pname, cell.coords, facing)
            
    
    
    def on_playerleft(self, pname):
        """ remove player's avatar from game state and notify everyone """
        
        try:
            av = self.players[pname]
            av.on_logout() # remove avatar from the world
            del self.players[pname]
            self.log.info(pname + ' left.')
        except KeyError:
            self.log.error('Tried to remove player ' + pname + 
                  ', but it was not found in player list')
        
        self._nw.bc_left(pname)
        
        

    #########################################################################
            
    def on_playerchangedname(self, oldname, newname):
        """ Change player's name only if the new name is not taken already. """
                
        if newname not in self.players:
            self.log.info(oldname + ' changed name into ' + newname)
            
            player = self.players[oldname]
            player.change_name(newname)
            
            self.players[newname] = player
            del self.players[oldname]
            
            self._nw.bc_namechange(oldname, newname)
        
        else: 
            # TODO: send personal notif to the client who failed to change name
            self.log.debug(oldname + ' asked to change name into ' + newname 
                           + ' but someone was already using that name.')

    
    ##########################################################################
            
    def received_chat(self, pname, txt):
        """ When a chat message is received, 
        parse eventual commands,
        or broadcast the text to all connected users.
        """
                
        self.log.debug(pname + ' says ' + txt)
        
        if txt and txt[0] == '/': # command
            args = txt.split()
            self.exec_cmd(pname, args[0][1:], args[1:])
            
        else: # normal chat msg
            self._nw.bc_chat(pname, txt)


    ##########################################################################
    
    def on_playermoved(self, pname, coords, facing):
        """ when a player moves, notify all of them """
        
        if self.world.iswalkable(coords):
            player = self.players[pname]

            # remove player from old cell and add player to new cell
            oldcell = player.cell
            newcell = self.world.get_cell(coords)
            oldcell.rm_occ(player)
            newcell.add_occ(player)
            player.move(newcell, facing)
            
            #self.log.debug(name + ' moved to ' + str(newcell.coords))
            self._nw.bc_move(pname, newcell.coords, facing)

        else:
            self.log.warn('Possible cheat: ' + pname 
                          + ' walks in non-walkable cell' + str(coords))
            




    ##########################################################################
    
    def on_charattacked(self, atkername, defername):
        """ Trigger the attacking charactor's attack(defer)
        This function is called by the network controller only.
        """
        
        # get charactors from names
        atker = self.get_charactor(atkername)
        defer = self.get_charactor(defername)
        
        if atker and defer: # both are still alive
            atker.attack(defer)
            #dmg = atker.attack(defer)
            # TODO: check that dmg == the player's nw msg says he inflicted        




    ######################### commands parsing ##############################

    def exec_cmd(self, pname, cmd, args):
        """ Execute a player command. 
        args[0] is not the command's name, it's the first cmd argument!! 
        """

        if cmd == 'start':
            if self.gameon:
                self.stopgame(pname)
            self.startgame(pname)

        elif cmd == 'stop':
            if self.gameon:
                self.stopgame(pname)
            
        elif cmd == 'nick':
            try:
                newname = args[0]
                self.on_playerchangedname(pname, newname)
            except IndexError: # new nick only contained spaces
                pass 
            

    ############### game commands #############
    
    def startgame(self, pname):
        """ start the game: creeps arrive """
        self.gameon = True
        self.log.info('Game started by ' + pname)
        self._nw.bc_gameadmin(pname, 'start')

        numcreeps = 1
        cell = self.world.get_lair()
        for x in range(numcreeps):
            cname = str(uuid4()) # TODO: shorter creep names
            creep = SCreep(self, self._sched, self._nw, cname, cell, DIRECTION_LEFT) #face left
            self.creeps[cname] = creep
            
            
    def stopgame(self, pname):
        """ stop the game: kill all creeps """
        self.gameon = False
        self.log.info('Game stopped by ' + pname)
        self._nw.bc_gameadmin(pname, 'stop')

        for cname in self.creeps.keys():
            self._sched.unschedule_actor(cname)
        self.creeps.clear()

