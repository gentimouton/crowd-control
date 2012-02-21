from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from common.events import TickEvent
from common.messages import PlayerArrivedNotifMsg, PlayerLeftNotifMsg, \
    NameChangeRequestMsg, ClChatMsg, SrvChatMsg, GreetMsg, NameChangeNotifMsg, \
    ClMoveMsg, SrvMoveMsg, SrvGameStartMsg, SrvCreepJoinedMsg, SrvCreepMovedMsg
from server.config import config_get_hostport
from server.events_server import SPlayerArrivedEvent, SSendGreetEvent, \
    SPlayerLeftEvent, SPlayerNameChangeRequestEvent, SBroadcastNameChangeEvent, \
    SReceivedChatEvent, SBroadcastChatEvent, SReceivedMoveEvent, SBroadcastMoveEvent, \
    SModelBuiltWorldEvent, SBroadcastArrivedEvent, SBroadcastLeftEvent, \
    SGameStartEvent, SBroadcastCreepArrivedEvent, SBroadcastCreepMoveEvent
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
        
    

    def Network_admin(self, data):
        """ change name messages """
        # all SerializableMsg have an mtype
        if data['msg']['mtype'] == 'namechange':
            nmsg = NameChangeRequestMsg(d_src=data['msg']) 
            self._server.received_name_change(self, nmsg.d['pname'])

    def Network_chat(self, data):
        """ when chat messages are received """ 
        cmsg = ClChatMsg(data['msg'])
        self._server.received_chat(self, cmsg)
        
    def Network_move(self, data):
        """ movement messages """
        mmsg = ClMoveMsg(data['msg']) 
        self._server.received_move(self, mmsg.d['coords'])




########################## SERVER ############################################



class NetworkController(Server):
    
    channelClass = ClientChannel # The Server needs that attribute to be set
    log = logging.getLogger('server')

    def __init__(self, evManager):
    
        host, port = config_get_hostport()
        Server.__init__(self, localaddr=(host, port))
                
        self._em = evManager
        self._em.reg_cb(TickEvent, self.on_tick)
        self._em.reg_cb(SModelBuiltWorldEvent, self.on_worldbuilt)
        self._em.reg_cb(SSendGreetEvent, self.greet)
        self._em.reg_cb(SBroadcastArrivedEvent, self.on_broadcastarrived)
        self._em.reg_cb(SBroadcastLeftEvent, self.on_broadcastleft)
        self._em.reg_cb(SBroadcastNameChangeEvent, self.broadcast_name_change)
        self._em.reg_cb(SBroadcastChatEvent, self.broadcast_chat)
        self._em.reg_cb(SBroadcastMoveEvent, self.broadcast_move)
        self._em.reg_cb(SGameStartEvent, self.broadcast_gamestart)
        self._em.reg_cb(SBroadcastCreepArrivedEvent, self.broadcast_creepjoined)
        self._em.reg_cb(SBroadcastCreepMoveEvent, self.broadcast_creepmoved)
        
        self.accept_connections = False # start accepting when model is ready
        
        self.chan_to_name = WeakKeyDictionary() #maps channel to name
        self.name_to_chan = WeakValueDictionary() #maps name to channel        
        #WeakKeyDictionary's key is garbage collected and removed from dictionary 
        # when used nowhere else but in the dict's mapping
        
        self.log.debug('Server Network up')



    def on_tick(self, event):
        """ Pump the sockets every tick """
        self.Pump()
        
        
    def on_worldbuilt(self, event):
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
        
        event = SPlayerArrivedEvent(name)
        self._em.post(event)
        
        
    def channel_closed(self, channel):
        """ when a player logs out, remove his channel from the list """
        name = self.chan_to_name[channel]
        
        self.log.debug(name + ' disconnected ' + str(channel.addr))
        
        event = SPlayerLeftEvent(name)
        self._em.post(event)

        del self.name_to_chan[name]
        del self.chan_to_name[channel]
        
        


    def on_broadcastarrived(self, event):
        """ User arrived: notify everyone connected but him """
        dic = {'pname':event.pname,
               'coords':event.coords}
        bcmsg = PlayerArrivedNotifMsg(dic)
        data = {"action": 'admin', "msg": bcmsg.d}
        
        for chan in self.chan_to_name:
            if self.chan_to_name[chan] != bcmsg.d['pname']:
                self.send(chan, data)
     
     
    def on_broadcastleft(self, event):
        """ Notify everyone connected. """
        dic = {'pname':event.pname}
        bcmsg = PlayerLeftNotifMsg(dic)
        data = {"action": 'admin', "msg": bcmsg.d}
             
        for chan in self.chan_to_name: 
            # The concerned player has been deleted, so he won't be notified
            self.send(chan, data) 
                

    def greet(self, event):
        """ send greeting data to a player """
        
        dic = {'mapname':event.mapname,
               'pname':event.pname,
               'coords':event.coords,
               'onlineppl':event.onlineppl,
               'creeps':event.creeps}
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
        event = SPlayerNameChangeRequestEvent(oldname, newname)
        self._em.post(event)
        
        
            
    def broadcast_name_change(self, event):
        """ update name<->channel mappings and notify all players """
        
        dic = {'oldname':event.oldname,
               'newname':event.newname} 
        bcmsg = NameChangeNotifMsg(dic)
            
        oldname = bcmsg .d['oldname']
        newname = bcmsg .d['newname']
        
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
        
    def received_chat(self, channel, cmsg):
        """ send a chat msg to all connected clients """
        
        author = self.chan_to_name[channel]
        
        event = SReceivedChatEvent(author, cmsg.d['txt'])
        self._em.post(event)
        
        
    def broadcast_chat(self, event):
        
        dic = {'pname':event.pname, 'txt':event.txt}
        cmsg = SrvChatMsg(dic)
        
        data = {"action": "chat", "msg": cmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data)

    
    ###################### movement  #####################################
    
    def received_move(self, channel, dest):
        pname = self.chan_to_name[channel]
        
        event = SReceivedMoveEvent(pname, dest)
        self._em.post(event)
        
        
    def broadcast_move(self, event):
        name, coords = event.pname, event.coords
        mmsg = SrvMoveMsg({"pname":name, "coords":coords})
        data = {"action": "move", "msg": mmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data) 
 
 
    ###################### GAME #############################################
    
    def broadcast_gamestart(self, event):
        pname = event.pname
        mmsg = SrvGameStartMsg({"pname":pname})
        data = {"action": "gamestart", "msg": mmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data) 
        
        
    def broadcast_creepjoined(self, event):
        cid, coords = event.creepid, event.coords
        mmsg = SrvCreepJoinedMsg({"creepid":cid, 'coords':coords, 'act':'join'})
        data = {"action": "creep", "msg": mmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data) 
        
    def broadcast_creepmoved(self, event):
        cid, coords = event.creepid, event.coords
        mmsg = SrvCreepMovedMsg({"creepid":cid, 'act':'move', 'coords':coords})
        data = {"action": "creep", "msg": mmsg.d}
        for chan in self.chan_to_name:
            self.send(chan, data) 
