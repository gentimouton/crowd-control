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

class NwRcvGameAdminEvt():
    def __init__(self, pname, cmd):
        self.pname = pname
        self.cmd = cmd

class NwRcvCreepJoinEvt():
    """ Sent from nw ctrler to model to notify of creep join """
    def __init__(self, cname, cinfo):
        self.cname = cname
        self.cinfo = cinfo

class CreepPlaceEvent():
    """ Sent from model to view to notify of creep appearance """
    def __init__(self, creep):
        self.creep = creep

class NwRcvDeathEvt():
    """ from nw to model to notify of creep death """
    def __init__(self, name):
        self.name = name


######################## ATTACK ##################################

class SendAtkEvt():
    """ Model to network. Local avatar attacks a cell. """
    def __init__(self, atker, defer, targetname, dmg):
        self.atker = atker # used by the view only
        self.defer = defer # used by the view only
        self.tname = targetname # used by the network only
        self.dmg = dmg

class NwRcvAtkEvt():
    """ Network received an attack message """
    def __init__(self, attacker, defender , damage):
        self.atker = attacker
        self.defer = defender
        self.dmg = damage

class CharactorRcvDmgEvt():
    """ Sent from model to view when a charactor received damage. """
    def __init__(self, defer, dmg):
        self.defer = defer
        self.dmg = dmg

class RemoteCharactorAtkEvt():
    """ Sent from model to view when a charactor attacks. """
    def __init__(self, atker):
        self.atker = atker


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

class NwRcvCharMoveEvt():
    """ The network component was notified that a remote player moved his avatar. """
    def __init__(self, name, coords, facing):
        self.name = name
        self.coords = coords
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



class CharactorDeathEvt():
    """ From Charactor to View. """
    def __init__(self, ch):
        self.charactor = ch
        
        
################# resurrect ###############################################

class NwRcvRezEvt():
    def __init__(self, name, info):
        self.name = name
        self.info = info
 
class RemoteCharactorRezEvt():
    """ Model tells the view a charactor resurrected. """
    def __init__(self, ch):
        self.charactor = ch
        
class LocalAvRezEvt():
    """ The local avatar is resurrected. Sent from model.char to view """
    def __init__(self, av):
        self.avatar = av
 
################# CHAT ###################################################


class SendChatEvt():
    def __init__(self, txt):
        self.txt = txt

class NwRcvChatEvt():
    def __init__(self, pname, txt):
        self.pname = pname
        self.txt = txt

class ChatlogUpdatedEvent():
    """ The model asks the view to refresh the chatlog """
    def __init__(self, pname, txt):
        self.pname = pname
        self.txt = txt


################### NETWORK ##############################################



class NwRcvGreetEvt():
    def __init__(self, mapname, newname, myinfo, onlineppl, creeps):
        self.mapname = mapname
        self.newname = newname
        self.myinfo = myinfo
        self.onlineppl = onlineppl
        self.creeps = creeps

class NwRcvNameChangeEvt():
    def __init__(self, oldname, newname):
        self.oldname = oldname
        self.newname = newname
class NwRcvNameChangeFailEvt():
    def __init__(self, failname, reason):
        self.failname = failname
        self.reason = reason
    
class NwRcvPlayerJoinEvt():
    def __init__(self, pname, pinfo):
        self.pname = pname
        self.pinfo = pinfo

class NwRcvPlayerLeftEvt():
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
