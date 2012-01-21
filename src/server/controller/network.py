from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from server.config import config_get_host, config_get_port
from uuid import uuid4
from weakref import WeakKeyDictionary, WeakValueDictionary

class ClientChannel(Channel):
      
    def Close(self):
        """ built-in called by Channel.handle_close """
        self._server.channel_closed(self)

    ######## custom logic called by Channel.found_terminator()
    
    def Network(self, data):
        """ called for all received msgs """
        # TODO: implement a logger, as a view of the mediator
        pass
    
    def Network_chat(self, data):
        """ when chat messages are received """ 
        self._server.received_chat(self, data['msg'])

    def Network_admin(self, data):
        """ change name messages """
        if data['msg']['type'] == 'namechange':
            self._server.received_name_change(self, data['msg']['newname'])

    def Network_move(self, data):
        """ movement messages """
        dest = data['msg']['dest'] 
        self._server.received_move(self, dest)


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
        print('Server Network up')



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


    def broadcast_conn_status(self, status, name, pos=None):
        """ notify clients that a new player just arrived (type='arrived') 
        or left (type='left') """
        data = {"action": 'admin', "msg": {"type":status, "name":name}}
        
        # user joined = broadcast his name and pos to all but him
        if pos is not None:
            data['msg']['newpos'] = pos
            for chan in self.chan_to_name:
                if self.chan_to_name[chan] != name:
                    chan.Send(data) 
        
        else: # user left: notify everyone
            for chan in self.chan_to_name:
                chan.Send(data) 
                

    def greet(self, mapname, name, pos, onlineppl):
        """ send greeting data to a player """
        msg = {"type":'greet', 'mapname':mapname, "newname":name, 'newpos':pos,
               'onlineppl':onlineppl}
        chan = self.name_to_chan[name]
        chan.Send({"action": 'admin', "msg": msg})

    def received_name_change(self, channel, newname):
        """ notify mediator that a player wants to change name """
        oldname = self.chan_to_name[channel]
        self.mediator.handle_name_change(oldname, newname)
    
            
    def broadcast_name_change(self, oldname, newname):
        """ update name<->channel mappings and notify all players """
        channel = self.name_to_chan[oldname]
        self.chan_to_name[channel] = newname
        self.name_to_chan[newname] = channel
        del self.name_to_chan[oldname]
        msg = {'type':'namechange', 'old':oldname, 'new':newname}
        for c in self.chan_to_name:
            c.Send({'action':'admin', 'msg':msg}) 

        
        
        
    #######  chat        
        
    def received_chat(self, channel, txt):
        """ send a chat msg to all connected clients """
        author = self.chan_to_name[channel]
        self.mediator.received_chat(txt, author)
        
    def broadcast_chat(self, txt, author):
        data = {"action": "chat", "msg": {"txt":txt, "author":author}}
        for chan in self.chan_to_name:
            chan.Send(data) 

    
    ###### movement
    
    def received_move(self, channel, dest):
        pname = self.chan_to_name[channel]
        self.mediator.player_moved(pname, dest)
        
    def broadcast_move(self, name, dest):
        msg = {"author":name, "dest":dest}
        data = {"action": "move", "msg": msg}
        for chan in self.chan_to_name:
            chan.Send(data) 
 
