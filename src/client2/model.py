from client2.config import config_get_mapname
from client2.constants import DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT, \
    DIRECTION_UP
from client2.events_client import MyCharactorMoveRequest, ModelBuiltMapEvent, \
    CharactorPlaceEvent, NetworkReceivedChatEvent, ChatlogUpdatedEvent, \
    CharactorMoveEvent, ServerGreetEvent, ServerNameChangeEvent, ServerPlayerArrived, \
    ServerPlayerLeft, CharactorRemoveEvent, NetworkReceivedCharactorMoveEvent, \
    SendCharactorMoveEvent
from collections import deque
import os



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
        self.map.build_world(self.mapname)
        #self.map.make_path() # TODO: make path

    
    
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
        # TODO: check that moving to destcell is a legal move
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


##############################################################################



class World:
    """..."""

    def __init__(self, evManager):
        """ ... """

        self.evManager = evManager
        #self.evManager.register_listener(self)
        
    def __str__(self):
        return '<World %s>' % (id(self))

    
    
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
                coords = j, i
                cellvalue = line[i]
                if cellvalue == 'E':#entrance is walkable
                    self.entrance_coords = coords # TODO: should be a list of coords
                    walkable = 1
                elif cellvalue == 'L':
                    self.lair_coords = coords # TODO: should be a list of coords
                    walkable = 1
                else:
                    walkable = int(cellvalue) # 0 or 1
                cell = Cell(self, coords, walkable, self.evManager)
                tmprow.append(cell)
            
            self.cellgrid.append(tmprow) 
            #such that cellgrid[i][j] = i-th cell from top, j-th from left
        
        # set the entrances and lair cells
        e_coords = self.entrance_coords
        if e_coords:
            cell = self.get_cell(e_coords)
            cell.set_entrance(True)
        l_coords = self.lair_coords
        if l_coords:
            cell = self.get_cell(l_coords)
            cell.set_lair(True)
        
        ev = ModelBuiltMapEvent(self)
        self.evManager.post(ev)




    def get_cell(self, tl, left=None):
        """ cell from coords;
        accepts get_cell(top,left) or get_cell(coords)
        """ 
        try:
            if left is not None: #left can be 0, and 0 != None
                if -1 in [tl, left]: # outside of the map
                    return None
                else:
                    return self.cellgrid[tl][left]
            else: #left was specified
                if -1 in tl:
                    return None
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
            
    def set_entrance(self, value):
        self.isentrance = value
    def set_lair(self, value):
        self.islair = value
        
