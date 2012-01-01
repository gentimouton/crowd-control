import sys
from time import sleep
from weakref import WeakKeyDictionary

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

class ClientChannel(Channel):
    """    This is the server representation of a single connected client. """
    def __init__(self, *args, **kwargs):
        self.nickname = "anonymous"
        Channel.__init__(self, *args, **kwargs)
    
    def Close(self):
        self._server.DelPlayer(self)
    
    ### Network specific callbacks ###
    
    def Network_message(self, data):
        print("received message: " + data['message'])
        self._server.SendToAll({"action": "message", "message": data['message'], "who": self.nickname})
    
    def Network_nickname(self, data):
        self.nickname = data['nickname']
        self._server.SendPlayers()

class ChatServer(Server):
    channelClass = ClientChannel
    
    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.playernames = WeakKeyDictionary()
        print('Server launched')
    
    def Connected(self, channel, addr):
        self.AddPlayer(channel)
    
    def AddPlayer(self, player):
        print("Add Player: " + str(player.addr))
        self.playernames[player] = True
        self.SendPlayers()
        #print ("playernames", [p for p in self.playernames])
    
    def DelPlayer(self, player):
        print ("Del Player: " + str(player.addr))
        del self.playernames[player]
        self.SendPlayers()
    
    def SendPlayers(self):
        self.SendToAll({"action": "playernames", "playernames": [p.nickname for p in self.playernames]})
    
    def SendToAll(self, data):
        [p.Send(data) for p in self.playernames]
    
    def Launch(self):
        while True:
            self.Pump()
            sleep(0.001)

# get command line argument of server, port
if len(sys.argv) != 2:
    host, port = 'localhost:8080'.split(':')
else:
    host, port = sys.argv[1].split(":")
s = ChatServer(localaddr=(host, int(port)))
s.Launch()

