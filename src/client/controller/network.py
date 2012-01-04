from PodSixNet.Connection import connection, ConnectionListener
from client.config import config_get_host, config_get_port

class NetworkController(ConnectionListener):
    
    def __init__(self, mainctrler):
        ''' open connection to the server '''
        self.mc = mainctrler
        host, port = config_get_host(), config_get_port()
        self.Connect((host, port))
        #print("Client connection started")
        
        
    def push(self): 
        """ push data to server """
        #TODO: log what has been sent 
        connection.Pump()
    
    def pull(self):
        """ pull data from the pipe and trigger the Network_* callbacks"""
        self.Pump() 


    ################## OTHER CALLBACKS ##########
  
    def Network_connected(self, data):
        print("Client connected to the server", str(connection.address))

        
    def Network_error(self, data):
        print("Error:" + data['error'][1])
        connection.Close()
    
    def Network_disconnected(self, data):
        # TODO: should call maincontroller 
        # and try to get back the connection instead of exit()
        print("Client disconnected from the server.")
        connection.Close()
        exit()
    
    ################## GAME-RELATED CALLBACKS ################    
    
    # CHAT
    
    def Network_chat(self, data):
        author = data['msg']['author']
        txt = data['msg']['txt']
        self.mc.someone_said(author, txt)
        
    def send_chat(self, txt):
        connection.Send({"action": "chat", "msg": txt})
    
    # MOVEMENT 
        
    def send_move(self, dest):
        connection.Send({'action':'move', 'msg':{'dest':dest}})
    
    def Network_move(self, data):
        author = data['msg']['author']
        dest = data['msg']['dest']
        self.mc.someone_moved(author, dest)
        
    
    
                
    # disconnection, connection, name changes 
    
    def Network_admin(self, data):
        ''' left, join, and namechange messages '''
        actiontype = data['msg']['type']
        if actiontype == 'namechange':
            oldname = data['msg']['old']
            newname = data['msg']['new']
            self.mc.someone_changed_name(oldname, newname)
        elif actiontype == 'greet':
            newname = data['msg']['newname']
            newpos = data['msg']['newpos']
            onlineppl = data['msg']['onlineppl']
            self.mc.init_players(onlineppl)
            self.mc.i_changed_name(newname)
            self.mc.set_startpos(newpos)
        else: #(dis)connection
            name = data['msg']['name']
            self.mc.someone_admin(name, actiontype)
            
    def ask_for_name_change(self, newname):
        msg = {'type':'namechange', 'newname':newname}
        connection.Send({"action": 'admin', "msg":msg})

    
    

    
