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
                logging.error('Source dictionary is missing required key ' + str(k))

        else:
            # default constructor: arguments have to be passed in the order
            # they are specified in the self.attrs of the subclass
            try:
                for k in self.attrs:
                    self.d[k] = d_src[k]
            except KeyError:
                logging.error('Key ' + str(k) + 'was missing from d_src')
                



# attack
class ClAtkMsg(SerializableMsg):
    """ Attack msg sent from a client to the server """        
    attrs = ['targetname', 'dmg'] 
class SrvAtkMsg(SerializableMsg):
    """ broadcast of an attack msg by the server """        
    attrs = ['atker', 'defer', 'dmg'] 

    
    
# chat
class ClChatMsg(SerializableMsg):
    """ chat msg sent from a client to the server """        
    attrs = ['txt'] 
class SrvChatMsg(SerializableMsg):
    """ brodcast of a chat msg by the server """        
    attrs = ['author', 'txt'] 
    
    

# creepjoin
class SrvCreepJoinedMsg(SerializableMsg):
    """ broadcast creep creation """
    attrs = ['cname', 'cinfo']



# death
class SrvDeathMsg(SerializableMsg):
    """ broadcast charactor death """
    attrs = ['name']



# gameadmin
class SrvGameAdminMsg(SerializableMsg):
    """ broadcast that someone started or stopped the game """        
    attrs = ['pname', 'cmd'] 



# greet        
class SrvGreetMsg(SerializableMsg):
    """ sent from the server to a player when he just arrived """
    attrs = ['mapname', 'pname', 'myinfo', 'onlineppl', 'creeps']


# movement
class ClMoveMsg(SerializableMsg):
    """ mvt msg sent from a client to the server """        
    attrs = ['coords', 'facing'] 
class SrvMoveMsg(SerializableMsg):
    """ broadcast of a mvt msg by the server """        
    attrs = ['name', 'coords', 'facing'] 



# namechange
class ClNameChangeMsg(SerializableMsg):
    """ sent from a client to the server when he wants to change name """        
    attrs = ['pname'] 
class SrvNameChangeMsg(SerializableMsg):
    """ broadcasted by the server to notify all the clients of a name change """        
    attrs = ['oldname', 'newname'] 
class SrvNameChangeFailMsg(SerializableMsg):
    """ Notification to player who failed to change name """
    attrs = ['failname', 'reason']
    
    
      
# playerjoin
class SrvPlyrJoinMsg(SerializableMsg):
    """ sent from the server to all players when a player arrived """        
    attrs = ['pname', 'pinfo']
    
    
# playerleft 
class SrvPlyrLeftMsg(SerializableMsg):
    """ sent from the server to all players when a player left """        
    attrs = ['pname'] 


# resurrect
class SrvRezMsg(SerializableMsg):
    """ sent from server to players when a charactor was revived. """
    attrs = ['name', 'info']
    
    
    
    
    

###################### deserialization #####################################

def unpack_msg(msgobj, msgClass):
    """ msgobj is the object sent on the network, 
     msgClass is the class to convert this object into.
    Example: In the callback Network_move, 
    unpack_msg(msgobj=data['msg'], SrvMoveMsg) 
    returns the tuple (msg.pname, msg.coords, msg.facing)
    because SrvMoveMsg has for attrs pname, coords, and facing. 
    """
    cmsg = msgClass(msgobj) #unserialize
    # TODO: PERF how much more expensive is it to build the lambda 
    # each time unpack_msg is called compared to calling a predefined function?
    get_msgvals = lambda attr: cmsg.d[attr]
    msg_attrs = msgClass.attrs
    return tuple(map(get_msgvals, msg_attrs))

