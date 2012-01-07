
class Event:
    """superclass for events sent to the EventManager"""
    def __init__(self):
        self.name = "Generic Event"

class TickEvent(Event):
    def __init__(self):
        self.name = "CPU Tick Event"

class QuitEvent(Event):
    def __init__(self):
        self.name = "Program Quit Event"

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

class GUIFocusThisWidgetEvent(Event):
    """ TODO: is this necessary from ButtonWidget to Widget? """
    def __init__(self, widget):
        self.name = "Activate particular widget Event"
        self.widget = widget

class ClickEvent(Event):
    """..."""
    def __init__(self, pos):
        self.name = "Mouse Click Event"
        self.pos = pos
        
class UnicodeKeyPushedEvent(Event):
    """ only concerns keys with visible representation
    (letters, numbers, ...) """
    def __init__(self, key, unicode):
        self.name = "Pushed key with visible representation Event "
        self.key = key
        self.unicode = unicode

class BackspaceKeyPushedEvent(Event):
    ''' TODO: refactor this to also include shift, control, alt, etc...'''
    def __init__(self):
        self.name = "Pushed backspace key Event "


        
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
        for listener in self.listeners:
            #NOTE: If the weakref has died, it will be 
            #automatically removed, so we don't have 
            #to worry about it.
            listener.notify(event)