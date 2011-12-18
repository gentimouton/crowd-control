from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from weakref import WeakKeyDictionary

class ClientChannel(Channel):

    # --- built-ins  
    
    def Close(self):
        #called by Channel.handle_close
        self._server.del_player(self)

    #  --- custom logic called by Channel.found_terminator()
    
    # called for all received messages
    def Network(self, data):
        # TODO: implement a logger
        pass
    
    # called when messages of type 'msg' are received
    def Network_chatmsg(self, data):
        #print("Received chatmsg: " + data['msg'])
        self._server.send_chatmsg_all(str(self.addr) + ' says: ' + data['msg'])


class ServerNetworkEngine(Server):
    """ all that deals with network on the server side
    """
    
    # custom-made ClientChannel
    channelClass = ClientChannel

    # --- built-ins
    
    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.players = WeakKeyDictionary()
        print('Server launched')
        
    # called by Server.handle_accept()
    def Connected(self, channel, addr):
        print("Add Player: " + str(channel.addr))
        self.players[channel] = True

    # --- custom logic
    
    #called by ClientChannel
    def del_player(self, player):
        print ("Del Player: " + str(player.addr))
        del self.players[player]
        
    def send_chatmsg_all(self,msg):
        if len(self.players) > 0:
            #print("Send: " + msg)
            data = {"action": "chatmsg", "msg": msg}
            [p.Send(data) for p in self.players]     