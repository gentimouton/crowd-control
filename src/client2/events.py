from _weakrefset import WeakSet
from collections import deque


class Event:
    """superclass for events sent to the EventManager"""
    def __init__(self):
        self.name = "Generic Event"


        
##############################################################################
""" INPUT CONTROLLER EVENTS """


class TickEvent(Event):
    def __init__(self):
        self.name = "CPU Tick Event"

class QuitEvent(Event):
    def __init__(self):
        self.name = "Program Quit Event"

class DownClickEvent(Event):
    """ When a button of the mouse is pushed down """
    def __init__(self, pos):
        self.name = "Mouse DownClick Event"
        self.pos = pos
        
class UpClickEvent(Event):
    """ When a button of the mouse is raised up """
    def __init__(self, pos):
        self.name = "Mouse UpClick Event"
        self.pos = pos

class MoveMouseEvent(Event):
    """ When the mouse moves """
    def __init__(self, pos):
        self.name = "Mouse Move Event"
        self.pos = pos

class UnicodeKeyPushedEvent(Event):
    """ only concerns keys with visible representation
    (letters, numbers, ...) """
    def __init__(self, key, unicode):
        self.name = "Pushed key with visible representation Event "
        self.key = key
        self.unicode = unicode

class NonprintableKeyEvent(Event):
    """ Triggered by enter, backspace, control, delete, and other keys 
    that are not letters, numbers, or punctuation 
    """
    def __init__(self, key):
        self.name = "Non-Printablekey pressed Event"
        self.key = key
        
        
##############################################################################
""" GAME LOGIC """

class ModelBuiltMapEvent(Event):
    def __init__(self, gameMap):
        self.name = "Map Finished Building Event"
        self.map = gameMap


###############################################################################
""" MOVEMENT """

class MyCharactorMoveRequest(Event):
    """ sent from controller to model """
    def __init__(self, direction):
        self.name = "Move my charactor towards " + str(direction)
        self.direction = direction


class CharactorPlaceEvent(Event):
    """this event occurs when a Charactor is *placed* in a cell,
    ie it doesn't move there from an adjacent cell."""
    def __init__(self, charactor, cell):
        self.name = "Charactor Placement - " + str(charactor)
        self.charactor = charactor
        self.cell = cell

class CharactorRemoveEvent(Event):
    """this event occurs when a Charactor is removed from the model, 
    and the view needs to be notified of that removal """
    def __init__(self, charactor):
        self.name = "Charactor Removal - " + str(charactor)
        self.charactor = charactor
        

class CharactorMoveEvent(Event):
    """ sent from model to view """
    def __init__(self, charactor, coords):
        self.name = "Charactor Move - " + str(charactor)
        self.charactor = charactor
        self.coords = coords

class SendCharactorMoveEvent(CharactorMoveEvent):
    """ sent from model to network controller """
    def __init__(self, charactor, coords):
        self.name = "Send Charactor Move - " + str(charactor)
        self.charactor = charactor
        self.coords = coords

class NetworkReceivedCharactorMoveEvent(Event):
    def __init__(self, author, dest):
        self.name = "Network received move - " + author + ' to ' + str(dest)
        self.author = author
        self.dest = dest
        
        
##############################################################################
""" CHAT """

class SendChatEvent(Event):
    def __init__(self, txt):
        self.name = "Ask to send a chat message to the server"
        self.txt = txt

class NetworkReceivedChatEvent(Event):
    def __init__(self, author, txt):
        self.name = "Received a chat message from the server"
        self.author = author
        self.text = txt

class ChatlogUpdatedEvent(Event):
    """ The model asks the view to refresh the chatlog """
    def __init__(self, author, txt):
        self.name = "Chatlog model has been updated"
        self.author = author
        self.text = txt


##############################################################################
""" NETWORK """


class ServerGreetEvent(Event):
    def __init__(self, mapname, newname, newpos, onlineppl):
        self.name = "Received a greeting message from the server"
        self.mapname = mapname
        self.newname = newname
        self.newpos = newpos
        self.onlineppl = onlineppl

class ServerNameChangeEvent(Event):
    def __init__(self, oldname, newname):
        self.name = "The server notified that " + oldname + " changed named to " + newname
        self.oldname = oldname
        self.newname = newname
    
class ServerPlayerArrived(Event):
    def __init__(self, playername, pos):
        self.name = "The server notified that " + playername + " connected"
        self.playername = playername
        self.pos = pos
class ServerPlayerLeft(Event):
    def __init__(self, playername):
        self.name = "The server notified that " + playername + " left"
        self.playername = playername


##############################################################################

        
class EventManager:
    """this object is responsible for coordinating most communication
    between the Model, View, and Controller."""
    def __init__(self):
        self.listeners = WeakSet()
        self.eventdq = deque()
        
        # Since a dict can't change size when iterated, when a listener is 
        # added during a loop iteration over the existing listeners,
        #  add temporarily that new listener to the newlisteners dict.
        self.newlisteners = WeakSet() 


    def register_listener(self, listener):
        self.newlisteners.add(listener)


    def join_new_listeners(self):
        """ add new listeners to the actual listeners """
        if len(self.newlisteners):
            for newlistener in self.newlisteners:
                self.listeners.add(newlistener)
            self.newlisteners.clear() 

            
    def post(self, event):
        """ do housekeeping of the listeners (remove/add those who requested it)
        then wait for clock ticks to notify listeners of all events 
        in chronological order 
        """
        
        if isinstance(event, MoveMouseEvent):
            pass
        elif isinstance(event, TickEvent):
            pass
        else:
            print('  Evt -- ', event.name)
        
        # at each clock tick, notify all listeners of all the events 
        # in the order these events were received
        if isinstance(event, TickEvent):
            while len(self.eventdq):
                ev = self.eventdq.popleft()
                self.join_new_listeners()
                for listener in self.listeners: 
                    #some of those listeners may enqueue events on the fly
                    # those events will be treated within this while loop,
                    # they don't have to wait for the next tick event
                    listener.notify(ev) 
                    
                self.join_new_listeners()
                
            # post tick event
            for listener in self.listeners:
                listener.notify(event)
            self.join_new_listeners()
            
        else:
            self.eventdq.append(event)
            
