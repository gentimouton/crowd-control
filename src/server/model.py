from common.world import World
from server.ai import AiDirector
from server.config import config_get_mapname
from server.events_server import SModelBuiltWorldEvent, SSendGreetEvent, \
    SBroadcastNameChangeEvent, SBroadcastChatEvent, SBroadcastMoveEvent, \
    SPlayerArrivedEvent, SPlayerLeftEvent, SPlayerNameChangeRequestEvent, \
    SReceivedChatEvent, SReceivedMoveEvent, SBroadcastArrivedEvent, \
    SBroadcastLeftEvent, NwBcAdminEvt
import logging
from common.constants import DIRECTION_UP


class SPlayer():
    
    def __init__(self, pname, coords, facing):
        self.pname = pname
        self.coords = coords
        self.facing = facing #direction the player is facing
        

class SGame():
    
    log = logging.getLogger('server')


    def __init__(self, evManager):
        self._em = evManager
        # callbacks
        self._em.reg_cb(SPlayerArrivedEvent, self.on_playerjoined)
        self._em.reg_cb(SPlayerLeftEvent, self.player_left)
        self._em.reg_cb(SPlayerNameChangeRequestEvent, self.handle_name_change)
        self._em.reg_cb(SReceivedChatEvent, self.received_chat)
        self._em.reg_cb(SReceivedMoveEvent, self.player_moved)
        
        # Players are here; creeps are in the AI director. 
        self.players = dict()
        
        # build world
        self.world = World(evManager, self.log)
        self.mapname = config_get_mapname()
        self.world.build_world(self.mapname, SModelBuiltWorldEvent)
        self.world.buildpath()

        # AI dir is activated when a player sends '/start'
        self.aidir = AiDirector(self._em, self.world)

      
    ############### (dis)connection and name changes ##########################
        
    # notifying for pausing/resuming the game could also fit in there
        
    def player_left(self, event):
        """ remove player's avatar from game state and notify everyone """
        
        pname = event.pname
        
        try:
            del self.players[pname]
            self.log.info(pname + ' left.')
        except KeyError:
            self.log.error('Tried to remove player ' + pname + 
                  ', but it was not found in player list')
        
        event = SBroadcastLeftEvent(pname)
        self._em.post(event)
        
        
                    
            
            
    def on_playerjoined(self, event):
        """ Create player's avatar, and send him the list of connected ppl.
        Send also the list of creeps in range.
        Do not include him in the list of connected people. 
        """
        
        pname = event.pname

        if pname not in self.players:

            self.log.info(pname + ' joined')

            # Build list of connected players with their coords and facing direction.
            onlineppl = dict()
            for (otherpname, otherplayer) in self.players.items():
                onlineppl[otherpname] = otherplayer.coords, otherplayer.facing
            
            # Build list of creeps with their coords.
            creeps = dict()
            for (cid, creep) in self.aidir.creeps.items():
                creeps[cid] = creep.cell.coords, creep.facing
            
            # build the new player on the entrance cell and facing upwards
            coords = self.world.entrance_coords
            facing = DIRECTION_UP
            player = SPlayer(pname, coords, facing)
            self.players[pname] = player
            
            # greet the new player 
            event = SSendGreetEvent(self.mapname, pname, coords, facing, onlineppl, creeps)
            self._em.post(event) 
            
            # notify the connected players of this arrival
            event = SBroadcastArrivedEvent(pname, coords, facing)
            self._em.post(event)
            
        else: 
            # player was already connected, 
            # or his pname had not been removed when he disconnected
            self.log.warning(pname, ' was already in connected players ; '
                             + 'self.player_positions[pname] may have been corrupted?')
    
    


    #########################################################################
            
    def handle_name_change(self, event):
        """ change player's name only if newname not taken already """
        
        oldname, newname = event.oldname, event.newname
        
        if newname not in self.players:
            self.log.info(oldname + ' changed name into ' + newname)
            
            self.players[newname] = self.players[oldname]
            del self.players[oldname]
                        
            event = SBroadcastNameChangeEvent(oldname, newname)
            self._em.post(event)
        
        else: 
            # TODO: send personal notif to the client who failed to change name
            self.log.debug(oldname + ' asked to change name into ' + newname 
                           + ' but someone was already using that name.')

    
    ##########################################################################
            
    def received_chat(self, event):
        """ When a chat message is received, 
        parse eventual commands,
        or broadcast the text to all connected users.
        """
        
        pname, txt = event.pname, event.txt 
        
        self.log.debug(pname + ' says ' + txt)
        
        if txt and txt[0] == '/': # command
            args = txt.split()
            self.exec_cmd(pname, args[0][1:], args[1:])
            
        else:
            event = SBroadcastChatEvent(pname, txt)
            self._em.post(event)



    ##########################################################################
    
    def player_moved(self, event):
        """ when a player moves, notify all of them """
        pname, coords, facing = event.pname, event.coords, event.facing
        
        if self.world.iswalkable(coords): 
            self.players[pname].coords = coords
            self.players[pname].facing = facing
            #self.log.debug(pname + ' moved to ' + str(coords))
            # dont have anything to do about facing yet
            event = SBroadcastMoveEvent(pname, coords, facing)
            self._em.post(event)

        else:
            self.log.warn('Possible cheat: ' + pname 
                          + ' walks in non-walkable cell' + str(coords))
            

    ######################### commands parsing ##############################

    def exec_cmd(self, pname, cmd, args):
        """ Execute a player command. 
        args[0] is not the command's name, it's the first argument!! 
        """

        if cmd == 'start':
            if self.aidir.isrunning:
                self.aidir.stop()
                ev = NwBcAdminEvt(pname, 'stop')
                self._em.post(ev)
            self.aidir.start()
            self.log.info('Game started by ' + pname)
            ev = NwBcAdminEvt(pname, 'start')
            self._em.post(ev)

        elif cmd == 'stop':
            self.aidir.stop()
            self.log.info('Game stopped by ' + pname)
            ev = NwBcAdminEvt(pname, 'stop')
            self._em.post(ev)
            
        elif cmd == 'nick':
            try:
                newname = args[0]
                ev = SPlayerNameChangeRequestEvent(pname, newname)
                self._em.post(ev)
            except IndexError: # new nick only contained spaces
                pass 
            

