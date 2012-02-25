from client.events_client import InputMoveRequest, ModelBuiltMapEvent, \
    NwRecChatEvt, ChatlogUpdatedEvent, NwRecGreetEvt, NwRecPlayerLeft, \
    CharactorRemoveEvent, NwRecAvatarMoveEvt, NwRecPlayerJoinEvt, NwRecNameChangeEvt, \
    LocalAvatarPlaceEvent, OtherAvatarPlaceEvent, SendMoveEvt, \
    RemoteCharactorMoveEvent, NwRecGameAdminEvt, NwRecCreepJoinEvt, CreepPlaceEvent, \
    NwRecCreepMoveEvt, MyNameChangedEvent, MdAddPlayerEvt, InputAtkRequest, \
    SendAtkEvt
from collections import deque
from common.world import World
import logging





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
        """ When the server greets me, set my cname,
        start world building process, and add other connected players and creeps.
        Start also listening to player inputs, and other network messages.
        """
        
        mapname, newname = event.mapname, event.newname
        newpos, facing = event.newpos, event.facing
        onlineppl, creeps = event.onlineppl, event.creeps
            
        self.myname = newname
        
        self.build_map(mapname)
        
        # creeps
        for cname, coords_facing in creeps.items():
            coords, facing = coords_facing
            self.add_creep(cname, coords, facing)
            
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
            self.log.warning(oldname + ' changed cname to ' + newname 
                             + ' which was already in use')
        
        if self.myname == oldname:
            self.myname = newname
            # notify the widget in charge of holding my cname
            ev = MyNameChangedEvent(oldname, newname)
            self._em.post(ev)
            
        player = self.players[oldname]
        player.changename(newname)
        self.players[newname] = player
        del self.players[oldname] #only del the mapping, not the player itself


    
    ###############################  AVATARS  ############################
        
    
    def on_remoteavmove(self, event):
        """ Move the avatar of the player which cname is pname. """
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
            for cname in oldcreeps.keys():
                self.remove_creep(cname)
            
        self.log.info(event.pname + ' ' + event.cmd + ' the game')
        
        
    
    def on_creepjoin(self, event):
        """ Create a creep. """
        cname, coords, facing = event.cname, event.coords, event.facing
        self.add_creep(cname, coords, facing)
        
        
    def on_creepmove(self, event):
        """ Move a creep. """
        cname, coords = event.cname, event.coords
        creep = self.creeps[cname]
        creep.move_absolute(self.world.get_cell(coords))
        
    
    def remove_creep(self, cname):
        """ remove a creep """
        try:
            self.creeps[cname].rmv()
            del self.creeps[cname]
        except KeyError:
            self.log.warning('Creep ' + str(cname) + ' had already been removed') 
        
        
    def add_creep(self, cname, coords, facing):
        """ Add a new creep to the existing creeps. """
        cell = self.world.get_cell(coords)
        creep = Creep(self._em, cname, cell, facing)       
        self.creeps[cname] = creep



        
##############################################################################



class Player():
    """ the model structure for a person playing the game 
    It has cname, score, etc. 
    """
    def __init__(self, name, cell, facing, islocal, evManager):
        self._em = evManager

        self.cname = name
        self.avatar = Avatar(self, cell, facing, islocal, evManager) 


    def __str__(self):
        return '<Player %s %s>' % (self.cname, id(self))

    def changename(self, name):
        self.cname = name
        self.avatar.changename(name)
        

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
        
        self.facing = facing # which direction the charactor is facing
        self.cname = name
        
        self.cell = cell
        self.cell.add_occ(name)
        
                

    def changename(self, newname):
        """ update my cname, and notify my cell """
        self.cell.occ_chngname(self.cname, newname)
        self.cname = newname
        
        
    def move_absolute(self, destcell):
        """ move to the specified destination.
        During a split second, the charactor is in no cell. 
        """ 
        if destcell:
            self.cell.rm_occ(self.cname)
            self.cell = destcell
            self.cell.add_occ(self.cname)
            ev = RemoteCharactorMoveEvent(self, destcell.coords)
            self._em.post(ev)
            
        else: #illegal move
            self.log.warning('Illegal move from ' + self.cname)
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
        Charactor.__init__(self, cell, facing, player.cname, evManager)
        
        self.islocal = islocal #whether the avatar is controlled by the client
        
        if islocal:
            ev = LocalAvatarPlaceEvent(self, cell)
        else: #avatar from someone else
            ev = OtherAvatarPlaceEvent(self, cell)
        self._em.post(ev)
        
    
    def __str__(self):
        return '<Avatar %s from player %s>' % (id(self), self.player.cname)


    def move_relative(self, direction):
        """ If possible, move towards that direction. """

        dest_cell = self.cell.get_adjacent_cell(direction)
        if dest_cell:
            self.cell.rm_occ(self.cname)
            self.cell = dest_cell
            self.cell.add_occ(self.cname)
            self.facing = direction
            # send to view and server that I moved
            ev = SendMoveEvt(self, dest_cell.coords, direction)
            self._em.post(ev)

        else: #move is not possible: TODO: give (audio?) feedback 
            pass 

    
    def atk_local(self):
        """ Attack a creep in the vicinity, 
        and send action + amount of damage to the server. 
        """
        target_cell = self.cell.get_adjacent_cell(self.facing)
        if target_cell: #only attack walkable cells
            occupant = target_cell.get_occ() # occupant picked randomly
            
            if occupant: # there's creep or avatar to attack
                ev = SendAtkEvt(occupant)
                self._em.post(ev)
            else:
                # dont attack if the cell has no occupant
                pass
                
                    
        

class Creep(Charactor):
    """ Representation of a remote enemy monster. """
        
    def __init__(self, evManager, cname, cell, facing):
        
        Charactor.__init__(self, cell, facing, cname, evManager)
        
        ev = CreepPlaceEvent(self)# ask view to display the new creep
        self._em.post(ev)
        
    
    def __str__(self):
        return '<Creep %s named %s>' % (id(self), self.cname)


        

########################### CHATLOG ####################################


class ChatLog():
    """ store all that deals with the chat window """
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(NwRecChatEvt, self.add_chatmsg)
        
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


    
