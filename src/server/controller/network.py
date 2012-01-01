from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from server.config import config_get_host, config_get_port
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


    ######## TODO: junk
    def Network_pos(self, data):
        """ when a pos msg is received from a client, 
        broadcast an announce to everyone """
        self._server.send_pos_all(str(self.addr), data['pos'])





class NetworkController(Server):
    
    channelClass = ClientChannel
    
    def __init__(self, mediator):
        host, port = config_get_host(), config_get_port()
        Server.__init__(self, localaddr=(host, port))
        self.mediator = mediator
        self.playernames = WeakKeyDictionary() #maps channel to name
        self.playerchannels = WeakValueDictionary() #maps name to channel
        #WeakKeyDictionary's key is garbage collected and removed from dictionary 
        # when used nowhere else but in the dict's mapping
        print('Network up')



    ####### (dis)connection logic called by channel and calling to mediator

    def Connected(self, channel, addr):
        """ Called by Server.handle_accept() whenever a new client connects 
        channel is a channelClass
        and addr is [ip,port], which can be obtained from channel.addr too """
        name = str(channel.addr) #name can be changed by client
        # TODO: before updating the dicts, check there's no user with that name already
        # a malicious user could name himself 123.145.167.189:1234,
        # when an actual player connects from 123.145.167.189:1234,
        # he'll use the data left behind by the malicious user
        # solution: do not allow '.' or ':' in user-entered names
        self.playernames[channel] = name
        self.playerchannels[name] = channel
        self.mediator.player_arrived(name)
        
    def channel_closed(self, channel):
        """ when a player logs out, remove his channel from the list """
        name = self.playernames[channel]
        self.mediator.player_left(name)
        del self.playerchannels[name]
        del self.playernames[channel]

    def send_admin(self, status, name):
        """ notify clients that a new player just arrived (type='arrived') 
        or left (type='left') """
        data = {"action": 'admin', "msg": {"type":status, "name":name}}
        [p.Send(data) for p in self.playernames.keys()]

        
    #######  chat logic called by ClientChannel and Mediator        
        
    def received_chat(self, channel, txt):
        """ send a chat msg to all connected clients """
        author = self.playernames[channel]
        self.mediator.received_chat(txt, author)
        
    def broadcast_chat(self, txt, author):
        data = {"action": "chat", "msg": {"txt":txt, "author":author}}
        [p.Send(data) for p in self.playernames.keys()]

    def send_chat_to(self, txt, author, dest):
        pass # TODO: implement send_chat_to
    
    
        
    ############ TODO: JUNK
                 
    def send_pos_all(self, clientid, txt):
        """ for now, only send a chat msg to say where someone moved to """
        # TODO: pos msgs to clients should contain {player:id, pos:x,y}
        if len(self.playernames) > 0:
            data = {"action": "pos", "coords": txt}
            [p.Send(data) for p in self.playernames]
            
             
