from client2.config import config_get_mapname
from client2.constants import DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT, \
    DIRECTION_UP
from client2.events import CharactorMoveRequest, ModelBuiltMapEvent, \
    CharactorPlaceEvent, NetworkReceivedChatEvent, ChatlogUpdatedEvent, \
    CharactorMoveEvent, ServerGreetEvent, ServerNameChange, ServerPlayerArrived, \
    ServerPlayerLeft
from collections import deque
import os



class Game:
    """ The top of the model. Contains players and map. """

    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        self.players = dict()
        self.map = World(evManager)
        self.chatlog = ChatLog(evManager)


    def add_player(self, name, pos):
        """ add a new player to the list of connected players """
        cell = self.map.get_cell(pos)
        newplayer = Player(name, cell, self.evManager)       
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
    def __init__(self, name, cell, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        self.name = name
        self.charactors = [ Charactor(cell, evManager) ]


    def __str__(self):
        return '<Player %s %s>' % (self.name, id(self))



    def notify(self, event):
        pass



##############################################################################


class Charactor:
    """ An entity controlled by a player """

    def __init__(self, cell, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        self.cell = cell        
        ev = CharactorPlaceEvent(self, cell)
        self.evManager.post(ev)
        


    def __str__(self):
        return '<Charactor %s>' % id(self)


    def move_if_allowed(self, direction):
        """ move towards that direction if possible """
        dest_cell = self.cell.get_adjacent_cell(direction)
        if dest_cell:
            self.cell = dest_cell
            ev = CharactorMoveEvent(self, dest_cell.coords)
            self.evManager.post(ev)
        else:
            pass #TODO: give (audio?) feedback that move is not possible



    def notify(self, event):
        """ ... """
        if isinstance(event, CharactorMoveRequest):
            self.move_if_allowed(event.direction)



##############################################################################



class World:
    """..."""

    def __init__(self, evManager):
        """ ... """

        self.evManager = evManager
        #self.evManager.register_listener(self)
        
        
    def matrix_transpose(self, a):
        """ matrix transposition: return matrix_transpose(a)
        TODO: move this into tools, or better: build the map correctly directly
         """
        assert(a[0] and a)
        return [[a[i][j] for i in range(len(a))] for j in range(len(a[0]))]
    
    
    
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
                    tmprow.append(Cell(self, coords, 1, self.evManager)) 
                elif cellvalue == 'L':#lair is walkable
                    self.lair_coords = coords
                    tmprow.append(Cell(self, coords, 1, self.evManager)) 
                else:
                    tmprow.append(Cell(self, coords, line[i], self.evManager))
            
            self.cellgrid.append(tmprow)
        self.cellgrid = self.matrix_transpose(self.cellgrid)
        
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
            if cell.iswalkable and cell.get_dist_from_entrance() > newdist:
                cell.set_dist_from_entrance(newdist)
                for neighborcell in self._get_adjacent_walkable_cells(cell):
                    recursive_dist_fill(neighborcell, newdist + 1)
            return
        
        # start filling from the entrance with distance=0
        recursive_dist_fill(self.get_cell(self.entrance_coords), 0)
        return



    def get_cell(self, tl, left=None):
        """ cell from coords;
        accepts get_cell(top,left) or get_cell(coords)
        """ 
        try:
            if left is not None: #left can be 0, and 0 != None
                return self.cellgrid[tl][left]
            else:
                top, left = tl
                return self.cellgrid[top][left]
        except IndexError: #outside of the map
            return None


##############################################################################



class Cell:
    """..."""
    def __init__(self, world, coords, walkable, evManager):
        self.evManager = evManager
        #self.evManager.register_listener( self )
        self.top, self.left = self.coords = coords
        self.world = world
        self.iswalkable = walkable
                    
    
    def __str__(self):
        return '<Cell %s %s>' % (self.coords, id(self))
    
    
    def get_adjacent_cell(self, direction):
        if direction == DIRECTION_UP: # TODO: use 'is' instead of '=='?
            dest_coords = self.top - 1, self.left
        elif direction == DIRECTION_DOWN:
            dest_coords = self.top + 1, self.left
        elif direction == DIRECTION_LEFT:
            dest_coords = self.top, self.left - 1
        elif direction == DIRECTION_RIGHT:
            dest_coords = self.top, self.left + 1
        
        dest_cell = self.world.get_cell(dest_coords) 
        if dest_cell and dest_cell.iswalkable:
            return dest_cell
        else: #non walkable or out of grid
            return None
            
                
