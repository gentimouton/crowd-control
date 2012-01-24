from common.messages import GreetMsg
from common.world import World
from server.config import config_get_mapname
from server.events_server import SModelBuiltWorldEvent, SBroadcastStatusEvent, \
    SSendGreetEvent, SBroadcastNameChangeEvent, SBroadcastChatEvent, \
    SBroadcastMoveEvent, SPlayerArrivedEvent, SPlayerLeftEvent, \
    SPlayerNameChangeRequestEvent, SReceivedChatEvent, SReceivedMoveEvent


class SPlayer():
    
    def __init__(self, pname, coords):
        self.pname = pname
        self.coords = coords
        

class SGame():
    
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)
        # player list
        self.players = dict() 
        
        # build world
        self.mapname = config_get_mapname()
        self.world = World(evManager)
        self.world.build_world(self.mapname, SModelBuiltWorldEvent)



    ############### (dis)connection and name changes ##########################


    # notifying for pausing/resuming the game could also fit in there
        
    def player_left(self, name):
        """ remove player's avatar from game state and notify everyone """
        try:
            del self.players[name]
        except KeyError:
            print('Tried to remove player ', name,
                  ', but it was not found in player list')
        
        event = SBroadcastStatusEvent('left', name)
        self.evManager.post(event)
        
        
        
    def player_arrived(self, pname):
        """ create player's avatar and send him the list of connected ppl
        do not include him in the list of connected people """
        #print(pname, "connected") #TODO: log
        if pname not in self.players:
            onlineppl = self.players.copy()
            coords = self.world.entrance_coords
            player = SPlayer(pname, coords)
            self.players[pname] = player
            # greet the new player
            gmsg = GreetMsg(self.mapname, pname, coords, onlineppl) 
            event = SSendGreetEvent(gmsg)
            self.evManager.post(event) 
            # notify the connected players of this arrival 
            event = SBroadcastStatusEvent('arrived', pname, coords)
            self.evManager.post(event)
            
        else: 
            # player was already connected, 
            # or his pname had not been removed when he disconnected
            print("Warning:", pname, 'was already in connected player_positions')
            print('Possibly, self.player_positions[pname] had not been cleaned properly')
    
    


##############################################################################
            
    def handle_name_change(self, oldname, newname):
        """ change player's name only if newname not taken already """
        if newname not in self.players:
            self.players[newname] = self.players[oldname]
            del self.players[oldname]
            #print(oldname, 'changed name into ', newname)
            
            event = SBroadcastNameChangeEvent(oldname, newname)
            self.evManager.post(event)
        
        else: 
            # TODO: send personal notif to the client who failed to change name
            pass
    
##############################################################################
            
    def received_chat(self, pname, txt):
        """ when chat msg received, broadcast it to all connected users """
        # TODO: implement a chat logger as a view
        
        event = SBroadcastChatEvent(pname, txt)
        self.evManager.post(event)



##############################################################################
    
    def player_moved(self, pname, coords):
        """ when a player moves, notify all of them """
        #if self.is_walkable(coords): 
        # iswalkable should come from package common to client and server
        self.players[pname] = coords
        
        event = SBroadcastMoveEvent(pname, coords)
        self.evManager.post(event)

#        else:
#            print('Warning/Cheat: player', pname,
#                  'walks in non-walkable area', coords)
#            
        
##############################################################################

    def notify(self, event):
        
        # network notifies that a player arrived or left
        if isinstance(event, SPlayerArrivedEvent):
            self.player_arrived(event.pname)
        elif isinstance(event, SPlayerLeftEvent):
            self.player_left(event.pname)
        
        # name changes
        elif isinstance(event, SPlayerNameChangeRequestEvent):
            self.handle_name_change(event.oldname, event.newname)
        
        # chat
        elif isinstance(event, SReceivedChatEvent):
            self.received_chat(event.pname, event.txt)
        
        # movement
        elif isinstance(event, SReceivedMoveEvent):
            self.player_moved(event.pname, event.coords)
            
            