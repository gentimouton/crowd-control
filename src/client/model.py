from client.events_client import InputMoveRequest, ModelBuiltMapEvent, \
    NwRecChatEvt, ChatlogUpdatedEvent, NwRecGreetEvt, NwRecPlayerLeft, \
    CharactorRemoveEvent, NwRecAvatarMoveEvt, NwRecPlayerJoinEvt, NwRecNameChangeEvt, \
    LocalAvatarPlaceEvent, OtherAvatarPlaceEvent, LocalAvatarMoveEvent, \
    RemoteCharactorMoveEvent, NwRecGameAdminEvt, NwRecCreepJoinEvt, CreepPlaceEvent, \
    NwRecCreepMoveEvt, MyNameChangedEvent, MdAddPlayerEvt, InputAtkRequest
from collections import deque
from common.world import World
import logging
from common.constants import DIRECTION_UP





class Game:
    """ The top of the model. Contains players and world. """

    log = logging.getLogger('client')
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(NwRecGreetEvt, self.on_greeted)
        # all other callbacks are registered AFTER having been greeted
        
        self.players = dict() #unlike WeakValueDict, I need to remove players manually
        self.creeps = dict() #need to remove creeps manually when they die
        
        self.world = World(evManager, self.log)
        self.chatlog = ChatLog(evManager)


    ########################################################################

        
    def build_map(self, mapname):
        """ load world from file """
        self.mapname = mapname
        self.world.build_world(self.mapname, ModelBuiltMapEvent)

    
    
    def on_greeted(self, event):
        """ When the server greets me, set my name,
        start world building process, and add other connected players.
        Start also listening to player inputs, and other network messages.
        """
        
        mapname, newname = event.mapname, event.newname
        newpos, facing = event.newpos, event.facing
        onlineppl, creeps = event.onlineppl, event.creeps
            
        self.myname = newname
        
        self.build_map(mapname)
        
        # creeps
        for cid, coords_facing in creeps.items():
            coords, facing = coords_facing
            self.add_creep(cid, coords, facing)
            
        # myself, local player
        self.add_player(newname, newpos, facing)
        # others, remote players
        for name, pos_facing in onlineppl.items():
            pos, facing = pos_facing
            self.add_player(name, pos, facing)
           
        # start listening to game events coming from the network
        
        # -- PLAYERS
        self._em.reg_cb(NwRecPlayerJoinEvt, self.on_playerjoin)
        self._em.reg_cb(NwRecPlayerLeft, self.on_playerleft)
        self._em.reg_cb(NwRecNameChangeEvt, self.on_namechange)
        
        # -- AVATARS (remote and local)
        self._em.reg_cb(NwRecAvatarMoveEvt, self.on_remoteavmove)
        self._em.reg_cb(InputMoveRequest, self.on_localavmove)
        self._em.reg_cb(InputAtkRequest, self.on_localatk)
        
        # -- RUNNING GAME and CREEPS
        self._em.reg_cb(NwRecGameAdminEvt, self.on_gameadmin)
        self._em.reg_cb(NwRecCreepJoinEvt, self.on_creepjoin)
        self._em.reg_cb(NwRecCreepMoveEvt, self.on_creepmove)
        
        


    ##################  PLAYERS  #####################################
    
    def on_playerjoin(self, event):
        """ When a new player arrives, add him to the connected players. """
        self.add_player(event.pname, event.pos, event.facing)
        
        
    def add_player(self, pname, pos, facing):
        """ add a new player to the list of connected players """
        cell = self.world.get_cell(pos)
        
        # whether that Player is the local client or a remote client
        islocal = hasattr(self, 'myname') and pname == self.myname 
        
        newplayer = Player(pname, cell, facing, islocal, self._em)       
        self.players[pname] = newplayer
        
        # notify the view 
        ev = MdAddPlayerEvt(pname)
        self._em.post(ev)
        
        
    def on_playerleft(self, event):
        """ remove a player """
        pname = event.pname
        try:
            self.players[pname].remov()
            #don't forget to clean the player data from the dict
            del self.players[pname]
        except KeyError:
            self.log.warning('Player ' + pname + ' had already been removed') 
        
    
    def on_namechange(self, event):
        """ update players' names when they change it """
        
        oldname, newname = event.oldname, event.newname
         
        if newname in self.players:
            self.log.warning(oldname + ' changed name to ' + newname 
                             + ' which was already in use')
        
        if self.myname == oldname:
            self.myname = newname
            # notify the widget in charge of holding my name
            ev = MyNameChangedEvent(oldname, newname)
            self._em.post(ev)
            
        player = self.players[oldname]
        player.name = newname
        self.players[newname] = player
        del self.players[oldname] #only del the mapping, not the player itself


    
    ###############################  AVATARS  ############################
        
    
    def on_remoteavmove(self, event):
        """ Move the avatar of the player which name is pname. """
        pname, dest = event.pname, event.dest
        
        if pname != self.myname:
            avatar = self.players[pname].avatar
            destcell = self.world.get_cell(dest)
            avatar.move_absolute(destcell)


    def on_localavmove(self, event):
        """ When the user pressed up,down,right,or left, move his avatar. """
        mychar = self.players[self.myname].avatar
        mychar.move_relative(event.direction)


    def on_localatk(self, event):
        """ When user pressed atk button, make him atk. """
        mychar = self.players[self.myname].avatar
        mychar.atk_local()

    
    ###################### RUNNING GAME + CREEPS ############################
    
    def on_gameadmin(self, event):
        """ If game stops, remove creeps. """
        if event.cmd == 'stop':
            # '/stop' happens rarely, so we can afford to copy the whole dict
            oldcreeps = self.creeps.copy()
            for cid in oldcreeps.keys():
                self.remove_creep(cid)
            
        self.log.info(event.pname + ' ' + event.cmd + ' the game')
        
        
    
    def on_creepjoin(self, event):
        """ Create a creep. """
        cid, coords, facing = event.cid, event.coords, event.facing
        self.add_creep(cid, coords, facing)
        
        
    def on_creepmove(self, event):
        """ Move a creep. """
        cid, coords = event.cid, event.coords
        creep = self.creeps[cid]
        creep.move_absolute(self.world.get_cell(coords))
        
    
    def remove_creep(self, cid):
        """ remove a creep """
        try:
            self.creeps[cid].rmv()
            del self.creeps[cid]
        except KeyError:
            self.log.warning('Creep ' + str(cid) + ' had already been removed') 
        
        
    def add_creep(self, cid, coords, facing):
        """ Add a new creep to the existing creeps. """
        cell = self.world.get_cell(coords)
        creep = Creep(self._em, cid, cell, facing)       
        self.creeps[cid] = creep



        
