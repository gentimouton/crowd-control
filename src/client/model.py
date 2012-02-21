from client.events_client import MoveMyAvatarRequest, ModelBuiltMapEvent, \
    NetworkReceivedChatEvent, ChatlogUpdatedEvent, ClGreetEvent, ClPlayerLeft, \
    CharactorRemoveEvent, NetworkReceivedAvatarMoveEvent, ClPlayerArrived, \
    ClNameChangeEvent, LocalAvatarPlaceEvent, OtherAvatarPlaceEvent, \
    LocalAvatarMoveEvent, RemoteCharactorMoveEvent, NetworkReceivedGameStartEvent, \
    NetworkReceivedCreepJoinEvent, CreepPlaceEvent, NetworkReceivedCreepMoveEvent
from collections import deque
from common.world import World
import logging





class Game:
    """ The top of the model. Contains players and world. """

    log = logging.getLogger('client')
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(ClGreetEvent, self.greeted)
        # all other callbacks are registered AFTER having been greeted
        
        self.players = dict() #unlike WeakValueDict, I need to remove players manually
        self.creeps = dict() #need to remove creeps manually when they die
        
        self.world = World(evManager)
        self.chatlog = ChatLog(evManager)


    ########################################################################

        
    def build_map(self, mapname):
        """ load world from file """
        self.mapname = mapname
        self.world.build_world(self.mapname, ModelBuiltMapEvent)

    
    
    def greeted(self, event):
        """ When the server greets me, set my name,
        start world building process, and add other connected players.
        Start also listening to player inputs, and other network messages.
        """
        
        mapname, newname = event.mapname, event.newname
        newpos, onlineppl = event.newpos, event.onlineppl
        creeps = event.creeps
            
        self.myname = newname
        
        self.build_map(mapname)
        
        # creeps
        for cid, coords in creeps.items():
            self.on_creepplace(cid, coords)
            
        # myself, local player
        self.add_player(newname, newpos)
        # others, remote players
        for name, pos in onlineppl.items():
            self.add_player(name, pos)
           
        # start listening to game events coming from the network
        
        # -- PLAYERS
        self._em.reg_cb(ClPlayerArrived, self.on_playerjoin)
        self._em.reg_cb(ClPlayerLeft, self.on_playerleft)
        self._em.reg_cb(ClNameChangeEvent, self.on_namechange)
        
        # -- AVATARS (remote and local)
        self._em.reg_cb(NetworkReceivedAvatarMoveEvent, self.on_remoteavmove)
        self._em.reg_cb(MoveMyAvatarRequest, self.on_localavmove)
        
        # -- RUNNING GAME and CREEPS
        self._em.reg_cb(NetworkReceivedGameStartEvent, self.on_gamestart)
        self._em.reg_cb(NetworkReceivedCreepJoinEvent, self.on_creepjoin)
        self._em.reg_cb(NetworkReceivedCreepMoveEvent, self.on_creepmove)
        
        


    ##################  PLAYERS  #####################################
    
    def on_playerjoin(self, event):
        """ When a new player arrives, add him to the connected players. """
        self.add_player(event.pname, event.pos)
        
        
    def add_player(self, pname, pos):
        """ add a new player to the list of connected players """
        cell = self.world.get_cell(pos)
        
        # whether that Player is the local client or a remote client
        islocal = hasattr(self, 'myname') and pname == self.myname 
        
        newplayer = Player(pname, cell, islocal, self._em)       
        self.players[pname] = newplayer
        
        
    def on_playerleft(self, event):
        """ remove a player """
        pname = event.playername
        try:
            self.players[pname].remove()
            #don't forget to clean the player data from the dict
            del self.players[pname]
        except KeyError:
            self.log.error('Player' + pname + ' had already been removed') 
        
            
    
    def on_namechange(self, event):
        """ update players' names when they change it """
        
        oldname, newname = event.oldname, event.newname
         
        if newname in self.players:
            self.log.warning(oldname + ' changed name to ' + newname 
                             + ' which was already in use')
        
        if self.myname == oldname:
            self.myname = newname
            
        player = self.players[oldname]
        player.name = newname
        self.players[newname] = player
        del self.players[oldname] #only del the mapping, not the player itself


    
    ###############################  AVATARS  ############################
        
    
    def on_remoteavmove(self, event):
        """ Move the avatar of the player which name is pname. """
        pname, dest = event.pname, event.dest
        
        if pname != self.myname:
            avatar = self.players[pname].avatar
            destcell = self.world.get_cell(dest)
            avatar.move_absolute(destcell)


    def on_localavmove(self, event):
        """ When the user pressed up,down,right,or left, move his avatar. """
        mychar = self.players[self.myname].avatar
        mychar.move_relative(event.direction)


    
    ###################### RUNNING GAME + CREEPS ############################
    
    def on_gamestart(self, event):
        self.log.info(event.pname + ' started the game')

    
    def on_creepjoin(self, event):
        """ Create a creep. """
        cid, coords = event.cid, event.coords
        self.on_creepplace(cid, coords)
        
        
    def on_creepmove(self, event):
        """ Move a creep. """
        cid, coords = event.cid, event.coords
        creep = self.creeps[cid]
        creep.move_absolute(self.world.get_cell(coords))
        
        
    def on_creepplace(self, cid, coords):
        """ Add a new creep to the existing creeps. """
        cell = self.world.get_cell(coords)
        creep = Creep(self._em, cid, cell)       
        self.creeps[cid] = creep



        
