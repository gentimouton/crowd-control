from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from common.events import TickEvent
from common.messages import PlayerArrivedNotifMsg, PlayerLeftNotifMsg, \
    NameChangeRequestMsg, ClChatMsg, SrvChatMsg, GreetMsg, NameChangeNotifMsg, \
    ClMoveMsg, SrvMoveMsg, SrvGameAdminMsg, SrvCreepJoinedMsg, SrvCreepMovedMsg, \
    unpack_msg, ClAtkMsg, SrvAtkMsg, SrvCreepDiedMsg
from server.config import config_get_hostport
from uuid import uuid4
from weakref import WeakKeyDictionary, WeakValueDictionary
import logging



class ClientChannel(Channel):

    log = logging.getLogger('server')
  
    def Close(self):
        """ built-in called by Channel.handle_close """
        self._server.channel_closed(self)

    ######## custom logic called by Channel.found_terminator()
    
    def Network(self, data):
        """ called for all received msgs """
        #self.log.debug('Received from ' + str(self.addr) + ' : ' + str(data))
        pass
        
    

    def Network_admin(self, data):
        """ change name messages """
        # all SerializableMsg have an mtype
        if data['msg']['mtype'] == 'namechange':
            nmsg = NameChangeRequestMsg(d_src=data['msg']) 
            self._server.received_name_change(self, nmsg.d['pname'])

    def Network_chat(self, data):
        """ when chat messages are received """ 
        txt, = unpack_msg(data['msg'], ClChatMsg) 
        self._server.received_chat(self, txt)
        
    def Network_move(self, data):
        """ movement messages """
        coords, facing = unpack_msg(data['msg'], ClMoveMsg) 
        self._server.received_move(self, coords, facing)

    def Network_atk(self, data):
        """ attack messages """
        tname, = unpack_msg(data['msg'], ClAtkMsg)
        self._server.received_atk(self, tname)
        


########################## SERVER ############################################



