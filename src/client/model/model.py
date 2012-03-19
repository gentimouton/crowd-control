""" 
The client model is only a shallow copy of the server model.
Dead reckoning happens for some actions of the local entities.
Local actions with far-reaching consequences are only dead-reckoned 
to the point where they do not have to be rollbacked if they are wrong. 
"""

from client.model.av import Avatar
from client.model.chatlog import ChatLog
from client.events_client import InputMoveRequest, MNameChangedEvt, \
    NwRcvPlayerJoinEvt, NwRcvPlayerLeftEvt, NwRcvNameChangeEvt, InputAtkRequest, \
    NwRcvCharMoveEvt, NwRcvAtkEvt, NwRcvGameAdminEvt, NwRcvCreepJoinEvt, \
    NwRcvDeathEvt, MdAddPlayerEvt, MMyNameChangedEvent, NwRcvRezEvt, \
    RemoteCharactorAtkEvt, NwRcvGreetEvt, NwRcvNameChangeFailEvt, MNameChangeFailEvt, \
    MGameAdminEvt, MPlayerLeftEvt, MGreetNameEvt, MBuiltMapEvt, NwRcvMoveSpeedEvt
from client.model.npc import Creep
from common.world import World
import logging

log = None # logger

class Game:
    """ The top of the model. Contains players and world. """

    
    def __init__(self, evManager):
        """Create the world and wait for the greet msg from the server. """
        
        global log
        log = logging.getLogger('client')
        
        self._em = evManager
        self._em.reg_cb(NwRcvGreetEvt, self.on_greet)
        # all other callbacks are registered AFTER having been greeted
        
        self.avs = dict() # currently connected avatars from players
        self.creeps = dict() #need to remove creeps manually when they die
        
        self.acceptinput = False # start accepting player input after greeted by server
        
        self.world = World(evManager, log)
        self.chatlog = ChatLog(evManager)



    
    #############  greet  #############
     
    def on_greet(self, event):
        """ When the server greets me, set my name,
        start world building process, and add other connected players and creeps.
        Start also listening to player inputs, and other network messages.
        """
        
        mapname, newname = event.mapname, event.newname
        myinfo = event.myinfo
        onlineppl, creeps = event.onlineppl, event.creeps
        
        # build map and notify the view when it's done
        self.mapname = mapname
        self.world.build_world(mapname, MBuiltMapEvt)
        
        # myself, local player
        # The map has to be built before positioning the player's avatar.
        self.myname = newname
        log.info('My name is %s' % newname)
        self.add_player(newname, myinfo)
        # notify the view 
        ev = MGreetNameEvt(newname)
        self._em.post(ev)
        
        # creeps
        for cname, creepinfo in creeps.items():
            self.add_creep(cname, creepinfo)
            
        # remote players
        for pname, pinfo in onlineppl.items():
            self.add_player(pname, pinfo)
           

        # -- start listening to player's input and network messages

        self._em.reg_cb(InputAtkRequest, self.on_localatk)
        self._em.reg_cb(NwRcvAtkEvt, self.on_remoteatk)
        
        self._em.reg_cb(InputMoveRequest, self.on_localavmove)
        self._em.reg_cb(NwRcvCharMoveEvt, self.on_remotemove)
        self._em.reg_cb(NwRcvMoveSpeedEvt, self.on_movespeedchange)
        
        self._em.reg_cb(NwRcvPlayerJoinEvt, self.on_playerjoin)
        self._em.reg_cb(NwRcvCreepJoinEvt, self.on_creepjoin)
        self._em.reg_cb(NwRcvPlayerLeftEvt, self.on_playerleft)
        
        self._em.reg_cb(NwRcvNameChangeEvt, self.on_namechange)
        self._em.reg_cb(NwRcvNameChangeFailEvt, self.on_namechangefail)
        
        self._em.reg_cb(NwRcvDeathEvt, self.on_death)
        self._em.reg_cb(NwRcvRezEvt, self.on_resurrect)
        
        self._em.reg_cb(NwRcvGameAdminEvt, self.on_gameadmin)
        
        self.acceptinput = True
        


    def get_charactor(self, name):
        """ Return a SCharactor (SCreep or SAvatar) from its name """
        if name in self.avs:
            return self.avs[name]
        else: 
            try: 
                return self.creeps[name]
            except KeyError: # creep not found
                log.error("Creep %s not found" % name)
                return None




    ############  attack  ##########
    
    
    def on_localatk(self, event):
        """ Unless dead, when user pressed atk button, make him atk. """
        
        if self.acceptinput:
            mychar = self.avs[self.myname]
            mychar.atk_local()


    def on_remoteatk(self, event):
        """ When the server tells about an attack, update the local model.
        My attacks also update the model when they come from the server,
        not when the player inputs them and the dmg are displayed on the screen. 
        """
        
        atker = self.get_charactor(event.atker)
        defer = self.get_charactor(event.defer)
        
        dmg = event.dmg
        if atker.name != self.myname: # when attacks from remote charactors
            ev = RemoteCharactorAtkEvt(atker) # notify the view
            self._em.post(ev)
        defer.rcv_dmg(dmg) 
        
    

    ##########  death  #########
    
        
    def on_death(self, event):
        """ A creep or avatar died. """
        
        name = event.name
        if name in self.creeps: # a creep died
            self.remove_creep(name)
        
        elif name in self.avs: # another avatar died
            av = self.get_charactor(name)
            av.die()
        
            if name == self.myname: # if my local avatar died
                self.acceptinput = False # stop accepting player inputs
                
        else: # name not found
            log.warn('Received death of ' + name
                          + ', but model does not know that name.')
        
        
    def remove_creep(self, name):
        """ Remove a creep. """
        
        try:
            self.creeps[name].rmv()
            del self.creeps[name]
        except KeyError:
            log.warning('Creep %s may have already been removed' % name) 
           

    ###########  gameadmin  ##############
    
    
    def on_gameadmin(self, event):
        """ If game stops, notify the view/widgets.
        Creeps are killed automatically on the server side.
        """
        
        pname, cmd = event.pname, event.cmd
        ev = MGameAdminEvt(pname, cmd)
        self._em.post(ev)
        
        log.info(event.pname + ' ' + event.cmd + ' the game')
        
        
    ##################  join, left  #####################################
    
    def on_playerjoin(self, event):
        """ When a new player arrives, add him to the connected players. """
        
        self.add_player(event.pname, event.pinfo)
        
        
    def add_player(self, pname, pinfo):
        """ add a new player to the list of connected players.
        pinfo contains a dic made by the server-side SAvatar object. 
        """
        
        coords, facing = pinfo['coords'], pinfo['facing']
        atk, hp = pinfo['atk'], pinfo['hp']
        move_cd = pinfo['move_cd_txt'][0] # dont care about move_txt when spawning avs
        cell = self.world.get_cell(coords)

        # whether that Player is the local client or a remote client
        islocal = hasattr(self, 'myname') and pname == self.myname 
        
        newplayer = Avatar(pname, cell, facing, atk, hp, move_cd, islocal, self._em)       
        self.avs[pname] = newplayer
        
        # notify the view 
        ev = MdAddPlayerEvt(pname)
        self._em.post(ev)
        
    
    def on_creepjoin(self, event):
        """ Create a creep. """
        
        cname, cinfo = event.cname, event.cinfo
        self.add_creep(cname, cinfo)
        
            
    def add_creep(self, cname, creepinfo):
        """ Add a new creep to the existing creeps.
        Info is a dic made on the server side by SCreep. """
        
        cell, facing = self.world.get_cell(creepinfo['coords']), creepinfo['facing']
        atk, hp = creepinfo['atk'], creepinfo['hp']
        
        creep = Creep(self._em, cname, cell, facing, atk, hp)       
        self.creeps[cname] = creep

        
            
    def on_playerleft(self, event):
        """ remove a player """
        
        pname = event.pname
        try:
            self.avs[pname].rmv()
            #don't forget to clean the player data from the dict
            del self.avs[pname]
            # notify the view
            ev = MPlayerLeftEvt(pname)
            self._em.post(ev)
        except KeyError:
            log.warning('Player ' + pname + ' had already been removed') 
        

 
    ##################  move  ######################## 

    def on_localavmove(self, event):
        """ Unless dead, when the user pressed up, down, right, or left,
        move his avatar.
        """
        if self.acceptinput:
            mychar = self.avs[self.myname]
            mychar.move_relative(event.direction, event.strafing)

  
    def on_remotemove(self, event):
        """ Move the avatar of the player which cname is pname. """
        
        name = event.name
        coords, facing = event.coords, event.facing
        
        if name != self.myname: # client is in charge of making its local av move
            char = self.get_charactor(name)
            destcell = self.world.get_cell(coords)
            char.move_absolute(destcell, facing)


    #############################  movespeed  ###########################
    
    def on_movespeedchange(self, event):
        """ A player changed his moving speed (run vs walk). 
        Only care if it's local player.
        """
        name = event.name 
        move_cd, move_txt = event.move_cd, event.move_txt
        av = self.avs[name]
        av.update_movespeed(move_cd, move_txt)
        
        
            
    ################## namechange ###################
    
    def on_namechange(self, event):
        """ update players' names when they change it """
        
        oldname, newname = event.oldname, event.newname
         
        if newname in self.avs:
            log.warning('%s changed name to %s, which was already in use'
                             % (oldname, newname))
        
        if self.myname == oldname: # I changed name
            self.myname = newname
            # notify the widget in charge of holding my cname
            log.info('Changed name to %s' % newname)
            ev = MMyNameChangedEvent(oldname, newname)
            self._em.post(ev)
        else: # someone else changed name
            ev = MNameChangedEvt(oldname, newname)
            self._em.post(ev)
            
        av = self.avs[oldname]
        av.changename(newname)
        self.avs[newname] = av
        del self.avs[oldname] #only del the mapping, not the player itself


    def on_namechangefail(self, event):
        """ When the player asked to change name but it was denied,
        notify the view. """
        
        ev = MNameChangeFailEvt(event.failname, event.reason)
        self._em.post(ev)
        
       
            
    ##############  resurrect  #############   
    
    def on_resurrect(self, event):
        """ An avatar (maybe myself) was resurrected. """
        
        name, info = event.name, event.info
        coords, facing = info['coords'], info['facing']
        hp, atk = info['hp'], info['atk']
        move_cd, move_txt = info['move_cd_txt']
        
        cell = self.world.get_cell(coords)
        
        # rez the char (update the view if local avatar)
        char = self.get_charactor(name)
        char.resurrect(cell, facing, hp, atk, move_cd, move_txt)
        
        # restart accepting input
        if name == self.myname:
            self.acceptinput = True

 
            