from common.constants import DIRECTION_UP
from common.world import World
from server.ai import AiDirector
from server.charactor import SCharactor
from server.config import config_get_mapname
from server.events_server import SModelBuiltWorldEvent, SSendGreetEvent, \
    SBcNameChangeEvent, SBcChatEvent, SBroadcastMoveEvent, \
    SPlayerArrivedEvent, SPlayerLeftEvent, SPlayerNameChangeRequestEvent, \
    SNwRcvChatEvent, SNwRcvMoveEvent, SBcArrivedEvent, SBcLeftEvent, \
    NwBcAdminEvt, SNwRcvAtkEvent, SCreepAtkEvent, SBcAtkEvent
import logging


        

###############################################################################




class SGame():
    
    log = logging.getLogger('server')


    def __init__(self, evManager):
        self._em = evManager
        # callbacks
        self._em.reg_cb(SPlayerArrivedEvent, self.on_playerjoined)
        self._em.reg_cb(SPlayerLeftEvent, self.player_left)
        self._em.reg_cb(SPlayerNameChangeRequestEvent, self.on_playerchangedname)
        self._em.reg_cb(SNwRcvChatEvent, self.received_chat)
        self._em.reg_cb(SNwRcvMoveEvent, self.on_playermoved)
        self._em.reg_cb(SNwRcvAtkEvent, self.on_charattacked)
        self._em.reg_cb(SCreepAtkEvent, self.on_charattacked)
        
        # Players are here; creeps are in the AI director. 
        self.players = dict()
        
        # build world
        self.world = World(evManager, self.log)
        mapname = config_get_mapname()
        self.world.build_world(mapname, SModelBuiltWorldEvent)
        self.world.buildpath()

        # AI dir is activated when a player sends '/start'
        self.aidir = AiDirector(self._em, self.world)

      
    def get_charactor(self, name):
        """ Return a SCharactor (SCreep or SAvatar) from its name """
        if name in self.players:
            return self.players[name]
        else: 
            return self.aidir.get_creep(name) # None if not found
        
        
    ############### (dis)connection and name changes ##########################
        
    # notifying for pausing/resuming the game could also fit in there
                    
            
            
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
                onlineppl[otherpname] = otherplayer.cell.coords, otherplayer.facing
                # TODO: should be player.get_serializable_pos(), returning (coords, facing)
            
            # Build list of creeps with their coords.
            creeps = dict()
            for creep in self.aidir.get_creeps():
                creeps[creep.name] = creep.cell.coords, creep.facing
                # TODO: should come from the creep itself
            
            # build the new player on the entrance cell and facing upwards
            cell = self.world.get_entrance()
            facing = DIRECTION_UP
            player = SAvatar(self._em, pname, cell, facing)
            self.players[pname] = player
            cell.add_occ(pname) # TODO: cell.add_player should be called in Avatar, World, or Cell?
            # TODO: should add_player(Charactor), not just player name
            
            # greet the new player 
            args = self.world.mapname, pname, cell.coords, facing, onlineppl, creeps
            event = SSendGreetEvent(*args)
            self._em.post(event)
            
            # notify the connected players of this arrival
            event = SBcArrivedEvent(pname, cell.coords, facing)
            self._em.post(event)
            
        else: 
            # player was already connected, 
            # or his pname had not been removed when he disconnected
            self.log.warning(pname, ' was already in connected players ; '
                             + 'self.player_positions[pname] may have been corrupted?')
    
    
    def player_left(self, event):
        """ remove player's avatar from game state and notify everyone """
        
        pname = event.pname
        
        try:
            del self.players[pname]
            # TODO: should call Avatar.logout() to have avatar.cell.rm_occ()
            self.log.info(pname + ' left.')
        except KeyError:
            self.log.error('Tried to remove player ' + pname + 
                  ', but it was not found in player list')
        
        event = SBcLeftEvent(pname)
        self._em.post(event)
        
        

    #########################################################################
            
    def on_playerchangedname(self, event):
        """ Change player's name only if the new name is not taken already. """
        
        oldname, newname = event.oldname, event.newname
        
        if newname not in self.players:
            self.log.info(oldname + ' changed name into ' + newname)
            player = self.players[oldname]
            player.change_name(newname)
            # notify the cell the player is currently on
            player.cell.occ_chngname(oldname, newname)
            self.players[newname] = player
            del self.players[oldname]
                        
            event = SBcNameChangeEvent(oldname, newname)
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
            event = SBcChatEvent(pname, txt)
            self._em.post(event)



    ##########################################################################
    
    def on_playermoved(self, event):
        """ when a player moves, notify all of them """
        pname, coords, facing = event.pname, event.coords, event.facing
        
        if self.world.iswalkable(coords):
            player = self.players[pname]

            # remove player from old cell and add player to new cell
            oldcell = player.cell
            newcell = self.world.get_cell(coords)
            oldcell.rm_occ(pname)
            newcell.add_occ(pname)
            player.move(newcell, facing)
            
            #self.log.debug(name + ' moved to ' + str(newcell.coords))
            event = SBroadcastMoveEvent(pname, newcell.coords, facing)
            self._em.post(event)

        else:
            self.log.warn('Possible cheat: ' + pname 
                          + ' walks in non-walkable cell' + str(coords))
            




    ##########################################################################
    
    def on_charattacked(self, event):
        """ when a creep or player attacks, it can only inflict dmg 
        to creeps or players in adjacent cells.
        Note: this allows for creep infighting and player friendly fire.
        """
        atker = self.get_charactor(event.atker)
        defer = self.get_charactor(event.defer)        
        
        # check that atker is facing the defer 
        # and that atker is in adjacent cell of defer
        atkercell = atker.cell
        targetcell = atkercell.get_adjacent_cell(atker.facing)
        if targetcell == defer.cell: 
            self.log.debug(event.atker + ' attacked ' + event.defer)
            defer.rcv_atk(atker) # take defense into account
        



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
            




#############################################################################
    
class SAvatar(SCharactor):
    """ represents a player in the game world """
    
    log = logging.getLogger('server')


    def __init__(self, em, pname, cell, facing):
        SCharactor.__init__(self, pname, cell, facing, 10, 6)
        self._em = em
        
        
    def __str__(self):
        args = self.name, str(self.cell.coord), self.hp, id(self)
        return '<SAvatar %s at %s, hp=%d, id=%s>' % args

    def move(self, cell, facing):
        self.cell = cell
        self.facing = facing
        # TODO: should ask for movement broadcast
        
    def attack(self, defer):
        pass # TODO:
    
    def rcv_atk(self, atker):
        dmg = atker.atk
        self.hp -= dmg
        self.log.debug('Player %s received %d dmg' % (self.name, dmg))
        
        ev = SBcAtkEvent(atker.name, self.name, dmg)
        self._em.post(ev)
        
        # less than 0 HP => death
        if self.hp <= 0:
            self.die()
            
    def die(self):
        self.log.info('Player %s should die' % self.name)
        self.hp = 10 # TODO: should really die instead