##############################################################################



class Player():
    """ the model structure for a person playing the game 
    It has name, score, etc. 
    """
    def __init__(self, name, cell, facing, islocal, evManager):
        self._em = evManager

        self.name = name
        self.avatar = Avatar(self, cell, facing, islocal, evManager) 


    def __str__(self):
        return '<Player %s %s>' % (self.name, id(self))


    def remov(self):
        """ tell the view to remove that player's avatar """
        self.avatar.rmv()




##############################################################################


class Charactor():
    """ A local or remote entity representing players or creeps. 
    It is located on a cell, and can move to another cell.
    """
    
    log = logging.getLogger('client')

    def __init__(self, cell, facing, name, evManager):
        self._em = evManager
        self.cell = cell
        self.facing = facing # which direction the charactor is facing
        self.name = name
                

    def move_absolute(self, destcell):
        """ move to the specified destination """ 
        if destcell:
            self.cell = destcell
            ev = RemoteCharactorMoveEvent(self, destcell.coords)
            self._em.post(ev)
            
        else: #illegal move
            self.log.warning('Illegal move from ' + self.name)
            #TODO: should report to server of potential cheat/hack
            pass
        
    def rmv(self):
        """ tell the view to remove this charactor's spr """ 
        ev = CharactorRemoveEvent(self)
        self._em.post(ev)

        
    
    
class Avatar(Charactor):
    """ An entity controlled by a player.
    Right now, the mapping is 1-to-1: one avatar per player. 
    """
    
    def __init__(self, player, cell, facing, islocal, evManager):
        
        self.player = player
        Charactor.__init__(self, cell, facing, player.name, evManager)
        
        self.islocal = islocal #whether the avatar is controlled by the client
        
        if islocal:
            ev = LocalAvatarPlaceEvent(self, cell)
        else: #avatar from someone else
            ev = OtherAvatarPlaceEvent(self, cell)
        self._em.post(ev)
        

    def __str__(self):
        return '<Avatar %s from player %s>' % (id(self), self.player.name)


    def move_relative(self, direction):
        """ If possible, move towards that direction. """

        dest_cell = self.cell.get_adjacent_cell(direction)
        if dest_cell:
            self.cell = dest_cell
            self.facing = direction
            # send to view and server that I moved
            ev = LocalAvatarMoveEvent(self, dest_cell.coords, direction)
            self._em.post(ev)

        else: #move is not possible: TODO: give (audio?) feedback 
            pass 

    
    def atk_local(self):
        """ Attack a creep in the vicinity, 
        and send action + amount of damage to the server. 
        """
        cell = self.cell.get_adjacent_cell(self.facing)
        # TODO: ATTACK!
        
        

class Creep(Charactor):
    """ Representation of a remote enemy monster. """
        
    def __init__(self, evManager, cid, cell, facing):
        
        Charactor.__init__(self, cell, str(cid), facing, evManager)
        
        ev = CreepPlaceEvent(self)# ask view to display the new creep
        self._em.post(ev)
        
    
    def __str__(self):
        return '<Creep %s named %s>' % (id(self), self.name)


        

########################### CHATLOG ####################################


class ChatLog():
    """ store all that deals with the chat window """
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(NwRecChatEvt, self.add_chatmsg)
        
        #double-ended queue to remember the most recent 30 messages
        self.chatlog = deque(maxlen=30) 
            
    
    
    def add_chatmsg(self, event):
        """ add a message to the chatlog.
        if full, remove oldest message 
        """
        author, txt = event.pname, event.txt
        msg = {'pname':author, 'text':txt}
        self.chatlog.appendleft(msg)
        
        ev = ChatlogUpdatedEvent(author, txt)
        self._em.post(ev)


    
