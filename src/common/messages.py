

############ serializable messages exchanged between client and server ######



class GreetMsg():
    mtype = 'greet'
    
    """ sent from the server to a player when he just arrived """
    def __init__(self, mapname=None, pname=None, coords=None, onlineppl=None):    
        self.mapname = mapname
        self.pname = pname
        self.coords = coords
        self.onlineppl = onlineppl
    
        
    def __str__(self):
        return "<GreetMsg for %s, %s>", (self.pname, id(self))
    
    
    
    def serialize(self):
        """ return a dict that can be sent over the network """
        d = dict()
        d['mtype'] = self.mtype
        d['mapname'] = self.mapname
        d['pname'] = self.pname
        d['coords'] = self.coords
        d['onlineppl'] = self.onlineppl
        return d
        #dict([(p.id, p.color) for p in self.players])
        
        
    def deserialize(self, smsg):
        """ fill attributes from a serialized msg """
        self.mtype = smsg['mtype']
        self.mapname = smsg['mapname']
        self.pname = smsg['pname']
        self.coords = smsg['coords']
        self.onlineppl = smsg['onlineppl']
    
