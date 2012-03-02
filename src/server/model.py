from common.constants import DIRECTION_UP
from common.world import World
from server.ai import AiDirector
from server.config import config_get_mapname
from server.events_server import SModelBuiltWorldEvent, SSendGreetEvent, \
    SBroadcastNameChangeEvent, SBroadcastChatEvent, SBroadcastMoveEvent, \
    SPlayerArrivedEvent, SPlayerLeftEvent, SPlayerNameChangeRequestEvent, \
    SReceivedChatEvent, SReceivedMoveEvent, SBroadcastArrivedEvent, \
    SBroadcastLeftEvent, NwBcAdminEvt, SReceivedAtkEvent, SBcAtkEvent
import logging


class SPlayer():
    # TODO: SPlayer needs to have an SAvatar attribute?
    
    def __init__(self, pname, coords, facing):
        self.pname = pname
        self.coords = coords
        self.facing = facing #direction the player is facing
        
        self.atk = 6 #how much dmg inflicted per attack

    
    def __str__(self):
        return '<SPlayer %s named %s>' % (id(self), self.pname)


class SGame():
    
    log = logging.getLogger('server')


    def __init__(self, evManager):
        self._em = evManager
        # callbacks
        self._em.reg_cb(SPlayerArrivedEvent, self.on_playerjoined)
        self._em.reg_cb(SPlayerLeftEvent, self.player_left)
        self._em.reg_cb(SPlayerNameChangeRequestEvent, self.on_playerchangedname)
        self._em.reg_cb(SReceivedChatEvent, self.received_chat)
        self._em.reg_cb(SReceivedMoveEvent, self.on_playermoved)
        self._em.reg_cb(SReceivedAtkEvent, self.on_playerattacked)
        
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
            cell = self.world.get_cell(coords)
            cell.add_occ(pname)
            
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
            
    def on_playerchangedname(self, event):
        """ Change player's name only if the new name is not taken already. """
        
        oldname, newname = event.oldname, event.newname
        
        if newname not in self.players:
            self.log.info(oldname + ' changed name into ' + newname)
            
            player = self.players[oldname]
            player.pname = newname
            # notify the cell the player is currently on
            cell = self.world.get_cell(player.coords)
            cell.occ_chngname(oldname, newname)
            self.players[newname] = player
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
    
    def on_playermoved(self, event):
        """ when a player moves, notify all of them """
        pname, coords, facing = event.pname, event.coords, event.facing
        
        if self.world.iswalkable(coords):
            player = self.players[pname]

            # remove player from old cell and add player to new cell
            oldcell = self.world.get_cell(player.coords)
            oldcell.rm_occ(player.pname)
            newcell = self.world.get_cell(coords)
            newcell.add_occ(player.pname)
            
            player.coords = coords
            player.facing = facing
            #self.log.debug(pname + ' moved to ' + str(coords))
            event = SBroadcastMoveEvent(pname, coords, facing)
            self._em.post(event)

        else:
            self.log.warn('Possible cheat: ' + pname 
                          + ' walks in non-walkable cell' + str(coords))
            




    ##########################################################################
    
    def on_playerattacked(self, event):
        """ when a player attacks, he can only inflict dmg 
        to creeps in adjacent cells. No friendly fire.
        """
        pname, tname = event.pname, event.tname
        player = self.players[pname]
        
        try:
            # check that player is facing the creep, and creep is in adjacent cell
            creep = self.aidir.creeps[tname]
            playercell = self.world.get_cell(player.coords)
            targetcell = playercell.get_adjacent_cell(player.facing)
            if targetcell == creep.cell: 
                self.log.debug(pname + ' attacked ' + tname)
                dmg = creep.rcv_atk(player.atk)# takes the creep's stats into account
                ev = SBcAtkEvent(pname, tname, dmg)
                self._em.post(ev)
                  
        except KeyError: # most likely, a client sent an incorrect creep id
            self.log.warning('Target ' + tname + ' was attacked by ' + pname  
                             + ' but target was not found.')
 
        
            
            



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
            

