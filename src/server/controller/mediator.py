
class Mediator():
    
    network = None 
    
    def __init__(self):
        pass
    
    def setnetwork(self, nw):
        self.network = nw
        
    
    # (dis)connection
    # notifying for pausing/resuming the game could also fit in there
        
    def player_left(self, name):
        """ TODO: remove player's avatar from game state 
        and notify everyone """
        print(name, "disconnected")
        self.network.send_admin('left', name)
        
    def player_arrived(self, name):
        """ TODO: create player's avatar """
        print(name, "connected") #TODO: log
        self.network.send_admin('arrived', name)

    # CHAT
            
    def received_chat(self, txt, author):
        """ when chat msg received, broadcast it to all connected users """
        # TODO: implement a logger as a view
        self.network.broadcast_chat(txt, author)
