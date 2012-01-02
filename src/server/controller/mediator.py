
class Mediator():
    
    network = None 
    
    def __init__(self):
        self.players = set() # store connected players 

    
    def setnetwork(self, nw):
        self.network = nw
        
    
    # (dis)connection and name changes
    # notifying for pausing/resuming the game could also fit in there
        
    def player_left(self, name):
        """ TODO: remove player's avatar from game state 
        and notify everyone """
        print(name, "disconnected")
        self.players.discard(name)
        self.network.broadcast_conn_status('left', name)
        
    def player_arrived(self, name):
        """ TODO: create player's avatar """
        print(name, "connected") #TODO: log
        if name not in self.players:
            self.players.add(name)
            self.network.greet(name)
            self.network.broadcast_conn_status('arrived', name)
        else:
            print("Warning:", name, 'was already in connected players')
            print('Possibly, self.players[name] had not been cleaned properly')

    def handle_name_change(self, oldname, newname):
        ''' change player's name only if newname not taken already '''
        if newname not in self.players:
            self.players.add(newname)
            self.players.remove(oldname)
            self.network.broadcast_name_change(oldname, newname)
        else: 
            # TODO: send personal notif to the client who failed to change name
            pass
    
    
    # CHAT
            
    def received_chat(self, txt, author):
        """ when chat msg received, broadcast it to all connected users """
        # TODO: implement a logger as a view
        self.network.broadcast_chat(txt, author)
