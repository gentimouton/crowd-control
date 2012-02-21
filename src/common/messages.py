import logging


class SerializableMsg():
    """ An abstract class representing messages exchanged between clients
    and server. 
    """
    
    attrs = [] #should be overriden in subclasses

    def __init__(self, d_src):
        """ Build self.d, the message's serializable dictionary holding 
        the message's attributes
        """
        self.d = dict() #serializable representation of the message
       
        if d_src: 
            # Build the message's dictionary from a source dictionary, 
            # eventually limiting the copy to some attributes. 
            try:
                for k in self.attrs:
                    self.d[k] = d_src[k]
            except KeyError:
                logging.error('Source dictionary is missing a required key')

        else:
            # default constructor: arguments have to be passed in the order
            # they are specified in the self.attrs of the subclass
            try:
                for k in self.attrs:
                    self.d[k] = d_src[k]
            except KeyError:
                logging.error('key', k, 'was missing from d_src')
                
                         

  
    
        
################# ADMIN #####################################################



class AdminSerializableMsg(SerializableMsg):
    """ Abstract class representing admin messages:
    connection, disconnection, name change, and greeting.
    """
    mtype = 'not set' #should be overriden in subclasses
    
    def __init__(self, d_src=None):
        # opts can be empty or contain d_src
        # SOLUTION: have all the message constructors specify the keys and pass **opts all the time
        SerializableMsg.__init__(self, d_src)
        self.d['mtype'] = self.mtype
        
        
        
class GreetMsg(AdminSerializableMsg):
    """ sent from the server to a player when he just arrived """
    mtype = 'greet'
    attrs = ['mapname', 'pname', 'coords', 'onlineppl', 'creeps']
    
    
class PlayerArrivedNotifMsg(AdminSerializableMsg):
    """ sent from the server to all players when a player arrived """        
    mtype = 'arrived'
    attrs = ['pname', 'coords'] 
class PlayerLeftNotifMsg(AdminSerializableMsg):
    """ sent from the server to all players when a player left """        
    mtype = 'left'
    attrs = ['pname'] 


class NameChangeRequestMsg(AdminSerializableMsg):
    """ sent from a client to the server when he wants to change name """        
    mtype = 'namechange'
    attrs = ['pname'] 
class NameChangeNotifMsg(AdminSerializableMsg):
    """ broadcasted by the server to notify all the clients of a name change """        
    mtype = 'namechange'
    attrs = ['oldname', 'newname'] 

    
    
    
################# CHAT #####################################################

class ClChatMsg(SerializableMsg):
    """ chat msg sent from a client to the server """        
    attrs = ['txt'] 
class SrvChatMsg(SerializableMsg):
    """ brodcast of a chat msg by the server """        
    attrs = ['pname', 'txt'] 
    
    
################# MOVEMENT #####################################################

class ClMoveMsg(SerializableMsg):
    """ mvt msg sent from a client to the server """        
    attrs = ['coords'] 
class SrvMoveMsg(SerializableMsg):
    """ brodcast of a mvt msg by the server """        
    attrs = ['pname', 'coords'] 



################# GAME #####################################################

 
class SrvGameStartMsg(SerializableMsg):
    """ broadcast that the game started """        
    attrs = ['pname'] 


class SrvCreepMovedMsg(SerializableMsg):
    """ broadcast creep movement """
    attrs = ['creepid', 'act', 'coords']
class SrvCreepJoinedMsg(SerializableMsg):
    """ broadcast creep creation """
    attrs = ['creepid', 'act', 'coords']
    