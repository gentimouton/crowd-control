import copy
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

class CharactorMoveRequest(Event):
    def __init__(self, direction):
        self.name = "Charactor Move Request"
        self.direction = direction

class CharactorPlaceEvent(Event):
    """this event occurs when a Charactor is *placed* in a sector,
    ie it doesn't move there from an adjacent sector."""
    def __init__(self, charactor):
        self.name = "Charactor Placement Event"
        self.charactor = charactor

class CharactorMoveEvent(Event):
    def __init__(self, charactor):
        self.name = "Charactor Move Event"
        self.charactor = charactor

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
    def __init__(self, newname, newpos, onlineppl):
        self.name = "Received a greeting message from the server"
        self.newname = newname
        self.newpos = newpos
        self.onlineppl = onlineppl
        


##############################################################################

        
class EventManager:
    """this object is responsible for coordinating most communication
    between the Model, View, and Controller."""
    def __init__(self):
        from weakref import WeakKeyDictionary
        self.listeners = WeakKeyDictionary()
        self.eventdq = deque()
        
        # Rationale: a dict can't change size when iterated
        #Hence, 1) when a listener is added during a loop iteration over the
        # existing listeners, add temporarily that new listener to a dict
        self.newlisteners = WeakKeyDictionary()
        # 2) same when a listener should be removed during a loop iteration
        self.oldlisteners = WeakKeyDictionary()

    def register_listener(self, listener):
        self.newlisteners[listener] = True


    def unregister_listener(self, listener):
        if listener in self.listeners:
            self.oldlisteners[listener] = True
        

    def post(self, event):
        """ do housekeeping of the listeners (remove/add those who requested it)
        then wait for clock ticks to notify listeners of all events 
        in chronological order 
        """
        
        # add new listeners    
        for newlistener in self.newlisteners:
            self.listeners[newlistener] = True
        self.newlisteners.clear()    
        
        # remove old listeners
        for oldlistener in self.oldlisteners:
            del self.oldlisteners[oldlistener]
        self.oldlisteners.clear()
                
        # at each clock tick, notify all listeners of all the events 
        # in the order those events were received,
        if isinstance(event, TickEvent):
            events = copy.copy(self.eventdq) #shallow copy, only copies object references
            self.eventdq.clear() #only removes references from the deque
            
            while len(events) > 0:
                ev = events.popleft()    
                for listener in self.listeners:
                    listener.notify(ev)

            # don't forget to notify the listeners of the Tick event too
            for listener in self.listeners:
                listener.notify(event)

        else: # non-tick events get stacked; they are processed at clock ticks
            self.eventdq.append(event)
        
        
        
        
        
