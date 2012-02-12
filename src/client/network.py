from PodSixNet.Connection import connection, ConnectionListener
from client.config import config_get_nick, config_get_hostport
from client.events_client import SendChatEvent, \
    NetworkReceivedChatEvent, ClGreetEvent, ClNameChangeEvent, ClPlayerArrived, \
    ClPlayerLeft, NetworkReceivedCharactorMoveEvent, LocalCharactorMoveEvent
from common.events import TickEvent
from common.messages import GreetMsg, PlayerArrivedNotifMsg, PlayerLeftNotifMsg, \
    NameChangeRequestMsg, NameChangeNotifMsg, ClChatMsg, SrvChatMsg, ClMoveMsg, \
    SrvMoveMsg
import logging

class NetworkController(ConnectionListener):
    
    log = logging.getLogger('client')


    def __init__(self, evManager):
        """ open connection to the server """
        self._em = evManager
        self._em.reg_cb(TickEvent, self.on_tick)
        self._em.reg_cb(SendChatEvent, self.send_chat)
        self._em.reg_cb(LocalCharactorMoveEvent, self.send_move)
        
        host, port = config_get_hostport()
        self.Connect((host, port))
        
        
    def push(self): 
        """ push data to server """
        connection.Pump()
    
    def pull(self):
        """ pull data from the pipe and trigger the Network_* callbacks"""
        self.Pump() 

    def send(self, data):
        """ data is a dict """
        self.log.debug('Network sends: ' + str(data))
        connection.Send(data)
        
                        
    def Network(self, data):
        """ triggered for any Network_* callback """
        self.log.debug("Network received: " + str(data))


    ################## DEFAULT ADMIN ##########
  
    def Network_connected(self, data):
        self.log.info("Client connected to the server " 
                      + str(connection.address))

    
    def Network_error(self, data):
        try:
            self.log.error("Network error: " + data['error'][1])
        except TypeError:
            self.log.error('Network error: ' + data['error'])
        connection.Close()
    

    def Network_disconnected(self, data):
        # TODO: should try to get back the connection instead of exit()
        self.log.info("Network disconnected.")
        connection.Close()
        exit()
    
    
    
    ################## CHAT ################    
    
    def Network_chat(self, data):
        cmsg = SrvChatMsg(data['msg'])
        author = cmsg.d['pname']
        txt = cmsg.d['txt']
        ev = NetworkReceivedChatEvent(author, txt)
        self._em.post(ev)
        
        
    def send_chat(self, event):
        txt = event.txt
        d = {'txt':txt}
        cmsg = ClChatMsg(d)
        self.send({"action": "chat", "msg": cmsg.d})
        
    
    
    
    ################## MOVEMENT ################    
        
    def send_move(self, event):
        coords = event.coords
        mmsg = ClMoveMsg({'coords':coords})
        self.send({'action':'move', 'msg':mmsg.d})
    
    def Network_move(self, data):
        mmsg = SrvMoveMsg(data['msg'])
        pname = mmsg.d['pname']
        coords = mmsg.d['coords']
        ev = NetworkReceivedCharactorMoveEvent(pname, coords)
        self._em.post(ev)

        
            
             
    ################## (DIS)CONNECTION + NAME CHANGE CALLBACKS ################    
    
    """ PROTOCOL for (dis)connections and name changes:
    When the server detects a client connection, 
    the server sends to the client a greeting containing that client's 
    temporary name (an hexa string). When the greet msg is received,
    the client asks the server to change to its preferred name. 
    The client knows if the server accepted the
    name change by a server broadcast which triggers 
    a ClNameChangeEvent(oldname, newname). 
    TODO: if the name change was rejected, the client should be notified
    and the user should be told that his preferred name is already in use.
    """
        
    def Network_admin(self, data):
        """ greeting, left, arrived, and name change messages """
        actiontype = data['msg']['mtype'] # all admin msg have an mtype

        if actiontype == 'greet':
            gmsg = GreetMsg(data['msg']) #build msg from dictionary
            preferred_name = config_get_nick()
            if gmsg.d['pname'] is not preferred_name:
                self.ask_for_name_change(preferred_name)
            ev = ClGreetEvent(gmsg.d['mapname'], gmsg.d['pname'],
                              gmsg.d['coords'], gmsg.d['onlineppl'])
            self._em.post(ev)

        elif actiontype == 'namechange':
            nmsg = NameChangeNotifMsg(data['msg'])
            oldname = nmsg.d['oldname']
            newname = nmsg.d['newname']
            ev = ClNameChangeEvent(oldname, newname)
            self._em.post(ev)

        elif actiontype == 'arrived': # new player connected
                amsg = PlayerArrivedNotifMsg(data['msg']) 
                ev = ClPlayerArrived(amsg.d['pname'], amsg.d['coords'])
                self._em.post(ev)
    
        elif actiontype == 'left': # player left
            lmsg = PlayerLeftNotifMsg(data['msg'])
            ev = ClPlayerLeft(lmsg.d['pname'])
            self._em.post(ev)
        
            
            
    def ask_for_name_change(self, newname):
        d = {'pname':newname}
        nmsg = NameChangeRequestMsg(d)
        self.send({"action": 'admin', "msg":nmsg.d})

    
    
    def on_tick(self, event):
        # TODO: only push and pull every once in a while, not every game loop
        self.pull()
        self.push()
            
            
        

