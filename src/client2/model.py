from client2.events_client import MoveMyCharactorRequest, ModelBuiltMapEvent, \
    NetworkReceivedChatEvent, ChatlogUpdatedEvent, ClGreetEvent, ClPlayerLeft, \
    CharactorRemoveEvent, NetworkReceivedCharactorMoveEvent, ClPlayerArrived, \
    ClNameChangeEvent, LocalCharactorPlaceEvent, OtherCharactorPlaceEvent, \
    LocalCharactorMoveEvent, RemoteCharactorMoveEvent
from collections import deque
from common.world import World
import logging





class Game:
    """ The top of the model. Contains players and world. """

    log = logging.getLogger('client')
    
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        self.players = dict() #unlike WeakValueDict, I need to remove players manually
        self.world = World(evManager)
        self.chatlog = ChatLog(evManager)


    def add_player(self, name, pos):
        """ add a new player to the list of connected players """
        cell = self.world.get_cell(pos)
        if hasattr(self, 'myname') and name == self.myname:
            islocal = True # whether that Player is controlled by the client 
        else:
            islocal = False
        newplayer = Player(name, cell, islocal, self.evManager)       
        self.players[name] = newplayer
        
        
    def remove_player(self, name):
        """ remove a player """
        try:
            self.players[name].remove()
            #don't forget to clean the player data from the dict
            del self.players[name]
        except KeyError:
            self.log.error('Player' + name + ' had already been removed') 
        
            
    
    def update_player_name(self, oldname, newname):
        """ update a player's name """ 
        if newname in self.players:
            self.log.warning(oldname + ' changed name to ' + newname 
                             + ' which was already in use')
        
        if self.myname == oldname:
            self.myname = newname
            
        player = self.players[oldname]
        player.name = newname
        self.players[newname] = player
        del self.players[oldname] #only del the mapping, not the player itself


    
    def start_map(self, mapname):
        """ load world from file """
        self.mapname = mapname
        self.world.build_world(self.mapname, ModelBuiltMapEvent)

    
    def greeted(self, mapname, newname, newpos, onlineppl):
        """ start world builing process and add already connected players """
        self.start_map(mapname)
            
        self.myname = newname 
        self.add_player(newname, newpos)
        
        for name, pos in onlineppl.items():
            self.add_player(name, pos)
            
    
    
    def move_charactor(self, pname, dest):
        """move the charactor of the player which name is pname
        #TODO: track my own updates inside a 'ghost' appearance
        """
        if pname != self.myname:
            charactor = self.players[pname].charactor
            destcell = self.world.get_cell(dest)
            charactor.move_absolute(destcell)

            
    def notify(self, event):
        # add/remove players when they join in/leave
        if isinstance(event, ClPlayerArrived):
            self.add_player(event.playername, event.pos)
        if isinstance(event, ClPlayerLeft):
            self.remove_player(event.playername)
            
        # update players' names when they change it
        if isinstance(event, ClNameChangeEvent):
            self.update_player_name(event.oldname, event.newname)
            
        # when the server greets me, build world and set my name 
        if isinstance(event, ClGreetEvent):
            self.greeted(event.mapname, event.newname, event.newpos, event.onlineppl)
            
        # when the user pressed up,down,right,or left, move his charactor
        # TODO: location-related events should be in Map?
        if isinstance(event, MoveMyCharactorRequest):
            mychar = self.players[self.myname].charactor
            mychar.move_relative(event.direction)

        # TODO: should be in Map?
        if isinstance(event, NetworkReceivedCharactorMoveEvent):
            self.move_charactor(event.author, event.dest)



##############################################################################



class Player(object):
    """ the model structure for a person playing the game 
    It has name, score, etc. 
    """
    def __init__(self, name, cell, islocal, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        self.name = name
        self.charactor = Charactor(self, cell, islocal, evManager) 


    def __str__(self):
        return '<Player %s %s>' % (self.name, id(self))


    def remove(self):
        """ tell the view to remove that charactor """
        ev = CharactorRemoveEvent(self.charactor)
        self.evManager.post(ev)


    def notify(self, event):
        pass



##############################################################################


class Charactor:
    """ An entity controlled by a player.
    Right now, the mapping is 1-to-1: one charactor per player. 
    """
    log = logging.getLogger('client')

    def __init__(self, player, cell, islocal, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        self.player = player
        self.cell = cell
        self.islocal = islocal #whether the charactor is controlled by the client
        
        if islocal:
            ev = LocalCharactorPlaceEvent(self, cell)
        else:
            ev = OtherCharactorPlaceEvent(self, cell)
        self.evManager.post(ev)
        


    def __str__(self):
        return '<Charactor %s from player %s>' % (id(self), self.player.name)


    def move_relative(self, direction):
        """ move towards that direction if possible """
        dest_cell = self.cell.get_adjacent_cell(direction)
        if dest_cell:
            self.cell = dest_cell
            # send to view and server that I moved
            ev = LocalCharactorMoveEvent(self, dest_cell.coords)
            self.evManager.post(ev)
        else:
            pass #TODO: give (audio?) feedback that move is not possible


    def move_absolute(self, destcell):
        """ move to the specified destination """ 
        if destcell:
            self.cell = destcell
            ev = RemoteCharactorMoveEvent(self, destcell.coords)
            self.evManager.post(ev)
        else:
            self.log.warning('Illegal move from ' + self.player.name 
                             + ' towards ' + str(destcell.coords))
            #TODO: should report to server of potential cheat/hack
            pass


    def notify(self, event):
        """ ... """
        pass



##############################################################################


class ChatLog(object):
    """ store all that deals with the chat window """
    
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        #double-ended queue to remember the most recent 30 messages
        self.chatlog = deque(maxlen=30) 


    def notify(self, event):
        """ """
        if isinstance(event, NetworkReceivedChatEvent):
            self.add_chatmsg(event.author, event.txt)
            
            
    def add_chatmsg(self, author, txt):
        """ add a message to the chatlog.
        if full, remove oldest message 
        """
        msg = {'author':author, 'text':txt}
        self.chatlog.appendleft(msg)
        
        ev = ChatlogUpdatedEvent(author, txt)
        self.evManager.post(ev)


    
