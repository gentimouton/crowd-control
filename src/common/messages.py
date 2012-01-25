

class SerializableMsg():
    """ An abstract class representing messages exchanged between clients
    and server. 
    """
    
    mtype = 'not set' #should be overriden in subclasses
    attrs = [] #should be overriden in subclasses



    def __init__(self, *args, d_src=None):
        """ Build self.d, the message's serializable dictionary holding 
        the message's attributes
        """
        
        self.d = dict() #serializable representation of the message
        self.d['mtype'] = self.mtype
        
        if d_src: 
            # Build the message's dictionary from a source dictionary, 
            # eventually limiting the copy to some attributes. 
            try:
                for k in self.attrs:
                    self.d[k] = d_src[k]
            except KeyError:
                print('Source dictionary is missing a required key')

        else:
            # default constructor: arguments have to be passed in the order
            # they are specified in the self.attrs of the subclass
            assert len(args) <= len(self.attrs), 'Too many arguments given'

            for i in range(len(args)):
                self.d[self.attrs[i]] = args[i]
            # careful: if self.attrs is longer than args, 
            # then the last elements of self.attrs stay undefined 
                
                         


        
################# ADMIN #####################################################



class GreetMsg(SerializableMsg):
    """ sent from the server to a player when he just arrived """
    mtype = 'greet'
    attrs = ['mapname', 'pname', 'coords', 'onlineppl']
    
    
class BroadcastArrivedMsg(SerializableMsg):
    """ sent from the server to all players when a player arrived """        
    mtype = 'arrived'
    attrs = ['pname', 'coords'] 
class BroadcastLeftMsg(SerializableMsg):
    """ sent from the server to all players when a player left """        
    mtype = 'left'
    attrs = ['pname'] 

    
    
    
