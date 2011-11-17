from PodSixNet.Connection import connection, ConnectionListener
from sys import exit

class Client(ConnectionListener):
    def __init__(self, host, port):
        self.Connect((host, port))
        print("Chat client started")
        connection.Send({"action": "nickname", "nickname": 'testName'})
    
    # app-specific
    
    def Loop(self): 
        connection.Pump()
        self.Pump() # why are there 2 pumps here?
    
    def send_msg(self,msg):
        connection.Send({"action": "message", "message": msg})
    

    # built in Network event/message callbacks 
    
    def Network_connected(self, data):
        print ("You are now connected to the server")
    
    def Network_error(self, data):
        print('error: ', data['error'][1])
        connection.Close()
    
    def Network_disconnected(self, data):
        print ('Server disconnected')
        exit()
