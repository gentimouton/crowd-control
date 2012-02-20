from client.events_client import MoveMyCharactorRequest, ModelBuiltMapEvent, \
    NetworkReceivedChatEvent, ChatlogUpdatedEvent, ClGreetEvent, ClPlayerLeft, \
    CharactorRemoveEvent, NetworkReceivedCharactorMoveEvent, ClPlayerArrived, \
    ClNameChangeEvent, LocalCharactorPlaceEvent, OtherCharactorPlaceEvent, \
    LocalCharactorMoveEvent, RemoteCharactorMoveEvent, NetworkReceivedGameStartEvent, \
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


    def on_playerarrived(self, event):
        """ When a new player arrives, add him to the connected players. """
        self.add_player(event.pname, event.pos)
        
        
    def add_player(self, name, pos):
        """ add a new player to the list of connected players """
        cell = self.world.get_cell(pos)
        if hasattr(self, 'myname') and name == self.myname:
            islocal = True # whether that Player is controlled by the client 
        else:
            islocal = False
        newplayer = Player(name, cell, islocal, self._em)       
        self.players[name] = newplayer
        
        
    def remove_player(self, event):
        """ remove a player """
        name = event.playername
        try:
            self.players[name].remove()
            #don't forget to clean the player data from the dict
            del self.players[name]
        except KeyError:
            self.log.error('Player' + name + ' had already been removed') 
        
            
    
    def update_player_name(self, event):
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


    
    def build_map(self, mapname):
        """ load world from file """
        self.mapname = mapname
        self.world.build_world(self.mapname, ModelBuiltMapEvent)

    
    
    def on_gamestart(self, event):
        self.log.info(event.pname + ' started the game')
    
    ################################ creeps ##########################
    
    def on_creepjoined(self, event):
        self.log.info('Creep %d appeared' % (str(event.cid))) 
        
    def on_creepmoved(self, event):
        cid, coords = event.cid, event.coords
        creep = self.creeps[cid]
        cell = self.world.get_cell(coords)
        creep.move_absolute(cell)
        
        
    def add_creep(self, cid, pos):
        """ Add a new creep to the list of existing creeps. """
        cell = self.world.get_cell(pos)
        creep = Creep(self._em, cid, cell)       
        self.creeps[cid] = creep


    ############################### admin ############################    
    
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
            self.add_creep(cid, coords)
            
        # my avatar
        self.add_player(newname, newpos)
        # other avatars
        for name, pos in onlineppl.items():
            self.add_player(name, pos)
           
        # start listening to game events coming from the network
        self._em.reg_cb(NetworkReceivedCharactorMoveEvent, self.move_charactor)
        self._em.reg_cb(ClPlayerLeft, self.remove_player)
        self._em.reg_cb(ClPlayerArrived, self.on_playerarrived) 
        self._em.reg_cb(ClNameChangeEvent, self.update_player_name)
        self._em.reg_cb(NetworkReceivedGameStartEvent, self.on_gamestart)
        self._em.reg_cb(NetworkReceivedCreepJoinEvent, self.on_creepjoined)
        self._em.reg_cb(NetworkReceivedCreepMoveEvent, self.on_creepmoved)
        
        # start listening to player input events
        self._em.reg_cb(MoveMyCharactorRequest, self.move_char_relative)
        
        
    
    def move_charactor(self, event):
        """move the charactor of the player which name is pname
        #TODO: track my own updates inside a 'ghost' appearance
        # TODO: location-related events should be in Map?
        """
        pname, dest = event.author, event.dest
        
        if pname != self.myname:
            charactor = self.players[pname].charactor
            destcell = self.world.get_cell(dest)
            charactor.move_absolute(destcell)


    def move_char_relative(self, event):
        """ When the user pressed up,down,right,or left, move his charactor
        TODO: location-related events should be in Map?
        """
        mychar = self.players[self.myname].charactor
        mychar.move_relative(event.direction)

        
##############################################################################



class Player():
    """ the model structure for a person playing the game 
    It has name, score, etc. 
    """
    def __init__(self, name, cell, islocal, evManager):
        self._em = evManager

        self.name = name
        self.charactor = Charactor(self, cell, islocal, evManager) 


    def __str__(self):
        return '<Player %s %s>' % (self.name, id(self))


    def remove(self):
        """ tell the view to remove that charactor """
        ev = CharactorRemoveEvent(self.charactor)
        self._em.post(ev)





##############################################################################


class Charactor:
    """ An entity controlled by a player.
    Right now, the mapping is 1-to-1: one charactor per player. 
    """
    log = logging.getLogger('client')

    def __init__(self, player, cell, islocal, evManager):
        self._em = evManager
        
        self.player = player
        self.cell = cell
        self.islocal = islocal #whether the charactor is controlled by the client
        
        if islocal:
            ev = LocalCharactorPlaceEvent(self, cell)
        else:
            ev = OtherCharactorPlaceEvent(self, cell)
        self._em.post(ev)
        


    def __str__(self):
        return '<Charactor %s from player %s>' % (id(self), self.player.name)


    def move_relative(self, direction):
        """ move towards that direction if possible """
                    
        dest_cell = self.cell.get_adjacent_cell(direction)
        if dest_cell:
            self.cell = dest_cell
            # send to view and server that I moved
            ev = LocalCharactorMoveEvent(self, dest_cell.coords)
            self._em.post(ev)
        else:
            pass #TODO: give (audio?) feedback that move is not possible


    def move_absolute(self, destcell):
        """ move to the specified destination """ 
        if destcell:
            self.cell = destcell
            ev = RemoteCharactorMoveEvent(self, destcell.coords)
            self._em.post(ev)
        else:
            self.log.warning('Illegal move from ' + self.player.name)
            #TODO: should report to server of potential cheat/hack
            pass



class Creep():
    """ representation of an ennemy monster """
    
    log = logging.getLogger('client')
    
    def __init__(self, em, cid, cell):
        self._em = em
        self.cid = cid
        self.cell = cell
        
        ev = CreepPlaceEvent(self, cell)# ask view to display the new creep
        self._em.post(ev)
        
    
    def move_absolute(self, destcell):
        """ move creep to the specified destination;
        TODO: refactorable with Player code?
        """ 
        if destcell:
            self.cell = destcell
            ev = RemoteCharactorMoveEvent(self, destcell.coords)
            self._em.post(ev)
        else:
            self.log.warning('Illegal move from creep ' + self.cid)
        

##############################################################################


class ChatLog(object):
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
        author, txt = event.author, event.txt
        msg = {'author':author, 'text':txt}
        self.chatlog.appendleft(msg)
        
        ev = ChatlogUpdatedEvent(author, txt)
        self._em.post(ev)


    
