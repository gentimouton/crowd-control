from client.av import Avatar
from client.events_client import InputMoveRequest, ModelBuiltMapEvent, \
    NwRcvGreetEvt, NwRcvPlayerJoinEvt, NwRcvPlayerLeftEvt, NwRcvNameChangeEvt, \
    InputAtkRequest, NwRcvCharMoveEvt, NwRcvAtkEvt, NwRcvGameAdminEvt, \
    NwRecCreepJoinEvt, NwRcvDeathEvt, MdAddPlayerEvt, MyNameChangedEvent, \
    NwRcvChatEvt, ChatlogUpdatedEvent, CharactorRemoveEvent, NwRcvWarpEvt
from client.npc import Creep
from collections import deque
from common.world import World
import logging






class Game:
    """ The top of the model. Contains players and world. """

    log = logging.getLogger('client')
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(NwRcvGreetEvt, self.on_greeted)
        # all other callbacks are registered AFTER having been greeted
        
        self.avs = dict() # currently connected avatars from players
        self.creeps = dict() #need to remove creeps manually when they die
        
        self.acceptinput = False # start accepting player input after greeted by server
        
        self.world = World(evManager, self.log)
        self.chatlog = ChatLog(evManager)


    ########################################################################

        
    def build_map(self, mapname):
        """ load world from file """
        self.mapname = mapname
        self.world.build_world(self.mapname, ModelBuiltMapEvent)

    
    
    def on_greeted(self, event):
        """ When the server greets me, set my name,
        start world building process, and add other connected players and creeps.
        Start also listening to player inputs, and other network messages.
        """
        
        mapname, newname = event.mapname, event.newname
        myinfo = event.myinfo
        onlineppl, creeps = event.onlineppl, event.creeps

        self.build_map(mapname)
        
        # myself, local player
        # The map has to be built before positioning the player's avatar.
        self.myname = newname
        self.log.info('My name is %s' % newname)
        self.add_player(newname, myinfo) 
        
        # creeps
        for cname, creepinfo in creeps.items():
            self.add_creep(cname, creepinfo)
            
        # remote players
        for pname, pinfo in onlineppl.items():
            self.add_player(pname, pinfo)
           
        # start listening to game events coming from the network
        
        # -- PLAYERS
        self._em.reg_cb(NwRcvPlayerJoinEvt, self.on_playerjoin)
        self._em.reg_cb(NwRcvPlayerLeftEvt, self.on_playerleft)
        self._em.reg_cb(NwRcvNameChangeEvt, self.on_namechange)
        
        # -- LOCAL events (attacks, moves, and removals)
        self._em.reg_cb(InputMoveRequest, self.on_localavmove)
        self._em.reg_cb(InputAtkRequest, self.on_localatk)
        self._em.reg_cb(CharactorRemoveEvent, self.on_localremoval)
        self.acceptinput = True
        
        # -- REMOTE events (attacks, moves, spawns, and deaths)
        self._em.reg_cb(NwRcvCharMoveEvt, self.on_remotemove)
        self._em.reg_cb(NwRcvAtkEvt, self.on_remoteatk)
        self._em.reg_cb(NwRcvWarpEvt, self.on_remotewarp)

        # -- RUNNING GAME and CREEPS
        self._em.reg_cb(NwRcvGameAdminEvt, self.on_gameadmin)
        self._em.reg_cb(NwRecCreepJoinEvt, self.on_creepjoin)
        self._em.reg_cb(NwRcvDeathEvt, self.on_death)
        
        


    def get_charactor(self, name):
        """ Return a SCharactor (SCreep or SAvatar) from its name """
        if name in self.avs:
            return self.avs[name]
        else: 
            try: 
                return self.creeps[name]
            except KeyError: # creep not found
                self.log.error("Creep %s not found" % name)
                return None


    ##################  PLAYERS  #####################################
    
    def on_playerjoin(self, event):
        """ When a new player arrives, add him to the connected players. """
        self.add_player(event.pname, event.pinfo)
        
        
    def add_player(self, pname, pinfo):
        """ add a new player to the list of connected players.
        pinfo contains a dic made by the server-side SAvatar object. 
        """
        coords, facing = pinfo['coords'], pinfo['facing']
        atk, hp = pinfo['atk'], pinfo['hp']
        cell = self.world.get_cell(coords)

        # whether that Player is the local client or a remote client
        islocal = hasattr(self, 'myname') and pname == self.myname 
        
        newplayer = Avatar(pname, cell, facing, atk, hp, islocal, self._em)       
        self.avs[pname] = newplayer
        
        # notify the view 
        ev = MdAddPlayerEvt(pname)
        self._em.post(ev)
        
        
    def on_playerleft(self, event):
        """ remove a player """
        pname = event.pname
        try:
            self.avs[pname].rmv()
            #don't forget to clean the player data from the dict
            del self.avs[pname]
        except KeyError:
            self.log.warning('Player ' + pname + ' had already been removed') 
        
    
    def on_namechange(self, event):
        """ update players' names when they change it """
        
        oldname, newname = event.oldname, event.newname
         
        if newname in self.avs:
            self.log.warning('%s changed name to %s, which was already in use'
                             % (oldname, newname))
        
        if self.myname == oldname:
            self.myname = newname
            # notify the widget in charge of holding my cname
            self.log.info('Changed name to %s' % newname)
            ev = MyNameChangedEvent(oldname, newname)
            self._em.post(ev)
            
        av = self.avs[oldname]
        av.changename(newname)
        self.avs[newname] = av
        del self.avs[oldname] #only del the mapping, not the player itself


    ########### LOCAL 

    def on_localavmove(self, event):
        """ Unless dead, when the user pressed up, down, right, or left,
        move his avatar.
        """
        if self.acceptinput:
            mychar = self.avs[self.myname]
            mychar.move_relative(event.direction)


    def on_localatk(self, event):
        """ Unless dead, when user pressed atk button, make him atk. """
        if self.acceptinput:
            mychar = self.avs[self.myname]
            mychar.atk_local()
    
    
    def on_localremoval(self, event):
        """ A charactor (Creep or avatar) is dead locally. 
        If this charactor is me, stop forwarding input events to the avatar.
        Start re-accepting inputs when the server acknowledges my death 
        and resurrect me.
        """
        ch = event.charactor
        if ch.name == self.myname:
            self.acceptinput = False
        
    
    ########## REMOTE
        
    
    def on_remotemove(self, event):
        """ Move the avatar of the player which cname is pname. """
        name, coords = event.name, event.coords
        
        if name != self.myname: # client is in charge of making its local av move
            char = self.get_charactor(name)
            destcell = self.world.get_cell(coords)
            char.move_absolute(destcell)


    def on_remoteatk(self, event):
        """ Only execute attacks from other charactors than myself.
        My attacks are executed by the model right when inputed by the player. 
        """
        atker = self.get_charactor(event.atker)
        defer = self.get_charactor(event.defer)
        if atker.name != self.myname:
            dmg = event.dmg
            self.log.info('Remote: %s attacked %s for %d dmg' 
                          % (event.atker, event.defer, dmg))
            defer.rcv_dmg(dmg)
        
    
    def on_remotewarp(self, event):
        """ A charactor teleported. """
        name, info = event.name, event.info
        coords = info['coords']
        if name == self.myname:
            # TODO: notify view to resurrect my sprite at the entrance
            self.log.info('I should be warped to %s' % str(coords))
        elif name in self.avs:
            # TODO: notify view to resurrect that player's sprite at entrance
            self.log.info('%s should be warped to %s' % (name, str(coords)))
        
    
    ###################### RUNNING GAME + CREEPS ############################
    
    def on_gameadmin(self, event):
        """ If game stops, remove creeps. """
        if event.cmd == 'stop':
            # '/stop' happens rarely, so we can afford to copy the whole dict
            oldcreeps = self.creeps.copy()
            for cname in oldcreeps.keys():
                self.remove_creep(cname)
            
        self.log.info(event.pname + ' ' + event.cmd + ' the game')
        
        
    
    def on_creepjoin(self, event):
        """ Create a creep. """
        cname, cinfo = event.cname, event.cinfo
        self.add_creep(cname, cinfo)
        
        
    def on_death(self, event):
        """ A creep or avatar died. """
        name = event.name
        if name in self.creeps: # a creep died
            self.remove_creep(event.name)
        elif name == self.myname: # my avatar died
            self.log.info('I should die')
        elif name in self.avs: # another avatar died
            self.log.info('player %s should die' % (name))
        
        
        
    def add_creep(self, cname, creepinfo):
        """ Add a new creep to the existing creeps.
        Info is a dic made on the server side by SCreep. """
        cell, facing = self.world.get_cell(creepinfo['coords']), creepinfo['facing']
        atk, hp = creepinfo['atk'], creepinfo['hp']
        
        creep = Creep(self._em, cname, cell, facing, atk, hp)       
        self.creeps[cname] = creep


    def remove_creep(self, cname):
        """ remove a creep """
        try:
            self.creeps[cname].rmv()
            del self.creeps[cname]
        except KeyError:
            self.log.warning('Creep ' + str(cname) + ' had already been removed') 
        
        






        

########################### CHATLOG ####################################


class ChatLog():
    """ store all that deals with the chat window """
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(NwRcvChatEvt, self.add_chatmsg)
        
        #double-ended queue to remember the most recent 30 messages
        self.chatlog = deque(maxlen=30) 
            
    
    
    def add_chatmsg(self, event):
        """ Add a message to the chatlog.
        If full, remove oldest message. 
        """
        author, txt = event.pname, event.txt
        msg = {'pname':author, 'text':txt}
        self.chatlog.appendleft(msg) #will remove oldest msg automatically
        
        ev = ChatlogUpdatedEvent(author, txt)
        self._em.post(ev)


    
