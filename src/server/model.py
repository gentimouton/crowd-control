from common.world import World
from server.ai import AiDirector
from server.config import config_get_mapname
from server.events_server import SModelBuiltWorldEvent, SSendGreetEvent, \
    SBroadcastNameChangeEvent, SBroadcastChatEvent, SBroadcastMoveEvent, \
    SPlayerArrivedEvent, SPlayerLeftEvent, SPlayerNameChangeRequestEvent, \
    SReceivedChatEvent, SReceivedMoveEvent, SBroadcastArrivedEvent, \
    SBroadcastLeftEvent, SGameStartEvent
import logging


class SPlayer():
    
    def __init__(self, pname, pos):
        self.pname = pname
        self.coords = pos
        

class SGame():
    
    log = logging.getLogger('server')


    def __init__(self, evManager):
        self._em = evManager
        # callbacks
        self._em.reg_cb(SPlayerArrivedEvent, self.player_arrived)
        self._em.reg_cb(SPlayerLeftEvent, self.player_left)
        self._em.reg_cb(SPlayerNameChangeRequestEvent, self.handle_name_change)
        self._em.reg_cb(SReceivedChatEvent, self.received_chat)
        self._em.reg_cb(SReceivedMoveEvent, self.player_moved)
        
        # Players are here; creeps are in the AI director. 
        self.players = dict()
        
        # build world
        self.world = World(evManager)
        self.mapname = config_get_mapname()
        self.world.build_world(self.mapname, SModelBuiltWorldEvent)

        # TODO: temporary: AI dir should only starts when a player types '/start'
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
        
        
                    
            
            
    def player_arrived(self, event):
        """ Create player's avatar, and send him the list of connected ppl.
        Send also the list of creeps in range.
        Do not include him in the list of connected people. 
        """
        
        pname = event.pname

        if pname not in self.players:

            self.log.info(pname + ' joined')

            # Build list of connected players with their coords.
            onlineppl = dict()
            for (otherpname, otherplayer) in self.players.items():
                onlineppl[otherpname] = otherplayer.coords
            
            # Build list of creeps with their coords.
            creeps = dict()
            for (cid, creep) in self.aidir.creeps.items():
                creeps[cid] = creep.cell.coords
            
            # build the new player    
            coords = self.world.entrance_coords
            player = SPlayer(pname, coords)
            self.players[pname] = player
            
            # greet the new player 
            event = SSendGreetEvent(self.mapname, pname, coords, onlineppl, creeps)
            self._em.post(event) 
            
            # notify the connected players of this arrival
            event = SBroadcastArrivedEvent(pname, coords)
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
        pname, coords = event.pname, event.coords
        
        if self.world.iswalkable(coords): 
            self.players[pname].coords = coords
            #self.log.debug(pname + ' moved to ' + str(coords))
            event = SBroadcastMoveEvent(pname, coords)
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
            self.aidir = AiDirector(self._em, self.world)
            self.log.info('Gane started by ' + pname)
            ev = SGameStartEvent(pname)
            self._em.post(ev)

        elif cmd == 'nick':
            newname = args[0]
            ev = SPlayerNameChangeRequestEvent(pname, newname)
            self._em.post(ev)
            

