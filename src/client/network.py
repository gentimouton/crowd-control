from PodSixNet.Connection import connection, ConnectionListener
    

class Client(ConnectionListener):
    def __init__(self, host, port):
        self.Connect((host, port))
        print("Client started")
        #connection.Send({"action": "msg", "msg": "hello!"})
    
    def Network_connected(self, data):
        print("connected to the server")
    
    def Network_error(self, data):
        print("error:" + data['error'][1])
        connection.Close()
    
    def Network_disconnected(self, data):
        print("disconnected from the server")
        connection.Close()
        exit()
    
    def Network_chatmsg(self,data):
        print(data['msg'])

    def push_and_pull(self):
        connection.Pump() #push data to server
        self.Pump() #pull data from the pipe and trigger the Network_* callbacks
        
    def send_chatmsg(self,msg):
        print("I say: " + msg)
        connection.Send({"action": "chatmsg", "msg": msg})
        