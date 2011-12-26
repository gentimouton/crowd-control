from PodSixNet.Connection import connection, ConnectionListener
from client.config import config_get_host, config_get_port, config_get_fps
    

class Client(ConnectionListener):
    def __init__(self):
        self.Connect((config_get_host(), config_get_port()))
        # send updates to the server 5 times per sec
        # if fps<5, then send msg every frame
        if config_get_fps() < 5: 
            self.push_frame_mod = config_get_fps()/5
        else:
            self.push_frame_mod = 1
        print("Client connection started")
        #connection.Send({"action": "msg", "msg": "hello!"})
 
    def update(self, elapsed_frames):
        # send client updates to server
        if elapsed_frames % self.push_frame_mod == 0:
            self.push() 
        # check for updates every frame
        self.pull()
        # TODO: this should be triggered by the controller or the mechanics
        if elapsed_frames % 30 == 1:
            self.send_chatmsg("hello i'm a client")
        
           
    def Network_connected(self, data):
        print("Client connected to the server")
    
    def Network_error(self, data):
        print("error:" + data['error'][1])
        connection.Close()
    
    def Network_disconnected(self, data):
        print("Client disconnected from the server")
        connection.Close()
        exit()
    
    def Network_chatmsg(self,data):
        print(data['msg'])
        
    #push data to server
    def push(self):
        connection.Pump() 
        
    #pull data from the pipe and trigger the Network_* callbacks
    def pull(self):    
        self.Pump() 
        
    def send_chatmsg(self,msg):
        print("Client send: " + msg)
        connection.Send({"action": "chatmsg", "msg": msg})
        