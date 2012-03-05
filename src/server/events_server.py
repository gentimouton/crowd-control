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


class SNwRcvChatEvent():
    def __init__(self, author, txt):
        self.txt = txt
        self.pname = author

class SBcChatEvent():
    def __init__(self, author, txt):
        self.txt = txt
        self.pname = author
    



######################### MOVEMENT ########################################


class SNwRcvMoveEvent():
    def __init__(self, pname, coords, facing):
        self.pname = pname
        self.coords = coords
        self.facing = facing

class SBroadcastMoveEvent():
    def __init__(self, pname, coords, facing):
        self.pname = pname
        self.coords = coords
        self.facing = facing
        

######################### PLAYER ATTACKS ####################################


class SNwRcvAtkEvent():
    def __init__(self, atker, defer):
        self.atker = atker # attacker
        self.defer = defer # defender
        
class SBcAtkEvent():
    def __init__(self, attacker, defender, damage):
        self.atker = attacker
        self.defer = defender
        self.dmg = damage
    

####################### CREEPS ##########################################
 
class SBcCreepArrivedEvent():
    def __init__(self, cname, coords, facing):
        self.name = cname
        self.coords = coords
        self.facing = facing

class SBcCreepMovedEvent():
    def __init__(self, cname, coords, facing):
        self.name = cname
        self.coords = coords
        self.facing = facing

class SBcCreepDiedEvent():
    def __init__(self, cname):
        self.name = cname

class SCreepAtkEvent():
    def __init__(self, attacker, defender ,damage):
        self.atker = attacker
        self.defer = defender
        self.dmg = damage
        
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
