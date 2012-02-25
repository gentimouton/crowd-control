from PodSixNet.Connection import connection, ConnectionListener
from client.events_client import SendChatEvt, NwRecChatEvt, NwRecGreetEvt, \
    NwRecNameChangeEvt, NwRecPlayerJoinEvt, NwRecPlayerLeft, NwRecAvatarMoveEvt, \
    SendMoveEvt, NwRecGameAdminEvt, NwRecCreepJoinEvt, NwRecCreepMoveEvt, SendAtkEvt
from common.events import TickEvent
from common.messages import GreetMsg, PlayerArrivedNotifMsg, PlayerLeftNotifMsg, \
    NameChangeRequestMsg, NameChangeNotifMsg, ClChatMsg, SrvChatMsg, ClMoveMsg, \
    SrvMoveMsg, SrvGameAdminMsg, SrvCreepJoinedMsg, SrvCreepMovedMsg, unpack_msg, \
    ClAtkMsg
import logging

class NetworkController(ConnectionListener):
    
    log = logging.getLogger('client')


    def __init__(self, evManager, hostport, nick):
        """ open connection to the server """
        self._em = evManager
        self._em.reg_cb(TickEvent, self.on_tick)
        self._em.reg_cb(SendChatEvt, self.on_sendchat)
        self._em.reg_cb(SendMoveEvt, self.on_sendmove)
        self._em.reg_cb(SendAtkEvt, self.on_sendatk)
        
        self.preferrednick = nick
        host, port = hostport
        self.Connect((host, port))
        
        
    def push(self): 
        """ push data to server """
        connection.Pump()
    
    def pull(self):
        """ pull data from the pipe and trigger the Network_* callbacks"""
        self.Pump() 

    def send(self, data):
        """ data is a dict """
        #self.log.debug('Network sends: ' + str(data))
        connection.Send(data)
        
                        
    def Network(self, data):
        """ triggered for any Network_* callback """
        #self.log.debug("Network received: " + str(data))


    ################## DEFAULT ADMIN ##########
  
    def Network_connected(self, data):
        self.log.info("Client connected to the server " 
                      + str(connection.address))

    
    def Network_error(self, data):
        try:
            self.log.error("Network error: " + data['error'][1])
        except TypeError:
            self.log.error('Network error: ' + str(data['error']))
            self.log.error('The server is not running.')
        connection.Close()
    

    def Network_disconnected(self, data):
        """ don't let the player in game if the server goes down """
        self.log.info("Network disconnected.")
        connection.Close()
        exit()
    
    
    
    ################## CHAT ################    
    
    def Network_chat(self, data):
        cmsg = SrvChatMsg(data['msg'])
        author = cmsg.d['pname']
        txt = cmsg.d['txt']
        ev = NwRecChatEvt(author, txt)
        self._em.post(ev)
        
        
    def on_sendchat(self, event):
        txt = event.txt
        d = {'txt':txt}
        cmsg = ClChatMsg(d)
        self.send({"action": "chat", "msg": cmsg.d})
        
    
    
    
    ################## MOVEMENT ################    
        
    def on_sendmove(self, event):
        dic = {'coords':event.coords, 'facing':event.facing}
        mmsg = ClMoveMsg(dic)
        self.send({'action':'move', 'msg':mmsg.d})
    
    def Network_move(self, data):
        pname, coords, facing = unpack_msg(data['msg'], SrvMoveMsg) 
        ev = NwRecAvatarMoveEvt(pname, coords, facing)
        self._em.post(ev)



    #################### ATTACKS ###############
    
    def on_sendatk(self, event):
        dic = {'targetname': event.target}
        amsg = ClAtkMsg(dic)
        self.send({'action':'atk', 'msg':amsg.d})
        
        
        

    
    ################### GAME ##################

    def Network_gameadmin(self, data):
        pname, cmd = unpack_msg(data['msg'], SrvGameAdminMsg)
        ev = NwRecGameAdminEvt(pname, cmd)
        self._em.post(ev)
        
    
    ################### CREEPS ##################

    def Network_creep(self, data):
        act = data['msg']['act'] # all creep msg have an act

        if act == 'join': # creep creation
            act, cname, coords, facing = unpack_msg(data['msg'], SrvCreepJoinedMsg)
            ev = NwRecCreepJoinEvt(cname, coords, facing)
            self._em.post(ev)
            
        elif act == 'move': # creep movement
            act, cname, coords, facing = unpack_msg(data['msg'], SrvCreepMovedMsg)
            ev = NwRecCreepMoveEvt(cname, coords, facing)
            self._em.post(ev)

    
    ################## (DIS)CONNECTION + NAME CHANGE CALLBACKS ################    
    
    """ PROTOCOL for (dis)connections and name changes:
    When the server detects a client connection, 
    the server sends to the client a greeting containing that client's 
    temporary name (an hexa string). When the greet msg is received,
    the client asks the server to change to its preferred name. 
    The client knows if the server accepted the
    name change by a server broadcast which triggers 
    a NwRecNameChangeEvt(oldname, newname). 
    TODO: if the name change was rejected, the client should be notified
    and the user should be told that his preferred name is already in use.
    """
        
    def Network_admin(self, data):
        """ greeting, left, arrived, and name change messages """
        actiontype = data['msg']['mtype'] # all admin msg have an mtype

        if actiontype == 'greet':
            tup = unpack_msg(data['msg'], GreetMsg) #deserialize 
            mapname, pname, coords, facing, onlineppl, creeps = tup
            
            preferred_name = self.preferrednick
            if pname is not preferred_name:
                self.ask_for_name_change(preferred_name)
            ev = NwRecGreetEvt(mapname, pname, coords, facing, onlineppl, creeps)
            self._em.post(ev)

        elif actiontype == 'namechange':
            nmsg = NameChangeNotifMsg(data['msg'])
            oldname = nmsg.d['oldname']
            newname = nmsg.d['newname']
            ev = NwRecNameChangeEvt(oldname, newname)
            self._em.post(ev)

        elif actiontype == 'arrived': # new player connected
                pname, coords, facing = unpack_msg(data['msg'], PlayerArrivedNotifMsg) 
                ev = NwRecPlayerJoinEvt(pname, coords, facing)
                self._em.post(ev)
    
        elif actiontype == 'left': # player left
            lmsg = PlayerLeftNotifMsg(data['msg'])
            ev = NwRecPlayerLeft(lmsg.d['pname'])
            self._em.post(ev)
        
            
            
    def ask_for_name_change(self, newname):
        d = {'pname':newname}
        nmsg = NameChangeRequestMsg(d)
        self.send({"action": 'admin', "msg":nmsg.d})

    
    
    def on_tick(self, event):
        """ push and pull every game loop """
        self.pull()
        self.push()
            
            
        

