
class Mediator():
    
    network = None 
    
    def __init__(self):
        pass
    
    def setnetwork(self, nw):
        self.network = nw
        
    
    # (dis)connection and name changes
    # notifying for pausing/resuming the game could also fit in there
        
    def player_left(self, name):
        """ TODO: remove player's avatar from game state 
        and notify everyone """
        print(name, "disconnected")
        self.network.broadcast_conn_status('left', name)
        
    def player_arrived(self, name):
        """ TODO: create player's avatar """
        print(name, "connected") #TODO: log
        self.network.broadcast_conn_status('arrived', name)

    def handle_name_change(self, oldname, newname):
        print('change name:', oldname, newname)
        self.network.broadcast_name_change(oldname, newname)

    # CHAT
            
    def received_chat(self, txt, author):
        """ when chat msg received, broadcast it to all connected users """
        # TODO: implement a logger as a view
        self.network.broadcast_chat(txt, author)
