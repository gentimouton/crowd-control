from common.world import World
from server.config import config_get_mapname
from server.events_server import SModelBuiltWorldEvent, SSendGreetEvent, \
    SBroadcastNameChangeEvent, SBroadcastChatEvent, SBroadcastMoveEvent, \
    SPlayerArrivedEvent, SPlayerLeftEvent, SPlayerNameChangeRequestEvent, \
    SReceivedChatEvent, SReceivedMoveEvent, SBroadcastArrivedEvent, \
    SBroadcastLeftEvent


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
        self.world = World(evManager)
        self.mapname = config_get_mapname()
        self.world.build_world(self.mapname, SModelBuiltWorldEvent)



    ############### (dis)connection and name changes ##########################


    # notifying for pausing/resuming the game could also fit in there
        
    def player_left(self, pname):
        """ remove player's avatar from game state and notify everyone """
        try:
            del self.players[pname]
        except KeyError:
            print('Tried to remove player ', pname,
                  ', but it was not found in player list')
        
        event = SBroadcastLeftEvent(pname)
        self.evManager.post(event)
        
        
        
    def player_arrived(self, pname):
        """ Create player's avatar, and send him the list of connected ppl.
        Do not include him in the list of connected people. 
        """
        #TODO: log
        if pname not in self.players:
            # build list of connected players with their coords
            onlineppl = dict()
            for (otherpname, otherplayer) in self.players.items():
                onlineppl[otherpname] = otherplayer.coords
            # build the new player    
            coords = self.world.entrance_coords
            player = SPlayer(pname, coords)
            self.players[pname] = player
            # greet the new player 
            event = SSendGreetEvent(self.mapname, pname, coords, onlineppl)
            self.evManager.post(event) 
            # notify the connected players of this arrival
            event = SBroadcastArrivedEvent(pname, coords)
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
        self.players[pname].coords = coords
        
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
            
            
