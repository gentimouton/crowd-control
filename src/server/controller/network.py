from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from common.messages import BroadcastArrivedMsg, BroadcastLeftMsg
from server.config import config_get_host, config_get_port
from server.events_server import ServerTickEvent, SPlayerArrivedEvent, \
    SSendGreetEvent, SBroadcastStatusEvent, SPlayerLeftEvent, \
    SPlayerNameChangeRequestEvent, SBroadcastNameChangeEvent, SReceivedChatEvent, \
    SBroadcastChatEvent, SReceivedMoveEvent, SBroadcastMoveEvent, \
    SModelBuiltWorldEvent
from uuid import uuid4
from weakref import WeakKeyDictionary, WeakValueDictionary

class ClientChannel(Channel):
      
    def Close(self):
        """ built-in called by Channel.handle_close """
        self._server.channel_closed(self)

    ######## custom logic called by Channel.found_terminator()
    
    def Network(self, data):
        """ called for all received msgs """
        # TODO: implement a logger
        pass
    
    def Network_chat(self, data):
        """ when chat messages are received """ 
        self._server.received_chat(self, data['msg'])

    def Network_admin(self, data):
        """ change name messages """
        if data['msg']['mtype'] == 'namechange':
            self._server.received_name_change(self, data['msg']['newname'])

    def Network_move(self, data):
        """ movement messages """
        dest = data['msg']['dest'] 
        self._server.received_move(self, dest)




########################## SERVER ############################################



class NetworkController(Server):
    
    channelClass = ClientChannel
    
    def __init__(self, evManager):
    
        host, port = config_get_host(), config_get_port()
        Server.__init__(self, localaddr=(host, port))
                
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        self.accept_connections = False # start accepting when model is ready
        
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
        already, and clients can use a command to change their name
        """
        
        # accept connections only after model is built
        if not self.accept_connections: 
            return
        
        name = str(uuid4())[:8] #random 32-hexadigit = 128-bit uuid 
        # Truncated to 8 hexits = 16^8 = 4 billion possibilities.
        # If by chance someone has this uuid name already, 
        # repick until unique.
        while name in self.chan_to_name.keys(): 
            name = str(uuid4())[:8]
        self.chan_to_name[channel] = name
        self.name_to_chan[name] = channel
        
        event = SPlayerArrivedEvent(name)
        self.evManager.post(event)
        
        
    def channel_closed(self, channel):
        """ when a player logs out, remove his channel from the list """
        name = self.chan_to_name[channel]
        event = SPlayerLeftEvent(name)
        self.evManager.post(event)

        del self.name_to_chan[name]
        del self.chan_to_name[channel]


    def broadcast_conn_status(self, bcmsg):
        """ notify clients that a new player just arrived or left """
        
        data = {"action": 'admin', "msg": bcmsg.d}
        
        # user joined: notify everyone connected but him
        if isinstance(bcmsg, BroadcastArrivedMsg):
            for chan in self.chan_to_name:
                if self.chan_to_name[chan] != bcmsg.d['pname']:
                    chan.Send(data)
                    
        # user left: notify everyone
        elif isinstance(bcmsg, BroadcastLeftMsg): 
            for chan in self.chan_to_name: 
                # The concerned player has been deleted, so he won't be notified
                chan.Send(data) 
                

    def greet(self, greetmsg):
        """ send greeting data to a player """
        
        name = greetmsg.d['pname']
        chan = self.name_to_chan[name]
        chan.Send({"action": 'admin', "msg": greetmsg.d})


    def received_name_change(self, channel, newname):
        """ notify that a player wants to change name """
        oldname = self.chan_to_name[channel]
        
        event = SPlayerNameChangeRequestEvent(oldname, newname)
        self.evManager.post(event)
        
        
            
    def broadcast_name_change(self, oldname, newname):
        """ update name<->channel mappings and notify all players """
        channel = self.name_to_chan[oldname]
        self.chan_to_name[channel] = newname
        self.name_to_chan[newname] = channel
        del self.name_to_chan[oldname]
        msg = {'mtype':'namechange', 'old':oldname, 'new':newname}
        for c in self.chan_to_name:
            c.Send({'action':'admin', 'msg':msg}) 

        
        
        
    ##################  chat   ########################################
        
    def received_chat(self, channel, txt):
        """ send a chat msg to all connected clients """
        author = self.chan_to_name[channel]
        
        event = SReceivedChatEvent(author, txt)
        self.evManager.post(event)
        
        
    def broadcast_chat(self, txt, author):
        data = {"action": "chat", "msg": {"txt":txt, "author":author}}
        for chan in self.chan_to_name:
            chan.Send(data) 

    
    ###################### movement  #####################################
    
    def received_move(self, channel, dest):
        pname = self.chan_to_name[channel]
        
        event = SReceivedMoveEvent(pname, dest)
        self.evManager.post(event)
        
        
    def broadcast_move(self, name, dest):
        msg = {"author":name, "dest":dest}
        data = {"action": "move", "msg": msg}
        for chan in self.chan_to_name:
            chan.Send(data) 
 
 
 
 
    ######### event notifications #####################################
    
    def notify(self, event):
        
        if isinstance(event, ServerTickEvent):
            self.Pump()
        
        # accept connections only after the model has been built
        elif isinstance(event, SModelBuiltWorldEvent):
            self.accept_connections = True
            
        elif isinstance(event, SSendGreetEvent):
            self.greet(event.greetmsg)
        
        elif isinstance(event, SBroadcastStatusEvent):
            self.broadcast_conn_status(event.bcmsg)
            
        elif isinstance(event, SBroadcastNameChangeEvent):
            self.broadcast_name_change(event.oldname, event.newname)
        
        elif isinstance(event, SBroadcastChatEvent):
            self.broadcast_chat(event.txt, event.pname)
            
        elif isinstance(event, SBroadcastMoveEvent):
            self.broadcast_move(event.pname, event.coords)
            