from common.events import Event, TickEvent


class ServerTickEvent(TickEvent):
    def __init__(self):
        self.name = "Server Tick"
  
class SQuitEvent(Event):
    def __init__(self):
        self.name = "Server Quit Event"
  



#################### model events #########################################

class SModelBuiltWorldEvent(Event):
    def __init__(self, world):
        self.name = "Server finished building its world map"
        self.world = world




##################### player arrived/left + greeting ######################



class SPlayerArrivedEvent(Event):
    def __init__(self, authorr):
        self.name = "Network notifies that a player arrived"
        self.pname = authorr
        
class SPlayerLeftEvent(Event):
    def __init__(self, authorr):
        self.name = "Network notifies that a player left"
        self.pname = authorr
        
        
class SSendGreetEvent(Event):
    def __init__(self, mapname, pname, coords, onlineppl):
        self.name = "Network is asked to greet a player"
        self.mapname = mapname
        self.pname = pname
        self.coords = coords
        self.onlineppl = onlineppl
        
        
class SBroadcastArrivedEvent(Event):
    def __init__(self, pname, coords):
        self.name = "Network is asked to broadcast a client connection"
        self.pname = pname
        self.coords = coords
        
class SBroadcastLeftEvent(Event):
    def __init__(self, pname):
        self.name = "Network is asked to broadcast a client disconnection"
        self.pname = pname




################### name change ###########################################

    
class SPlayerNameChangeRequestEvent(Event):
    def __init__(self, oldname, newname):
        self.name = "Network was notified that a client wants to change name"
        self.oldname = oldname
        self.newname = newname

class SBroadcastNameChangeEvent(Event):
    def __init__(self, oldname, newname):
        self.name = "Network is asked to broadcast that a client changed name"
        self.oldname = oldname
        self.newname = newname

####################################### CHAT ##############################


class SReceivedChatEvent(Event):
    def __init__(self, authorr, txt):
        self.name = "Network received a chat message"
        self.txt = txt
        self.pname = authorr

class SBroadcastChatEvent(Event):
    def __init__(self, authorr, txt):
        self.name = "Network is asked to broadcast a chat message"
        self.txt = txt
        self.pname = authorr
    



######################### MOVEMENT ########################################


class SReceivedMoveEvent(Event):
    def __init__(self, pname, coords):
        self.name = "Network received a move message"
        self.pname = pname
        self.coords = coords

class SBroadcastMoveEvent(Event):
    def __init__(self, pname, coords):
        self.name = "Network is asked to broadcast a move message"
        self.pname = pname
        self.coords = coords
    




