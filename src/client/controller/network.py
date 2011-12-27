from PodSixNet.Connection import connection, ConnectionListener
from client.config import config_get_host, config_get_port, config_get_fps, \
    config_get_push_freq
from time import sleep
    

class NetworkController(ConnectionListener):
    
    def __init__(self, mainctrler):
        """ send updates to the server push_freq times per sec
        if fps < push_freq, then send updates every frame """
        self.mc = mainctrler
        self.connected = False
        self.Connect((config_get_host(), config_get_port()))        
        push_freq = config_get_push_freq()
        fps = config_get_fps()
        if fps > push_freq: 
            self.push_frame_mod = fps / push_freq
        else:
            self.push_frame_mod = 1
        print("Client connection started")
        #connection.Send({"action": "msg", "msg": "hello!"})
        

    
    def push(self): 
        """ push data to server """
        #TODO: log what has been sent here
        connection.Pump()
    
    def pull(self):
        """ pull data from the pipe and trigger the Network_* callbacks"""
        self.Pump() 

        
    ################## GAME-RELATED CALLBACKS ################    
    
    
    def Network_chat(self, data):
        # TODO: call mainController to have the msg stored in chatlog
        print("chat:" + data['txt'])
        
    def send_chat(self, txt):
        print("Client send chat: " + txt)
        connection.Send({"action": "chat", "msg": txt})
        
        
    def Network_pos(self, data):
        # TODO: call mainController to have the msg stored in chatlog
        print("chat:" + data['pos'])
        
    def send_pos(self, pos):
        print("Client send pos: " + pos)
        connection.Send({"action": "pos", "msg": pos})
    
    

    ################## OTHER CALLBACKS ##########
 
 
    def Network_connected(self, data):
        if self.connected == True:
            return
        else:
            self.connected = True
            print("Client connected to the server")
        
    
    def Network_error(self, data):
        print("Error:" + data['error'][1])
        connection.Close()
    
    def Network_disconnected(self, data):
        # TODO: should call maincontroller 
        # and try to get back the connection instead of exit()
        print("Client disconnected from the server.")
        connection.Close()
        exit()
    
    
