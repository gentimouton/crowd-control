from client2.config import config_get_mapname
from client2.events_client import MyCharactorMoveRequest, ModelBuiltMapEvent, \
    CharactorPlaceEvent, NetworkReceivedChatEvent, ChatlogUpdatedEvent, \
    CharactorMoveEvent, ServerGreetEvent, ServerNameChangeEvent, ServerPlayerArrived, \
    ServerPlayerLeft, CharactorRemoveEvent, NetworkReceivedCharactorMoveEvent, \
    SendCharactorMoveEvent
from collections import deque
from common.world import World




class Game:
    """ The top of the model. Contains players and map. """

    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        self.players = dict() #unlike WeakValueDict, I need to remove players manually
        self.map = World(evManager)
        self.chatlog = ChatLog(evManager)


    def add_player(self, name, pos):
        """ add a new player to the list of connected players """
        cell = self.map.get_cell(pos)
        newplayer = Player(name, cell, self.evManager)       
        self.players[name] = newplayer
        
        
    def remove_player(self, name):
        """ remove a player """
        self.players[name].remove() 
        #remove the player data structure since self.players is a normal dict
        del self.players[name]
    
    
    def update_player_name(self, oldname, newname):
        """ update a player's name """ 
        if newname in self.players:
            print('Warning from model:', oldname, 'changed name to', newname,
                  'which was already in use')
        
        if self.myname == oldname:
            self.myname = newname
            
        player = self.players[oldname]
        player.name = newname
        self.players[newname] = player
        del self.players[oldname] #only del the mapping, not the player itself


    
    def start_map(self, mapname):
        """ load map from file """
        self.mapname = mapname
        if config_get_mapname() != self.mapname:
            print('---- Warning: the server map (', self.mapname ,
                   ') is not the client map (', config_get_mapname(), ')') 
        self.map.build_world(self.mapname, ModelBuiltMapEvent)

    
    
    def notify(self, event):
        # add/remove players when they join in/leave
        if isinstance(event, ServerPlayerArrived):
            self.add_player(event.playername, event.pos)
        if isinstance(event, ServerPlayerLeft):
            self.remove_player(event.playername)
            
        # update players' names when they change it
        if isinstance(event, ServerNameChangeEvent):
            self.update_player_name(event.oldname, event.newname)
            
        # when the server greets me, build map and set my name 
        if isinstance(event, ServerGreetEvent):
            # map stuffs
            self.start_map(event.mapname)
            
            # players stuff
            for name, pos in event.onlineppl.items():
                self.add_player(name, pos)
            self.myname = event.newname 
            self.add_player(event.newname, event.newpos)
            
        # when the user pressed up,down,right,or left, move his charactor
        # TODO: location-related events should be in Map
        if isinstance(event, MyCharactorMoveRequest):
            mychar = self.players[self.myname].charactor
            mychar.move_relative(event.direction)

        # TODO: should be in Map?
        if isinstance(event, NetworkReceivedCharactorMoveEvent):
            pname = event.author
            if pname != self.myname: #TODO: track my own updates inside a 'ghost' appearance 
                charactor = self.players[event.author].charactor
                destcell = self.map.get_cell(event.dest)
                charactor.move_absolute(destcell)



##############################################################################



class Player(object):
    """ the model structure for a person playing the game 
    It has name, score, etc. 
    """
    def __init__(self, name, cell, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        self.name = name
        self.charactor = Charactor(self, cell, evManager) 


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
    Right now, the mapping is 1-to-1: one charactor per player. """

    def __init__(self, player, cell, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        self.player = player
        self.cell = cell        
        ev = CharactorPlaceEvent(self, cell)
        self.evManager.post(ev)
        


    def __str__(self):
        return '<Charactor %s from player %s>' % (id(self), self.player.name)


    def move_relative(self, direction):
        """ move towards that direction if possible """
        dest_cell = self.cell.get_adjacent_cell(direction)
        if dest_cell:
            self.cell = dest_cell
            # send to server that I moved
            ev = SendCharactorMoveEvent(self, dest_cell.coords)
            self.evManager.post(ev)
            # send to view that I moved
            ev = CharactorMoveEvent(self, dest_cell.coords)
            self.evManager.post(ev)
        else:
            pass #TODO: give (audio?) feedback that move is not possible


    def move_absolute(self, destcell):
        # TODO: check that moving to destcell is a legal move. 
        #If illegal move, report to server of potential cheat/hack
        self.cell = destcell
        ev = CharactorMoveEvent(self, destcell.coords)
        self.evManager.post(ev)


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
            msg = {'author':event.author, 'text':event.text}
            self.add_chatmsg(msg)
            
            
    def add_chatmsg(self, msg):
        """ add a message to the chatlog.
        if full, remove oldest message 
        """
        self.chatlog.appendleft(msg)
        
        ev = ChatlogUpdatedEvent(msg['author'], msg['text'])
        self.evManager.post(ev)


    
