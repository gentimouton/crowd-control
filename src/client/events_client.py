from common.events import EventManager, TickEvent
import logging


        
######################## USER INPUT ########################################


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
        
class InputAtkRequest():
    """ User pushed a key to attack. """ 
    pass


#################### MODEL TO VIEW #######################################
""" message passing from model to view """

class MdAddPlayerEvt():
    """ Add a player name to the list of connected players 
    in a text widget from the view. 
    """
    def __init__(self, pname):
        self.pname = pname
        
        
                
################# GAME LOGIC ##############################################


class ModelBuiltMapEvent():
    def __init__(self, worldmap):
        self.worldmap = worldmap

class NwRecGameAdminEvt():
    def __init__(self, pname, cmd):
        self.pname = pname
        self.cmd = cmd

class NwRecCreepJoinEvt():
    """ Sent from nw ctrler to model to notify of creep join """
    def __init__(self, cname, coords, facing):
        self.cname = cname
        self.coords = coords
        self.facing = facing
        
class CreepPlaceEvent():
    """ Sent from model to view to notify of creep appearance """
    def __init__(self, creep):
        self.creep = creep
        
class NwRecCreepMoveEvt():
    """ Sent from network to model """
    def __init__(self, cname, coords, facing):
        self.cname = cname
        self.coords = coords
        self.facing = facing


class SendAtkEvt():
    """ Model to network. Local avatar attacks a cell. """
    def __init__(self, target):
        self.target = target
    

######################### ADMIN ######################################

class MyNameChangedEvent():
    """ sent from model to a text label widget 
    to notify that the local player changed name. 
    """
    def __init__(self, oldname, newname):
        self.oldname = oldname
        self.newname = newname
        
######################### MOVEMENT #########################################


class InputMoveRequest():
    """ sent from input controller to model """
    def __init__(self, direction):
        self.direction = direction

class OtherAvatarPlaceEvent():
    """this event occurs when another client's avatar is *placed* in a cell,
    ie it doesn't move there from an adjacent cell."""
    def __init__(self, char, cell):
        self.avatar = char
        self.cell = cell
        
class LocalAvatarPlaceEvent():
    """this event occurs when the client's avatar is *placed* in a cell,
    ie it doesn't move there from an adjacent cell."""
    def __init__(self, char, cell):
        self.avatar = char
        self.cell = cell

class SendMoveEvt():
    """ sent from model to view and network controller when my avatar moved """
    def __init__(self, char, coords, facing):
        self.avatar = char
        self.coords = coords
        self.facing = facing

class NwRecAvatarMoveEvt():
    """ The network component was notified that a remote player moved his avatar. """
    def __init__(self, pname, dest, facing):
        self.pname = pname
        self.dest = dest
        self.facing = facing



class RemoteCharactorMoveEvent():
    """ sent from model to view when an avatar or a creep moved """
    def __init__(self, char, coords):
        self.charactor = char
        self.coords = coords
        
class CharactorRemoveEvent():
    """this event occurs when a creep or avatar is removed from the model, 
    and the view needs to be notified of that removal. """
    def __init__(self, ch):
        self.charactor = ch


        
        
################# CHAT ###################################################


class SendChatEvt():
    def __init__(self, txt):
        self.txt = txt

class NwRecChatEvt():
    def __init__(self, pname, txt):
        self.pname = pname
        self.txt = txt

class ChatlogUpdatedEvent():
    """ The model asks the view to refresh the chatlog """
    def __init__(self, pname, txt):
        self.pname = pname
        self.txt = txt


################### NETWORK ##############################################



class NwRecGreetEvt():
    def __init__(self, mapname, newname, newpos, facing, onlineppl, creeps):
        self.mapname = mapname
        self.newname = newname
        self.newpos = newpos
        self.facing = facing
        self.onlineppl = onlineppl
        self.creeps = creeps

class NwRecNameChangeEvt():
    def __init__(self, oldname, newname):
        self.oldname = oldname
        self.newname = newname
    
class NwRecPlayerJoinEvt():
    def __init__(self, pname, pos, facing):
        self.pname = pname
        self.pos = pos
        self.facing = facing
        
class NwRecPlayerLeft():
    def __init__(self, pname):
        self.pname = pname


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
