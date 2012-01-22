from server.config import config_get_mapname
import os

class Mediator():
    
    network = None 
    
    def __init__(self):
        self.player_positions = dict() # maps player names to their positions 
        self.build_world()

    
    def setnetwork(self, nw):
        self.network = nw
        

##############################################################################

    def build_world(self):
        """ open map file and build map from it: 
        TODO: this hsould be shared between client and server """
        self.mapname = config_get_mapname()
        f = open(os.path.join(os.pardir, 'maps', self.mapname))
        #other lines = map in itself
        lines = f.readlines() #might be optimized: for line in open("file.txt"):
        self.cellgrid = [] #contains game board
        for i in range(len(lines)): #for all lines in file
            tmprow = []
            line = lines[i].strip().split(',')
            for j in range(len(line)):
                cellvalue = line[j]
                if cellvalue == 'E':
                    self.entrance_coords = i, j
                    tmprow.append(1) #entrance is walkable
                elif cellvalue == 'L':
                    self.lair_coords = i, j
                    tmprow.append(1) #lair is walkable
                else:
                    tmprow.append(int(line[i]))
            self.cellgrid.append(tmprow)
        
##############################################################################

    
    # (dis)connection and name changes
    # notifying for pausing/resuming the game could also fit in there
        
    def player_left(self, name):
        """ TODO: remove player's avatar from game state 
        and notify everyone """
        #print(name, "disconnected")
        try:
            del self.player_positions[name]
        except KeyError:
            print('Tried to remove player ', name,
                  ', but it was not in player list')
        self.network.broadcast_conn_status('left', name)
        
    def player_arrived(self, name):
        """ create player's avatar and send him the list of connected ppl
        do not include him in the list of connected people """
        #print(name, "connected") #TODO: log
        if name not in self.player_positions:
            onlineppl = self.player_positions.copy()
            self.player_positions[name] = self.entrance_coords
            self.network.greet(self.mapname, name, self.entrance_coords, onlineppl) 
            self.network.broadcast_conn_status('arrived', name, self.entrance_coords)
        else:
            print("Warning:", name, 'was already in connected player_positions')
            print('Possibly, self.player_positions[name] had not been cleaned properly')
    
    


##############################################################################
            
    def handle_name_change(self, oldname, newname):
        """ change player's name only if newname not taken already """
        if newname not in self.player_positions:
            self.player_positions[newname] = self.player_positions[oldname]
            del self.player_positions[oldname]
            #print(oldname, 'changed name into ', newname)
            self.network.broadcast_name_change(oldname, newname)
        else: 
            # TODO: send personal notif to the client who failed to change name
            pass
    
##############################################################################
            
    def received_chat(self, txt, author):
        """ when chat msg received, broadcast it to all connected users """
        # TODO: implement a chat logger as a view
        self.network.broadcast_chat(txt, author)



##############################################################################
    
    def player_moved(self, pname, dest):
        """ when a player moves, notify all of them """
        #if self.is_walkable(dest): 
        # iswalkable should come from package common to client and server
        self.player_positions[pname] = dest
        self.network.broadcast_move(pname, dest)
#        else:
#            print('Warning/Cheat: player', pname,
#                  'walks in non-walkable area', dest)
#            
        