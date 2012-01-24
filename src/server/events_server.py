from common.events import Event, EventManager, TickEvent



class SEventManager(EventManager):
    """ nothing particular to have the server event manager do """    
    def __init__(self):
        EventManager.__init__(self)



class ServerTickEvent(TickEvent):
    def __init__(self):
        self.name = "Server Tick"
  
class SQuitEvent(Event):
    def __init__(self):
        self.name = "Server Quit Event"
  



##################### player arrived/left + greeting ######################



class SPlayerArrivedEvent(Event):
    def __init__(self, pname):
        self.name = "Network notifies that a player arrived"
        self.pname = pname
        
class SPlayerLeftEvent(Event):
    def __init__(self, pname):
        self.name = "Network notifies that a player left"
        self.pname = pname
        
        
class SSendGreetEvent(Event):
    def __init__(self, mapname, pname, coords, onlineppl):
        self.name = "Network is asked to greet a player"
        self.mapname = mapname
        self.pname = pname
        self.coords = coords
        self.onlineppl = onlineppl
        
class SBroadcastStatusEvent(Event):
    def __init__(self, status, pname, coords=None):
        self.name = "Network is asked to broadcast a client (dis)connection"
        self.status= status
        self.pname = pname
        self.coords = coords



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
    def __init__(self, pname, txt):
        self.name = "Network received a chat message"
        self.txt = txt
        self.pname = pname

class SBroadcastChatEvent(Event):
    def __init__(self, pname, txt):
        self.name = "Network is asked to broadcast a chat message"
        self.txt = txt
        self.pname = pname
    



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
    




