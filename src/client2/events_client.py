from common.events import Event, TickEvent, EventManager


        
##############################################################################
""" INPUT CONTROLLER EVENTS """

class ClientTickEvent(TickEvent):
    def __init__(self):
        self.name = "CPU Tick Event"

class QuitEvent(Event):
    def __init__(self):
        self.name = "Program Quit Event"

class DownClickEvent(Event):
    """ When a button of the mouse is pushed down """
    def __init__(self, coords):
        self.name = "Mouse DownClick Event"
        self.pos = coords
        
class UpClickEvent(Event):
    """ When a button of the mouse is raised up """
    def __init__(self, coords):
        self.name = "Mouse UpClick Event"
        self.pos = coords

class MoveMouseEvent(Event):
    """ When the mouse moves """
    def __init__(self, coords):
        self.name = "Mouse Move Event"
        self.pos = coords

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
    def __init__(self, worldmap):
        self.name = "Map Finished Building Event"
        self.worldmap = worldmap


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
    def __init__(self, pname, dest):
        self.name = "Network received move - " + pname + ' to ' + str(dest)
        self.author = pname
        self.dest = dest
        
        
##############################################################################
""" CHAT """

class SendChatEvent(Event):
    def __init__(self, txt):
        self.name = "Ask to send a chat message to the server"
        self.txt = txt

class NetworkReceivedChatEvent(Event):
    def __init__(self, pname, txt):
        self.name = "Received a chat message from the server"
        self.author = pname
        self.text = txt

class ChatlogUpdatedEvent(Event):
    """ The model asks the view to refresh the chatlog """
    def __init__(self, pname, txt):
        self.name = "Chatlog model has been updated"
        self.author = pname
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
    def __init__(self, playername, coords):
        self.name = "The server notified that " + playername + " connected"
        self.playername = playername
        self.pos = coords
class ServerPlayerLeft(Event):
    def __init__(self, playername):
        self.name = "The server notified that " + playername + " left"
        self.playername = playername


##############################################################################


class ClientEventManager(EventManager):
    
    def post(self, event):
        """ print non-tick events """
        if isinstance(event, MoveMouseEvent):
            pass
        elif isinstance(event, ClientTickEvent):
            pass
        else:
            print('  Evt -- ', event.name)

        