class NetworkController(Server):
    
    channelClass = ClientChannel # The Server needs that attribute to be set
    log = logging.getLogger('server')

    def __init__(self, evManager):
    
        host, port = config_get_hostport()
        Server.__init__(self, localaddr=(host, port))
                
        self._em = evManager
        self._em.reg_cb(TickEvent, self.on_tick)
        
        
        self.accept_connections = False # start accepting when model is ready
        
        self.chan_to_name = WeakKeyDictionary() #maps channel to name
        self.name_to_chan = WeakValueDictionary() #maps name to channel        
        #WeakKeyDictionary's key is garbage collected and removed from dictionary 
        # when used nowhere else but in the dict's mapping
        
        self.model = None # set by model later on
        
        self.log.debug('Server Network up')



    def on_tick(self, event):
        """ Pump the sockets every tick """
        self.Pump()
        
        
    def on_worldbuilt(self):
        """ Accept connections only after the model has been built. """
        self.accept_connections = True
        
        
    def send(self, chan, data):
        """ send data to a channel """
        #self.log.debug('Send to ' + str(chan.addr) + ' : ' + str(data))
        chan.Send(data)
        
        
    ####### (dis)connection and name changes 

    def Connected(self, channel, addr):
        """ Called by Server.handle_accept() whenever a new client connects. 
        assign a temporary name to a client, a la IRC. 
        The client should change user's name automatically if it's not taken
        already, and clients can use a command to change their name
        """
        
        self.log.debug('Connection try from ' + str(addr))
        
        # accept connections only after model is built
        if not self.accept_connections: 
            return
        
        name = str(uuid4())[:8] #random 32-hexadigit = 128-bit uuid 
        # Truncated to 8 hexits = 16^8 = 4 billion possibilities.
        # If by chance someone has this uuid name already, 
        # repick until unique.
        while name in self.chan_to_name.keys(): 
            name = str(uuid4())[:8]
        self.chan_to_name[channel] = name
        self.name_to_chan[name] = channel
        
        self.log.debug(name + ' joined ' + str(channel.addr))
        self.model.on_playerjoined(name)
        
        
    def channel_closed(self, channel):
        """ when a player logs out, remove his channel from the list """
        name = self.chan_to_name[channel]
        
        self.log.debug(name + ' disconnected ' + str(channel.addr))
        
        self.model.on_playerleft(name)
        

        del self.name_to_chan[name]
        del self.chan_to_name[channel]
        
        


    def bc_playerjoined(self, pname, coords, facing):
        """ User arrived: notify everyone connected but him """
        dic = {'pname':pname,
               'coords':coords,
               'facing':facing}
        bcmsg = PlayerArrivedNotifMsg(dic)
        data = {"action": 'admin', "msg": bcmsg.d}
        
        for chan in self.chan_to_name:
            if self.chan_to_name[chan] != bcmsg.d['pname']:
                self.send(chan, data)
     
     
    def bc_left(self, pname):
        """ Notify everyone connected. """
        dic = {'pname':pname}
        bcmsg = PlayerLeftNotifMsg(dic)
        data = {"action": 'admin', "msg": bcmsg.d}
             
        for chan in self.chan_to_name: 
            # The concerned player has been deleted, so he won't be notified
            self.send(chan, data) 
                

    def greet(self, mapname, pname, coords, facing, onlineppl, creeps):
        """ send greeting data to a player """
        
        dic = {'mapname':mapname,
               'pname':pname,
               'coords':coords,
               'facing':facing,
               'onlineppl':onlineppl,
               'creeps':creeps}
        greetmsg = GreetMsg(dic)
            
        name = greetmsg.d['pname']
        chan = self.name_to_chan[name]
        try:
            data = {"action": 'admin', "msg": greetmsg.d}
            self.send(chan, data)
        except KeyError:
            self.log.error('Could not find greet message data for ' + str(chan.addr))
        

    def received_name_change(self, channel, newname):
        """ notify that a player wants to change name """
        
        oldname = self.chan_to_name[channel]
        self.model.on_playerchangedname(oldname, newname)
               
            
    def bc_namechange(self, oldname, newname):
        """ update name<->channel mappings and notify all players """

        dic = {'oldname':oldname, 'newname':newname} 
        bcmsg = NameChangeNotifMsg(dic)
        
        # update my chan<->name mappings
        channel = self.name_to_chan[oldname]
        self.chan_to_name[channel] = newname
        self.name_to_chan[newname] = channel
        del self.name_to_chan[oldname]
        
        # notify everyone
        data = {'action':'admin', 'msg':bcmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data) 

        
        
        
    ##################  chat   ########################################
        
    def received_chat(self, channel, txt):
        """ send a chat msg to all connected clients """
        
        pname = self.chan_to_name[channel]
        self.model.received_chat(pname, txt)
                
        
    def bc_chat(self, pname, txt):
        
        dic = {'pname':pname, 'txt':txt}
        cmsg = SrvChatMsg(dic)
        
        data = {"action": "chat", "msg": cmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data)

    
    ###################### movement  #####################################
    
    def received_move(self, channel, coords, facing):
        pname = self.chan_to_name[channel]
        self.model.on_playermoved(pname, coords, facing)
        
        
        
    def bc_move(self, pname, coords, facing):
        dic = {"pname":pname,
               "coords":coords,
               'facing':facing}
        mmsg = SrvMoveMsg(dic)
        data = {"action": "move", "msg": mmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data) 
 
 
 
    ###################### attack  #####################################
    
    def received_atk(self, channel, tname):
        pname = self.chan_to_name[channel]
        self.model.on_charattacked(pname, tname)
        
    def bc_atk(self, atkername, defername, dmg):
        dic = {'atker':atkername,
               'defer':defername,
               'dmg': dmg}
        amsg = SrvAtkMsg(dic)
        data = {"action": "atk", "msg": amsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data) 
 
 
 
 
    ###################### GAME #############################################
    
    def bc_gameadmin(self, pname, cmd):
        mmsg = SrvGameAdminMsg({"pname":pname, 'cmd':cmd})
        data = {"action": "gameadmin", "msg": mmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data) 
        
        
    def bc_creepjoin(self, name, coords, facing):
        """ broadcast creep creation """
        dic = {'act':'join',
               "cname":name,
               'coords':coords,
               'facing':facing}
        mmsg = SrvCreepJoinedMsg(dic)
        data = {"action": "creep", "msg": mmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data) 
        
    def bc_creepmoved(self, name, coords, facing):
        """ broadcast creep movement """
        dic = {'act':'move',
               "cname":name,
               'coords':coords,
               'facing':facing}
        mmsg = SrvCreepMovedMsg(dic)
        data = {"action": "creep", "msg": mmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data) 


    def bc_creepdied(self, name):
        """ broadcast creep death """
        dic = {'act':'die',
               'cname':name}
        dmsg = SrvCreepDiedMsg(dic)
        data = {"action": "creep", "msg": dmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data) 

