from common.events import EventManager, TickEvent
import logging


        
##############################################################################
""" INPUT CONTROLLER EVENTS """

class QuitEvent():
    pass

class DownClickEvent():
    """ When a button of the mouse is pushed down """
    def __init__(self, pos):
        self.pos = pos
        
class UpClickEvent():
    """ When a button of the mouse is raised up """
    def __init__(self, pos):
        self.pos = pos

class MoveMouseEvent():
    """ When the mouse moves """
    def __init__(self, pos):
        self.pos = pos

class UnicodeKeyPushedEvent():
    """ only concerns keys with visible representation
    (letters, numbers, ...) """
    def __init__(self, key, unicode):
        self.key = key
        self.unicode = unicode

class NonprintableKeyEvent():
    """ Triggered by enter, backspace, control, delete, and other keys 
    that are not letters, numbers, or punctuation 
    """
    def __init__(self, key):
        self.key = key
        
        
##############################################################################
""" GAME LOGIC """

class ModelBuiltMapEvent():
    def __init__(self, worldmap):
        self.worldmap = worldmap


###############################################################################
""" MOVEMENT """

class MoveMyCharactorRequest():
    """ sent from controller to model """
    def __init__(self, direction):
        self.direction = direction


class OtherCharactorPlaceEvent():
    """this event occurs when another client's Charactor is *placed* in a cell,
    ie it doesn't move there from an adjacent cell."""
    def __init__(self, charactor, cell):
        self.charactor = charactor
        self.cell = cell
        
class LocalCharactorPlaceEvent():
    """this event occurs when the client's Charactor is *placed* in a cell,
    ie it doesn't move there from an adjacent cell."""
    def __init__(self, charactor, cell):
        self.charactor = charactor
        self.cell = cell

class CharactorRemoveEvent():
    """this event occurs when a Charactor is removed from the model, 
    and the view needs to be notified of that removal """
    def __init__(self, charactor):
        self.charactor = charactor
        
        
class RemoteCharactorMoveEvent():
    """ sent from model to view when another client moved """
    def __init__(self, charactor, coords):
        self.charactor = charactor
        self.coords = coords
        
class LocalCharactorMoveEvent():
    """ sent from model to view and network controller when my charactor moved """
    def __init__(self, charactor, coords):
        self.charactor = charactor
        self.coords = coords


class NetworkReceivedCharactorMoveEvent():
    def __init__(self, pname, dest):
        self.author = pname
        self.dest = dest
        
        
##############################################################################
""" CHAT """

class SendChatEvent():
    def __init__(self, txt):
        self.txt = txt

class NetworkReceivedChatEvent():
    def __init__(self, pname, txt):
        self.author = pname
        self.txt = txt

class ChatlogUpdatedEvent():
    """ The model asks the view to refresh the chatlog """
    def __init__(self, pname, txt):
        self.author = pname
        self.txt = txt


##############################################################################
""" NETWORK """


class ClGreetEvent():
    def __init__(self, mapname, newname, newpos, onlineppl):
        self.mapname = mapname
        self.newname = newname
        self.newpos = newpos
        self.onlineppl = onlineppl

class ClNameChangeEvent():
    def __init__(self, oldname, newname):
        self.oldname = oldname
        self.newname = newname
    
class ClPlayerArrived():
    def __init__(self, pname, pos):
        self.pname = pname
        self.pos = pos
        
class ClPlayerLeft():
    def __init__(self, pname):
        self.playername = pname


##############################################################################


class ClientEventManager(EventManager):

    log = logging.getLogger('client')

    def __init__(self):
        EventManager.__init__(self)
    
    
    def reg_cb(self, eventClass, callback):
        """ just to log what's going on """
        EventManager.reg_cb(self, eventClass, callback)
        self.log.debug(eventClass.__name__ + ' will trigger ' 
                       + callback.__self__.__class__.__name__ + '.' 
                       + callback.__name__)
        
        
    def post(self, event):
        """ only log non-tick and non-moving events """
        
        if isinstance(event, MoveMouseEvent) or isinstance(event, TickEvent):
            pass
        else:
            #self.log.debug('Event: ' + event.__class__.__name__)
            pass
        
        # notify listeners in any case
        EventManager.post(self, event)
