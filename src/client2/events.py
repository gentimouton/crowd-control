
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

class MapBuiltEvent(Event):
    def __init__(self, gameMap):
        self.name = "Map Finished Building Event"
        self.map = gameMap

class GameStartedEvent(Event):
    def __init__(self, game):
        self.name = "Game Started Event"
        self.game = game

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
        self.eventQueue = []


    def register_listener(self, listener):
        self.listeners[ listener ] = 1


    def unregister_listener(self, listener):
        if listener in self.listeners:
            del self.listeners[ listener ]
        

    def post(self, event):
        for listener in self.listeners.copy(): #shallow copy 
            #NOTE: If the weakref has died, it will be 
            #automatically removed, so we don't have 
            #to worry about it.
            listener.notify(event)