##############################################################################



class Player():
    """ the model structure for a person playing the game 
    It has name, score, etc. 
    """
    def __init__(self, name, cell, islocal, evManager):
        self._em = evManager

        self.name = name
        self.avatar = Avatar(self, cell, islocal, evManager) 


    def __str__(self):
        return '<Player %s %s>' % (self.name, id(self))


    def remove(self):
        """ tell the view to remove that avatar """
        ev = CharactorRemoveEvent(self.avatar)
        self._em.post(ev)





##############################################################################


class Charactor():
    """ A local or remote entity representing players or creeps. 
    It is located on a cell, and can move to another cell.
    """
    
    log = logging.getLogger('client')

    def __init__(self, cell, name, evManager):
        self._em = evManager
        self.cell = cell
        self.name = name

    def move_absolute(self, destcell):
        """ move to the specified destination """ 
        if destcell:
            self.cell = destcell
            ev = RemoteCharactorMoveEvent(self, destcell.coords)
            self._em.post(ev)
            
        else: #illegal move
            self.log.warning('Illegal move from ' + self.name)
            #TODO: should report to server of potential cheat/hack
            pass
        
    
    
class Avatar(Charactor):
    """ An entity controlled by a player.
    Right now, the mapping is 1-to-1: one avatar per player. 
    """
    
    def __init__(self, player, cell, islocal, evManager):
        
        self.player = player
        Charactor.__init__(self, cell, self.player.name, evManager)
        
        self.islocal = islocal #whether the avatar is controlled by the client
        
        if islocal:
            ev = LocalAvatarPlaceEvent(self, cell)
        else:
            ev = OtherAvatarPlaceEvent(self, cell)
        self._em.post(ev)
        

    def __str__(self):
        return '<Avatar %s from player %s>' % (id(self), self.player.name)


    def move_relative(self, direction):
        """ move towards that direction if possible """

        dest_cell = self.cell.get_adjacent_cell(direction)
        if dest_cell:
            self.cell = dest_cell
            # send to view and server that I moved
            ev = LocalAvatarMoveEvent(self, dest_cell.coords)
            self._em.post(ev)

        else: #move is not possible: TODO: give (audio?) feedback 
            pass 



class Creep(Charactor):
    """ Representation of a remote enemy monster. """
        
    def __init__(self, evManager, cid, cell):
        
        Charactor.__init__(self, cell, str(cid), evManager)
        
        ev = CreepPlaceEvent(self, cell)# ask view to display the new creep
        self._em.post(ev)
        
    
    def __str__(self):
        return '<Creep %s named %s>' % (id(self), self.name)


        

########################### CHATLOG ####################################


class ChatLog():
    """ store all that deals with the chat window """
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(NetworkReceivedChatEvent, self.add_chatmsg)
        
        #double-ended queue to remember the most recent 30 messages
        self.chatlog = deque(maxlen=30) 
            
    
    
    def add_chatmsg(self, event):
        """ add a message to the chatlog.
        if full, remove oldest message 
        """
        author, txt = event.pname, event.txt
        msg = {'pname':author, 'text':txt}
        self.chatlog.appendleft(msg)
        
        ev = ChatlogUpdatedEvent(author, txt)
        self._em.post(ev)


    
