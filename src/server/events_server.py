from common.events import EventManager
import logging


  
class SQuitEvent():
    pass
  



#################### model events #########################################

class SModelBuiltWorldEvent():
    def __init__(self, world):
        self.world = world




##################### player arrived/left + greeting ######################



class SPlayerArrivedEvent():
    def __init__(self, authorr):
        self.pname = authorr
        
class SPlayerLeftEvent():
    def __init__(self, authorr):
        self.pname = authorr
        
        
class SSendGreetEvent():
    def __init__(self, mapname, pname, coords, onlineppl, creeps):
        self.mapname = mapname
        self.pname = pname
        self.coords = coords
        self.onlineppl = onlineppl
        self.creeps = creeps
        
class SBroadcastArrivedEvent():
    def __init__(self, pname, coords):
        self.pname = pname
        self.coords = coords
        
class SBroadcastLeftEvent():
    def __init__(self, pname):
        self.pname = pname




################### name change ###########################################

    
class SPlayerNameChangeRequestEvent():
    def __init__(self, oldname, newname):
        self.oldname = oldname
        self.newname = newname

class SBroadcastNameChangeEvent():
    def __init__(self, oldname, newname):
        self.oldname = oldname
        self.newname = newname

####################################### CHAT ##############################


class SReceivedChatEvent():
    def __init__(self, author, txt):
        self.txt = txt
        self.pname = author

class SBroadcastChatEvent():
    def __init__(self, author, txt):
        self.txt = txt
        self.pname = author
    



######################### MOVEMENT ########################################


class SReceivedMoveEvent():
    def __init__(self, pname, coords):
        self.pname = pname
        self.coords = coords

class SBroadcastMoveEvent():
    def __init__(self, pname, coords):
        self.pname = pname
        self.coords = coords
    

####################### CREEPS ##########################################
 
class SBroadcastCreepArrivedEvent():
    def __init__(self, creepid, coords):
        self.creepid = creepid
        self.coords = coords

class SBroadcastCreepMoveEvent():
    def __init__(self, creepid, coords):
        self.creepid = creepid
        self.coords = coords

        
######################### GAME #############################################

class SGameStartEvent():
    def __init__(self, pname):
        self.pname = pname



class SrvEventManager(EventManager):

    log = logging.getLogger('server')

    def __init__(self):
        EventManager.__init__(self)
        
    def reg_cb(self, eventClass, callback):
        """ just to log """
        EventManager.reg_cb(self, eventClass, callback)
        self.log.debug(eventClass.__name__ + ' will trigger ' 
                       + callback.__self__.__class__.__name__ + '.' 
                       + callback.__name__)
        
    def post(self, event):
        """ only log non-tick and non-moving events """
        
        if event.__class__.__name__ == 'TickEvent':
            pass
        else:
            #self.log.debug('Event: ' + event.__class__.__name__)
            pass
            
        # notify listeners in any case
        EventManager.post(self, event)
