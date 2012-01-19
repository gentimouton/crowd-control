from client2.config import config_get_mapname
from client2.constants import DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT, \
    DIRECTION_UP
from client2.events import CharactorMoveRequest, ModelBuiltMapEvent, \
    CharactorPlaceEvent, NetworkReceivedChatEvent, ChatlogUpdatedEvent, \
    CharactorMoveEvent, ServerGreetEvent, ServerNameChange, ServerPlayerArrived, \
    ServerPlayerLeft
from collections import deque
from weakref import WeakValueDictionary
import os



class Game:
    """ The top of the model. Contains players and map. """

    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        self.players = dict()
        self.map = Map(evManager)
        self.chatlog = ChatLog(evManager)


    def add_player(self, name, pos):
        """ add a new player to the list of connected players """
        sector = self.map.get_sector(pos)
        newplayer = Player(name, sector, self.evManager)       
        self.players[name] = newplayer
        
        
    def remove_player(self, name):
        """ remove a player """
        del self.players[name]
    
    
    def update_player_name(self, oldname, newname):
        """ update a player's name """ 
        if newname in self.players:
            print('Warning from model:', oldname, 'changed name to', newname,
                  'which was already in use')
        
        player = self.players[oldname]
        player.name = newname # TODO: setter instead?
        self.players[newname] = player
        del self.players[oldname]


    
    def start_map(self, mapname):
        """ load map from file """
        self.mapname = mapname
        if config_get_mapname() != self.mapname:
            print('---- Warning: the server map (', self.mapname ,
                   ') is not the client map (', config_get_mapname(), ')') 
        self.map.build_world(self.mapname)
        #self.map.make_path() # TODO: make path

    
    
    def notify(self, event):
        # add/remove players when they join in/leave
        if isinstance(event, ServerPlayerArrived):
            self.add_player(event.playername, event.pos)
        if isinstance(event, ServerPlayerLeft):
            self.remove_player(event.playername)
        # update players' names when they change it
        if isinstance(event, ServerNameChange):
            self.update_player_name(event.oldname, event.newname)
            
        # when the server greets me, build map and set my name 
        if isinstance(event, ServerGreetEvent):
            # map stuffs
            self.start_map(event.mapname)
            
            # players stuff
            for name, pos in event.onlineppl.items():
                self.add_player(name, pos)
            self.myname = event.newname 
            # TODO: self.myname is going to be needed to know which avatar this client can move
            self.add_player(event.newname, event.newpos)
            

        



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



##############################################################################



class Player(object):
    """ the model structure for a person playing the game 
    It has name, score, etc. 
    """
    def __init__(self, name, sector, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        self.name = name
        self.charactors = [ Charactor(sector, evManager) ]


    def __str__(self):
        return '<Player %s %s>' % (self.name, id(self))



    def notify(self, event):
        pass



##############################################################################


class Charactor:
    """ An entity controlled by a player """

    def __init__(self, sector, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        self.sector = sector        
        ev = CharactorPlaceEvent(self, sector)
        self.evManager.post(ev)
        



    def __str__(self):
        return '<Charactor %s>' % id(self)


    def move_if_allowed(self, direction):
        """ move towards that direction if possible """
        if self.sector.move_possible(direction):
            newSector = self.sector.neighbors[direction]
            self.sector = newSector
            ev = CharactorMoveEvent(self)
            self.evManager.post(ev)



    def notify(self, event):
        """ ... """
        if isinstance(event, CharactorMoveRequest):
            self.move_if_allowed(event.direction)



##############################################################################



class Map:
    """..."""

    def __init__(self, evManager):
        """ ... """

        self.evManager = evManager
        #self.evManager.register_listener(self)
        
        
        
    def build_world(self, mapname):
        """ open map file and build the map from it
        TODO: this should be shared between server and client 
        """
        
        f = open(os.path.join(os.pardir, 'maps', mapname))
        lines = f.readlines() #might be optimized: for line in open("file.txt"):
        self.cellgrid = [] #contains game board

        # sanity checks on map width and height
        self.width = len(lines)
        if self.width == 0:
            print('Warning: map', mapname, 'has no lines.')
        else:
            self.height = len(lines[0].strip().split(','))
            if self.height == 0:
                print('Waning: the first line of map', mapname, 'has no cells.')
        
        # build the cell matrix
        for j in range(self.width): 
            tmprow = []
            line = lines[j].strip().split(',')
            
            for i in range(len(line)):
                cellvalue = line[i]
                coords = i, j
                if cellvalue == 'E':#entrance is walkable
                    self.entrance_coords = coords
                    tmprow.append(Sector(coords, 1, self.evManager)) 
                elif cellvalue == 'L':#lair is walkable
                    self.lair_coords = coords
                    tmprow.append(Sector(coords, 1, self.evManager)) 
                else:
                    tmprow.append(Sector(coords, line[i], self.evManager))
            
            self.cellgrid.append(tmprow)
        
        ev = ModelBuiltMapEvent(self)
        self.evManager.post(ev)

        
        
    def make_path(self):  
        """ assign to each cell a distance from the entrance: 
        distance(entrance) = 0,
        and then have each cell with an assigned distance 
        sets recursively its neighbors' distance   
        """

        def recursive_dist_fill(cell, newdist):
            """ only assign distance to walkable cells """
            if cell.iswalkable() and cell.get_dist_from_entrance() > newdist:
                cell.set_dist_from_entrance(newdist)
                for neighborcell in self._get_adjacent_walkable_cells(cell):
                    recursive_dist_fill(neighborcell, newdist + 1)
            return
        
        # start filling from the entrance with distance=0
        recursive_dist_fill(self.get_sector(self.entrance_coords), 0)
        return



    def get_sector(self, xy, y=None):
        """ cell from coords;
        accepts get_sector(x,y) or get_sector(coords)
        """ 
        if y is not None: #y can be 0
            return self.cellgrid[xy][y]
        else:
            x, y = xy
            return self.cellgrid[x][y]
        

##############################################################################



class Sector:
    """..."""
    def __init__(self, coords, walkable, evManager):
        self.evManager = evManager
        #self.evManager.register_listener( self )

        self.iswalkable = walkable
        
        self.neighbors = dict()

        self.neighbors[DIRECTION_UP] = None
        self.neighbors[DIRECTION_DOWN] = None
        self.neighbors[DIRECTION_LEFT] = None
        self.neighbors[DIRECTION_RIGHT] = None

    def iswalkable(self):
        return self.iswalkable
    
    def move_possible(self, direction):
        if self.neighbors[direction]:
            return True

