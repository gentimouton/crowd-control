
class Mediator():
    
    network = None 
    
    def __init__(self):
        self.other_players = dict() # store connected other_players 
        self.startpos = 100, 100
        self.boundaries = 600, 200
    
    def setnetwork(self, nw):
        self.network = nw
        
    
    # (dis)connection and name changes
    # notifying for pausing/resuming the game could also fit in there
        
    def player_left(self, name):
        """ TODO: remove player's avatar from game state 
        and notify everyone """
        #print(name, "disconnected")
        try:
            del self.other_players[name]
        except KeyError:
            print('Tried to remove player ', name,
                  ', but it was not in player list')
        self.network.broadcast_conn_status('left', name)
        
    def player_arrived(self, name):
        """ create player's avatar and send him the list of connected ppl
        do not include him in the list of connected people """
        #print(name, "connected") #TODO: log
        if name not in self.other_players:
            onlineppl = self.other_players.copy()
            self.other_players[name] = self.startpos
            self.network.greet(name, self.startpos, onlineppl) 
            self.network.broadcast_conn_status('arrived', name)
        else:
            print("Warning:", name, 'was already in connected other_players')
            print('Possibly, self.other_players[name] had not been cleaned properly')

    def handle_name_change(self, oldname, newname):
        ''' change player's name only if newname not taken already '''
        if newname not in self.other_players:
            self.other_players[newname] = self.other_players[oldname]
            del self.other_players[oldname]
            #print(oldname, 'changed name into ', newname)
            self.network.broadcast_name_change(oldname, newname)
        else: 
            # TODO: send personal notif to the client who failed to change name
            pass
    
    
    # CHAT
            
    def received_chat(self, txt, author):
        """ when chat msg received, broadcast it to all connected users """
        # TODO: implement a chat logger as a view
        self.network.broadcast_chat(txt, author)


    # MOVEMENT
    
    def player_moved(self, pname, dest):
        ''' when a player moves, notify all of them '''
        if self.is_walkable(dest):
            self.other_players[pname] = dest
            self.network.broadcast_move(pname, dest)
        
    def is_walkable(self, pos):
        ''' TODO: duplicated from client.world; should use a common package instead '''
        return (pos[0] > 0 
            and pos[1] > 0 
            and pos[0] < self.boundaries[0] 
            and pos[1] < self.boundaries[1])
