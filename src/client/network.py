from PodSixNet.Connection import connection, ConnectionListener
from client.events_client import SendChatEvt, NwRcvChatEvt, NwRcvNameChangeEvt, \
    NwRcvPlayerJoinEvt, NwRcvPlayerLeftEvt, NwRcvCharMoveEvt, SendMoveEvt, \
    NwRcvGameAdminEvt, NwRcvCreepJoinEvt, SendAtkEvt, NwRcvAtkEvt, NwRcvDeathEvt, \
    NwRcvRezEvt, NwRcvNameChangeFailEvt, NwRcvGreetEvt
from common.events import TickEvent
from common.messages import SrvGreetMsg, SrvPlyrJoinMsg, SrvPlyrLeftMsg, \
    ClNameChangeMsg, SrvNameChangeMsg, ClChatMsg, SrvChatMsg, ClMoveMsg, SrvMoveMsg, \
    SrvGameAdminMsg, SrvCreepJoinedMsg, unpack_msg, ClAtkMsg, SrvAtkMsg, SrvDeathMsg, \
    SrvRezMsg, SrvNameChangeFailMsg
import logging

log = logging.getLogger('client')

class NetworkController(ConnectionListener):


    def __init__(self, evManager, hostport, nick):
        """ open connection to the server """
        
        self._em = evManager
        self._em.reg_cb(TickEvent, self.on_tick)
        
        self._em.reg_cb(SendAtkEvt, self.on_sendattack)
        self._em.reg_cb(SendChatEvt, self.on_sendchat)
        self._em.reg_cb(SendMoveEvt, self.on_sendmove)
        
        self.preferrednick = nick
        host, port = hostport

        self.Connect((host, port))
        


    def on_tick(self, event):
        """ push and pull every game loop """
        self.Pump() # pull from socket and trigger Network_* callbacks
        connection.Pump() # push to socket


    def _send(self, data):
        """ Send data to the server.
        data is a dict.
        """
        log.debug('Send ' + str(data))
        connection.Send(data)
        
                        
    def Network(self, data):
        """ Receive data from the socket. 
        Triggered along all Network_* callbacks 
        """
        log.debug("Received " + str(data))
        

  
    def Network_connected(self, data):
        log.info("Client connected to the server " 
                      + str(connection.address))

    
    def Network_error(self, data):
        try:
            log.error("Network error: " + data['error'][1])
        except TypeError:
            log.error('Network error: ' + str(data['error']))
            log.error('The server is not running.')
        connection.Close()
    

    def Network_disconnected(self, data):
        """ don't let the player in game if the server goes down """
        log.info("Network disconnected.")
        connection.Close()
        exit()
    


    ####################  attack  ###############
    
    def on_sendattack(self, event):
        """ Send an attack msg to the server """
        dic = {'targetname': event.tname, 'dmg':event.dmg}
        amsg = ClAtkMsg(dic)
        self._send({'action':'attack', 'msg':amsg.d})
        
    def Network_attack(self, data):
        """ Receive atk message from server """
        atker, defer, dmg = unpack_msg(data['msg'], SrvAtkMsg)
        ev = NwRcvAtkEvt(atker, defer, dmg)
        self._em.post(ev)

    
    ##################  chat  ################    
    
    def on_sendchat(self, event):
        """ Send chat msg to server """
        txt = event.txt
        d = {'txt':txt}
        cmsg = ClChatMsg(d)
        self._send({"action": "chat", "msg": cmsg.d})
        
    def Network_chat(self, data):
        """ Receive chat msg from server. """
        author, txt = unpack_msg(data['msg'], SrvChatMsg)
        ev = NwRcvChatEvt(author, txt)
        self._em.post(ev)
        
        
    ####################  creepjoin  ############
    
    def Network_creepjoin(self, data):
        """ A creep arrived in the game. """
        cname, cinfo = unpack_msg(data['msg'], SrvCreepJoinedMsg)
        ev = NwRcvCreepJoinEvt(cname, cinfo)
        self._em.post(ev)
    
    
    ###################  death  ####################
    
    def Network_death(self, data):
        """ A charactor died. """
        name, = unpack_msg(data['msg'], SrvDeathMsg)
        ev = NwRcvDeathEvt(name)
        self._em.post(ev)


    ###################  gameadmin  ##################

    def Network_gameadmin(self, data):
        """ Received a game command from the server. """
        pname, cmd = unpack_msg(data['msg'], SrvGameAdminMsg)
        ev = NwRcvGameAdminEvt(pname, cmd)
        self._em.post(ev)


    
    ################ greet ##############

    """ PROTOCOL for connections, disconnections, and name changes:
    When the server detects a client connection, 
    the server sends to the client a greeting containing that client's 
    temporary name (an hexa string). 
    
    When the greet msg is received,
    the client asks the server to change to its preferred name. 
    The client knows if the server accepted the name change 
    by a namechange server broadcast.
    """    

    def Network_greet(self, data):
        """ Receive a greeting msg from the server. """
       
        #deserialize        
        tup = unpack_msg(data['msg'], SrvGreetMsg)  
        mapname, pname, myinfo, onlineppl, creeps = tup
        
        # start the client's game
        ev = NwRcvGreetEvt(mapname, pname, myinfo, onlineppl, creeps)
        self._em.post(ev)

        # ask for name change
        preferred_name = self.preferrednick
        if pname is not preferred_name:
            self.ask_namechange(preferred_name)
    
    
        
    ##################  move  ################    
        
    def on_sendmove(self, event):
        """ Send a movement msg to the server """
        dic = {'coords':event.coords, 'facing':event.facing}
        mmsg = ClMoveMsg(dic)
        self._send({'action':'move', 'msg':mmsg.d})
    
    def Network_move(self, data):
        """ Receive a movement msg from the server. """
        name, coords, facing = unpack_msg(data['msg'], SrvMoveMsg) 
        ev = NwRcvCharMoveEvt(name, coords, facing)
        self._em.post(ev)



    ############### namechange ############
    
    def Network_namechange(self, data):
        """ Someone changed name. """
        oldname, newname = unpack_msg(data['msg'], SrvNameChangeMsg)
        log.debug('namechange: %s becomes %s' %(oldname, newname))
        ev = NwRcvNameChangeEvt(oldname, newname)
        self._em.post(ev)
        
    def ask_namechange(self, newname):
        """ Ask the server to change name """
        d = {'pname':newname}
        nmsg = ClNameChangeMsg(d)
        self._send({"action": 'namechange', "msg":nmsg.d})

    def Network_namechangefail(self, data):
        """ Failed to change my name. """
        failname, reason = unpack_msg(data['msg'], SrvNameChangeFailMsg)
        ev = NwRcvNameChangeFailEvt(failname, reason)
        self._em.post(ev)
        
    
    
    ############  playerjoin  ###########
    
    def Network_playerjoin(self, data):
        """ A new player joined the game """
        pname, pinfo = unpack_msg(data['msg'], SrvPlyrJoinMsg) 
        ev = NwRcvPlayerJoinEvt(pname, pinfo)
        self._em.post(ev)
        
    #############  playerleft  #########
    
    def Network_playerleft(self, data):
        """ A player left the game. """
        pname, = unpack_msg(data['msg'], SrvPlyrLeftMsg) 
        ev = NwRcvPlayerLeftEvt(pname)
        self._em.post(ev)



    ############ resurrect ###############
    
    def Network_resurrect(self, data):
        """ A charactor was revived. """
        name, info = unpack_msg(data['msg'], SrvRezMsg) 
        ev = NwRcvRezEvt(name, info)
        self._em.post(ev)
        
        
