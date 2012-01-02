from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from server.config import config_get_host, config_get_port
from time import time
from uuid import uuid4
from weakref import WeakKeyDictionary, WeakValueDictionary

class ClientChannel(Channel):
      
    def Close(self):
        """ built-in called by Channel.handle_close """
        self._server.channel_closed(self)

    ######## custom logic called by Channel.found_terminator()
    
    def Network(self, data):
        """ called for all received msgs """
        # TODO: implement a logger, as a view of a mediator
        pass
    
    def Network_chat(self, data):
        """ when chat messages are received """
        #print("Received chat: " + data['msg']) 
        self._server.received_chat(self, data['msg'])

    def Network_admin(self, data):
        ''' change name messages '''
        if data['msg']['type'] == 'namechange':
            self._server.received_name_change(self, data['msg']['newname'])





class NetworkController(Server):
    
    channelClass = ClientChannel
    
    def __init__(self, mediator):
        host, port = config_get_host(), config_get_port()
        Server.__init__(self, localaddr=(host, port))
        self.mediator = mediator
        self.chan_to_name = WeakKeyDictionary() #maps channel to name
        self.name_to_chan = WeakValueDictionary() #maps name to channel
        #WeakKeyDictionary's key is garbage collected and removed from dictionary 
        # when used nowhere else but in the dict's mapping
        print('Network up')



    ####### (dis)connection and name changes 

    def Connected(self, channel, addr):
        """ Called by Server.handle_accept() whenever a new client connects. 
        assign a temporary name to a client, a la IRC. 
        The client should change user's name automatically if it's not taken
        already, and clients can use a command to change their name"""
        name = str(uuid4())[:8] #random 32-hexadigit uuid 
        # truncated to 8 hexits = 16^8 = 4 billion possibilities
        # if by chance someone already has this uuid name, repick until unique
        while name in self.chan_to_name.keys(): 
            name = str(uuid4())[:8]
        self.chan_to_name[channel] = name
        self.name_to_chan[name] = channel
        self.mediator.player_arrived(name)
        
    def channel_closed(self, channel):
        """ when a player logs out, remove his channel from the list """
        name = self.chan_to_name[channel]
        self.mediator.player_left(name)
        del self.name_to_chan[name]
        del self.chan_to_name[channel]

    def broadcast_conn_status(self, status, name):
        """ notify clients that a new player just arrived (type='arrived') 
        or left (type='left') """
        data = {"action": 'admin', "msg": {"type":status, "name":name}}
        [chan.Send(data) for chan in self.chan_to_name.keys()]

    def greet(self, name):
        ''' send greeting data to a player '''
        data = {"action": 'admin', "msg": {"type":'greet', "newname":name}}
        chan = self.name_to_chan[name]
        chan.Send(data)

    def received_name_change(self, channel, newname):
        ''' notify mediator that a player wants to change name '''
        oldname = self.chan_to_name[channel]
        self.mediator.handle_name_change(oldname, newname)
    
            
    def broadcast_name_change(self, oldname, newname):
        ''' update name<->channel mappings and notify all players '''
        channel = self.name_to_chan[oldname]
        self.chan_to_name[channel] = newname
        self.name_to_chan[newname] = channel
        del self.name_to_chan[oldname]
        msg = {'type':'namechange', 'old':oldname, 'new':newname}
        [c.Send({'action':'admin', 'msg':msg}) for c in self.chan_to_name.keys()]
        
        
        
    #######  chat        
        
    def received_chat(self, channel, txt):
        """ send a chat msg to all connected clients """
        author = self.chan_to_name[channel]
        self.mediator.received_chat(txt, author)
        
    def broadcast_chat(self, txt, author):
        data = {"action": "chat", "msg": {"txt":txt, "author":author}}
        [p.Send(data) for p in self.chan_to_name.keys()]

    
    
        
            
             