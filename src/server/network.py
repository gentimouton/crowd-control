from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from common.events import TickEvent
from common.messages import SrvPlyrJoinMsg, SrvPlyrLeftMsg, ClNameChangeMsg, \
    ClChatMsg, SrvChatMsg, SrvGreetMsg, SrvNameChangeMsg, ClMoveMsg, SrvMoveMsg, \
    SrvGameAdminMsg, SrvCreepJoinedMsg, unpack_msg, ClAtkMsg, SrvAtkMsg, SrvDeathMsg, \
    SrvRezMsg, SrvNameChangeFailMsg
from server.config import config_get_hostport
from uuid import uuid4
from weakref import WeakKeyDictionary, WeakValueDictionary
import logging



class ClientChannel(Channel):

    log = logging.getLogger('server')

    def __str__(self):
        return str(self.addr) 
      
    def Close(self):
        """ built-in called by Channel.handle_close """
        self._server.channel_closed(self)

    ######## custom logic called by Channel.found_terminator()
    
    def Network(self, data):
        """ called for all received msgs """
        #self.log.debug('Received %s from %s' %(str(data), str(self.addr)))
        pass
        

    def Network_namechange(self, data):
        """ change name messages """
        # all SerializableMsg have an mtype        
        nmsg = ClNameChangeMsg(d_src=data['msg']) 
        self._server.rcv_namechange(self, nmsg.d['pname'])

    def Network_chat(self, data):
        """ when chat messages are received """ 
        txt, = unpack_msg(data['msg'], ClChatMsg) 
        self._server.rcv_chat(self, txt)
        
    def Network_move(self, data):
        """ movement messages """
        coords, facing = unpack_msg(data['msg'], ClMoveMsg) 
        self._server.rcv_move(self, coords, facing)

    def Network_attack(self, data):
        """ attack messages """
        tname, dmg = unpack_msg(data['msg'], ClAtkMsg)
        self._server.rcv_attack(self, tname, dmg)

    def Network_death(self, data):
        """ A player died. """
        self._server.rcv_death(self)
        


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


    
    def Connected(self, channel, addr):
        """ Inherited from PodSixNet.
        Called by Server.handle_accept() whenever a new client connects. 
        assign a temporary name to a client, a la IRC. 
        """
        
        self.log.debug('%s tries to connect' % str(addr))
        
        # accept connections only after model is built
        if not self.accept_connections: 
            return
        
        name = 'anon-' + str(uuid4())[:4] #random 32-hexadigit = 128-bit uuid 
        # Truncated to 4 hexa digits = 16^4 = 65k possibilities.
        # If by chance someone has this uuid name already, 
        # repick until unique.
        while name in self.chan_to_name.keys(): 
            name = 'anon-' + str(uuid4())[:4]
            
        self.chan_to_name[channel] = name
        self.name_to_chan[name] = channel
        
        self.log.debug('%s joined %s' % (name, str(channel.addr)))
        self.model.on_playerjoin(name)
        
        
        
    def channel_closed(self, channel):
        """ when a player logs out, remove his channel from the list """
        name = self.chan_to_name[channel]
        
        self.log.debug(name + ' disconnected ' + str(channel.addr))
        
        self.model.on_playerleft(name)
        

        del self.name_to_chan[name]
        del self.chan_to_name[channel]


    
    
    def on_tick(self, event):
        """ Pump the sockets every tick """
        self.Pump()
        
        
    def on_worldbuilt(self):
        """ Accept connections only after the model has been built. """
        self.accept_connections = True
        
        
    def _send(self, chan, data):
        """ send data to a channel """
        self.log.debug('%s is sent %s' % (self.chan_to_name[chan], str(data)))
        chan.Send(data)
        
    def _bc(self, data):
        """ Send data to all channels """
        for chan in self.chan_to_name:
            self._send(chan, data) 



    ################################ attack ##################################
    
    def rcv_attack(self, channel, tname, atk):
        """ A player attacked. """
        pname = self.chan_to_name[channel]
        self.model.on_attack(pname, tname, atk)
        
    def bc_attack(self, atkername, defername, dmg):
        """ Broadcast to everyone the attack of defername by atkername. """
        dic = {'atker':atkername,
               'defer':defername,
               'dmg': dmg}
        amsg = SrvAtkMsg(dic)
        data = {"action": "attack", "msg": amsg.d}
        self._bc(data)
        
        
        
    ##################  chat   ########################################
        
    def rcv_chat(self, channel, txt):
        """ A client sent a chat msg """
        pname = self.chan_to_name[channel]
        self.model.on_chat(pname, txt)
                        
    def bc_chat(self, pname, txt):
        """ send a chat msg to all connected clients """
        dic = {'author':pname, 'txt':txt}
        cmsg = SrvChatMsg(dic)
        data = {"action": "chat", "msg": cmsg.d}
        self._bc(data)
        



    #################### creepjoin ############
     
    def bc_creepjoin(self, name, cinfo):
        """ broadcast creep creation to clients.
        cinfo contains some information about the creep (max HP, pos) """
        dic = {"cname":name,
               'cinfo':cinfo}
        mmsg = SrvCreepJoinedMsg(dic)
        data = {"action": "creepjoin", "msg": mmsg.d}
        self._bc(data)

        


    ########################## death #################

    def bc_death(self, name):
        """ broadcast creep or avatar death """
        dic = {'name':name}
        dmsg = SrvDeathMsg(dic)
        data = {"action": "death", "msg": dmsg.d}
        self._bc(data)
    
    
    
    
    #############################  gameadmin  ###################    
 
    def bc_gameadmin(self, pname, cmd):
        mmsg = SrvGameAdminMsg({"pname":pname, 'cmd':cmd})
        data = {"action": "gameadmin", "msg": mmsg.d}
        self._bc(data) 
    
    
    
        
        
    ##########################  greet  ###################
    def greet(self, mapname, pname, myinfo, onlineppl, creeps):
        """ send greeting data to a player """
        
        dic = {'mapname':mapname,
               'pname':pname,
               'myinfo':myinfo, #contains player coords, facing, atk, and hp
               'onlineppl':onlineppl,
               'creeps':creeps}
        greetmsg = SrvGreetMsg(dic)
            
        name = greetmsg.d['pname']
        chan = self.name_to_chan[name]
        try:
            data = {"action": 'greet', "msg": greetmsg.d}
            self._send(chan, data)
        except KeyError:
            self.log.error('Could not find greet message data for ' + str(chan.addr))
        



    ######################  movement  #####################################
    
    def rcv_move(self, channel, coords, facing):
        """ Receive a movement message from a player """
        pname = self.chan_to_name[channel]
        self.model.on_move(pname, coords, facing)
        
        
    def bc_move(self, name, coords, facing):
        """ Broadcast the movement of a charactor to all players. """
        dic = {"name":name,
               "coords":coords,
               'facing':facing}
        mmsg = SrvMoveMsg(dic)
        data = {"action": "move", "msg": mmsg.d}
        self._bc(data)
        



            
    #############  namechange  #################
    
    
    
    def rcv_namechange(self, channel, newname):
        """ Tell the model tat a player wants to change her name. """
        self.log.debug('%s requests namechange' % self.chan_to_name[channel])
        oldname = self.chan_to_name[channel]
        self.model.on_playernamechange(oldname, newname)
               
            
    def bc_namechange(self, oldname, newname):
        """ update name<->channel mappings and notify all players """

        dic = {'oldname':oldname, 'newname':newname} 
        bcmsg = SrvNameChangeMsg(dic)
        
        # update my chan<->name mappings
        channel = self.name_to_chan[oldname]
        self.chan_to_name[channel] = newname
        self.name_to_chan[newname] = channel
        del self.name_to_chan[oldname]
        
        # notify everyone
        data = {'action':'namechange', 'msg':bcmsg.d}
        self._bc(data)


    def send_namechangefail(self, pname, failname, reason):
        """ Notify a player that his name could not be changed. 
        Reason is a string. 
        """
        dic = {'failname':failname,
               'reason':reason}
        fmsg = SrvNameChangeFailMsg(dic)
            
        chan = self.name_to_chan[pname]
        data = {"action": 'namechangefail', "msg": fmsg.d}
        self._send(chan, data)
        
        
        

    ############# playerjoin ############

    def bc_playerjoined(self, pname, pinfo):
        """ User arrived: notify everyone connected but him """
        dic = {'pname':pname,
               'pinfo': pinfo}
        bcmsg = SrvPlyrJoinMsg(dic)
        data = {"action": 'playerjoin', "msg": bcmsg.d}
        # broadcast to everyone BUT the player who just arrived
        for chan in self.chan_to_name:
            if self.chan_to_name[chan] != bcmsg.d['pname']:
                self._send(chan, data)
     
     
         
    ############### playerleft #############
     
    def bc_playerleft(self, pname):
        """ Notify everyone that a player disconnected. """
        dic = {'pname':pname}
        bcmsg = SrvPlyrLeftMsg(dic)
        data = {"action": 'playerleft', "msg": bcmsg.d}
        # The player who left has been deleted, so he won't be notified.
        self._bc(data)




    ################ warp ################
    
    def bc_resurrect(self, name, info):
        """ Notify everyone of a resurrection; send the charactor info. """
        dic = {"name":name,
               "info":info}
        wmsg = SrvRezMsg(dic)
        data = {"action": "resurrect", "msg": wmsg.d}
        self._bc(data)
        
