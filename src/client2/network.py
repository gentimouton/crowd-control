from PodSixNet.Connection import connection, ConnectionListener
from client2.config import config_get_host, config_get_port, config_get_my_name
from client2.events import TickEvent, SendChatEvent, ReceivedChatEvent

class NetworkController(ConnectionListener):
    
    def __init__(self, evManager):
        """ open connection to the server """
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        host, port = config_get_host(), config_get_port()
        self.Connect((host, port))
        #print("Client connection initiated.")
        
        
    def push(self): 
        """ push data to server """
        #TODO: log what has been sent 
        connection.Pump()
    
    def pull(self):
        """ pull data from the pipe and trigger the Network_* callbacks"""
        self.Pump() 



    ################## DEFAULT ADMIN ##########
  
    def Network_connected(self, data):
        print("Client connected to the server", str(connection.address))

    
    def Network_error(self, data):
        try:
            print("Error:" + data['error'][1])
        except TypeError:
            print('Error:', data['error'])
        connection.Close()
    

    def Network_disconnected(self, data):
        # TODO: should try to get back the connection instead of exit()
        print("Client disconnected from the server.")
        connection.Close()
        exit()
    
    
    
    ################## CHAT ################    
    
    def Network_chat(self, data):
        author = data['msg']['author']
        txt = data['msg']['txt']
        ev = ReceivedChatEvent(author, txt)
        self.evManager.post(ev)
        
        
    def send_chat(self, txt):
        connection.Send({"action": "chat", "msg": txt})
    
    
    
    ################## MOVEMENT ################    
        
    def send_move(self, dest):
        connection.Send({'action':'move', 'msg':{'dest':dest}})
    
    def Network_move(self, data):
        author = data['msg']['author']
        dest = data['msg']['dest']
        #self.mc.someone_moved(author, dest)
        print('move', author, dest)
        # TODO: send msg to evtMgr
        
            
             
    ################## (DIS)CONNECTION + NAME CHANGE CALLBACKS ################    
    
    """ connection and name changing protocol:
    When the server end detects a client connection, 
    the server sends to the client a greeting containing that client's 
    temporary name (an hexa string). When the greet msg is received,
    the client asks the server to change to its preferred name. 
    The client knows if the server accepted the
    name change by a server broadcast which triggers 
    someone_changed_name(oldname=server-given-name). 
    TODO: if the name change was rejected, client should be notified
    and user should be told that the preferred name is already in use.
     """
        
    def Network_admin(self, data):
        """ left, join, and namechange messages """
        actiontype = data['msg']['type']
        if actiontype == 'namechange':
            oldname = data['msg']['old']
            newname = data['msg']['new']
            #self.mc.someone_changed_name(oldname, newname)
            print('namechange', oldname, newname)
            # TODO: send msg to evtMgr
        elif actiontype == 'greet':
            newname = data['msg']['newname']
            newpos = data['msg']['newpos']
            onlineppl = data['msg']['onlineppl']
            print('greet', newname, newpos, onlineppl)
            name_i_want = config_get_my_name()
            if newname is not name_i_want:
                self.ask_for_name_change(name_i_want)
            # TODO: send msg to evtMgr
        else: #(dis)connection
            name = data['msg']['name']
            #self.mc.someone_admin(name, actiontype) #TODO: send to evtMgr
            print('admindefault', name, actiontype)
            
            
    def ask_for_name_change(self, newname):
        msg = {'type':'namechange', 'newname':newname}
        connection.Send({"action": 'admin', "msg":msg})

    
    
    #################### MESSAGES FROM OTHER COMPONENTS ####################
     
    def notify(self, event):
        # TODO: only push and pull every once in a while, not every game loop
        if isinstance(event, TickEvent): 
            self.pull()
            self.push()
        elif isinstance(event, SendChatEvent):
            self.send_chat(event.txt)
            
    
            
