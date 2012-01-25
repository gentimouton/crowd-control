from PodSixNet.Connection import connection, ConnectionListener
from client2.config import config_get_host, config_get_port, config_get_my_name
from client2.events_client import ClientTickEvent, SendChatEvent, \
    NetworkReceivedChatEvent, ServerGreetEvent, ServerNameChangeEvent, \
    ServerPlayerArrived, ServerPlayerLeft, NetworkReceivedCharactorMoveEvent, \
    SendCharactorMoveEvent
from common.messages import GreetMsg, BroadcastArrivedMsg, BroadcastLeftMsg

class NetworkController(ConnectionListener):
    
    def __init__(self, evManager):
        """ open connection to the server """
        self.evManager = evManager
        self.evManager.register_listener(self)
        
        host, port = config_get_host(), config_get_port()
        self.Connect((host, port))
        
        
    def push(self): 
        """ push data to server """
        #TODO: log what has been sent 
        connection.Pump()
    
    def pull(self):
        """ pull data from the pipe and trigger the Network_* callbacks"""
        # TODO: log what's been received
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
        ev = NetworkReceivedChatEvent(author, txt)
        self.evManager.post(ev)
        
        
    def send_chat(self, txt):
        connection.Send({"action": "chat", "msg": txt})
    
    
    
    ################## MOVEMENT ################    
        
    def send_move(self, dest):
        connection.Send({'action':'move', 'msg':{'dest':dest}})
    
    def Network_move(self, data):
        author = data['msg']['author']
        dest = data['msg']['dest']
        ev = NetworkReceivedCharactorMoveEvent(author, dest)
        self.evManager.post(ev)

        
            
             
    ################## (DIS)CONNECTION + NAME CHANGE CALLBACKS ################    
    
    """ PROTOCOL for (dis)connections and name changes:
    When the server detects a client connection, 
    the server sends to the client a greeting containing that client's 
    temporary name (an hexa string). When the greet msg is received,
    the client asks the server to change to its preferred name. 
    The client knows if the server accepted the
    name change by a server broadcast which triggers 
    a ServerNameChangeEvent(oldname, newname). 
    TODO: if the name change was rejected, the client should be notified
    and the user should be told that his preferred name is already in use.
    """
        
    def Network_admin(self, data):
        """ greeting, left, arrived, and name change messages """
        actiontype = data['msg']['mtype'] # all SerializableMsg have an mtype

        if actiontype == 'greet':
            greetmsg = GreetMsg(d_src=data['msg']) #build msg from dictionary
            preferred_name = config_get_my_name()
            if greetmsg.d['pname'] is not preferred_name:
                self.ask_for_name_change(preferred_name)
            ev = ServerGreetEvent(greetmsg.d['mapname'], greetmsg.d['pname'], 
                                  greetmsg.d['coords'], greetmsg.d['onlineppl'])
            self.evManager.post(ev)

        elif actiontype == 'namechange':
            oldname = data['msg']['old']
            newname = data['msg']['new']
            ev = ServerNameChangeEvent(oldname, newname)
            self.evManager.post(ev)

        elif actiontype == 'arrived': # new player connected
                msg = BroadcastArrivedMsg(d_src=data['msg']) 
                ev = ServerPlayerArrived(msg.d['pname'], msg.d['coords'])
                self.evManager.post(ev)
    
        elif actiontype == 'left': # player left
            msg = BroadcastLeftMsg(d_src=data['msg'])
            ev = ServerPlayerLeft(msg.d['pname'])
            self.evManager.post(ev)
        
            
            
    def ask_for_name_change(self, newname):
        msg = {'mtype':'namechange', 'newname':newname}
        connection.Send({"action": 'admin', "msg":msg})

    
    
    #################### MESSAGES FROM OTHER COMPONENTS ####################
     
    def notify(self, event):
        # TODO: only push and pull every once in a while, not every game loop
        if isinstance(event, ClientTickEvent):
            self.pull()
            self.push()
        elif isinstance(event, SendChatEvent):
            self.send_chat(event.txt)
        elif isinstance(event, SendCharactorMoveEvent):
            self.send_move(event.coords)
            
