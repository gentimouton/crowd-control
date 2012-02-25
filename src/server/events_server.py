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
    def __init__(self, mapname, pname, coords, facing, onlineppl, creeps):
        self.mapname = mapname
        self.pname = pname
        self.coords = coords
        self.facing = facing
        self.onlineppl = onlineppl
        self.creeps = creeps
        
class SBroadcastArrivedEvent():
    def __init__(self, pname, coords, facing):
        self.pname = pname
        self.coords = coords
        self.facing = facing
        
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
    def __init__(self, pname, coords, facing):
        self.pname = pname
        self.coords = coords
        self.facing = facing

class SBroadcastMoveEvent():
    def __init__(self, pname, coords, facing):
        self.pname = pname
        self.coords = coords
        self.facing = facing
        

######################### ATTACK ########################################


class SReceivedAtkEvent():
    def __init__(self, pname, tname):
        self.pname = pname
        self.tname = tname
        
class SBroadcastAtkEvent():
    def __init__(self, pname, coords, facing):
        self.pname = pname
        self.coords = coords
        self.facing = facing
    

####################### CREEPS ##########################################
 
class SBroadcastCreepArrivedEvent():
    def __init__(self, cname, coords, facing):
        self.cname = cname
        self.coords = coords
        self.facing = facing

class SBcCreepMoveEvent():
    def __init__(self, cname, coords, facing):
        self.cname = cname
        self.coords = coords
        self.facing = facing

        
######################### GAME #############################################

class NwBcAdminEvt():
    """ ask the network to broadcast 'game start' or 'game stop' """
    def __init__(self, pname, cmd):
        self.pname = pname
        self.cmd = cmd # doesnt have to be the same string as the player's cmd



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
