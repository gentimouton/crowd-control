from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from server.config import config_get_host, config_get_port
from weakref import WeakKeyDictionary

class ClientChannel(Channel):

    def Close(self):
        """ built-in called by Channel.handle_close """
        self._server.del_player(self)

    ######## custom logic called by Channel.found_terminator()
    
    def Network(self, data):
        """ called for all received msgs """
        # TODO: implement a logger
        pass
    
    def Network_chat(self, data):
        """ when chat messages are received, broadcast them to everyone """
        print("Received chat: " + data['msg'])
        self._server.send_chat_all(str(self.addr), data['msg'])

    def Network_pos(self, data):
        """ when a pos msg is received from a client, 
        broadcast an announce to everyone """
        self._server.send_pos_all(str(self.addr), data['pos'])





class ServerNetworkEngine(Server):
    """ all that deals with network on the server side """
    
    channelClass = ClientChannel

    # --- built-ins
    
    def __init__(self):
        host, port = config_get_host(), config_get_port()
        Server.__init__(self, localaddr=(host, port))
        self.players = WeakKeyDictionary()
        print('Server launched')
      

    def Connected(self, channel, addr):
        """ called by Server.handle_accept() 
        called whenever a new client connects to your server """
        print("Added Player: " + str(channel.addr))
        self.players[channel] = True




    #######  custom logic called by ClientChannel
    
    def del_player(self, player):
        """ when a player logs out, remove him from the list """
        print ("Deleted Player: " + str(player.addr))
        del self.players[player]
        
    def send_chat_all(self, clientid, txt):
        """ send a chat msg to all connected clients """
        if len(self.players) > 0:
            data = {"action": "chat", "msg": {"txt":txt, "author":clientid}}
            [p.Send(data) for p in self.players]
            
    def send_pos_all(self, clientid, txt):
        """ for now, only send a chat msg to say where someone moved to """
        # TODO: pos msgs to clients should contain {player:id, pos:x,y}
        if len(self.players) > 0:
            data = {"action": "pos", "coords": txt}
            [p.Send(data) for p in self.players]
            
             
