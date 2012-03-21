from client.config import config_get_screenres, config_get_loadingscreen_bgcolor, \
    config_get_fontsize, config_get_walkable_color, config_get_nonwalkable_color, \
    config_get_entrance_color, config_get_lair_color, config_get_avdefault_bgcolor, \
    config_get_myav_bgcolor, config_get_creep_bgcolor
from client.events_client import QuitEvent, SubmitChat, CharactorRemoveEvent, \
    OtherAvatarPlaceEvent, LocalAvatarPlaceEvent, SendMoveEvt, \
    RemoteCharactorMoveEvent, CreepPlaceEvent, MMyNameChangedEvent, \
    CharactorRcvDmgEvt, RemoteCharactorAtkEvt, LocalAvRezEvt, CharactorDeathEvt, \
    RemoteCharactorRezEvt, SendAtkEvt, MGreetNameEvt, MBuiltMapEvt
from client.view.charspr import CharactorSprite, ScrollingTextSprite
from client.view.indexablespr import RenderUpdatesDict
from client.view.widgets import ButtonWidget, InputFieldWidget, ChatLogWidget, \
    TextLabelWidget, PlayerListWidget
from common.events import TickEvent
from pygame.sprite import RenderUpdates, Sprite
import logging
import pygame


log = logging.getLogger('client')
        

class MasterView:
    """ links to presentations of game world and HUD """

    def __init__(self, evManager):
        """ when view starts, register callbacks to events and build the GUI """
         
        self._em = evManager
        self.register_callbacks()
        
        self.build_screen()
        self.build_gui()
        
        
    def register_callbacks(self):
        """ """
        
        #tick
        self._em.reg_cb(TickEvent, self.on_tick)

        # attack
        self._em.reg_cb(SendAtkEvt, self.on_localavatk)
        self._em.reg_cb(RemoteCharactorAtkEvt, self.on_charatks)
        self._em.reg_cb(CharactorRcvDmgEvt, self.on_charrcvdmg)
        # creepjoin
        self._em.reg_cb(CreepPlaceEvent, self.add_creep)        
        # death/left
        self._em.reg_cb(CharactorDeathEvt, self.on_chardeath)
        self._em.reg_cb(CharactorRemoveEvent, self.on_charremove)
        # greet
        self._em.reg_cb(MBuiltMapEvt, self.on_mapbuilt)
        #join
        self._em.reg_cb(LocalAvatarPlaceEvent, self.on_localavplace)
        self._em.reg_cb(OtherAvatarPlaceEvent, self.on_remoteavplace)
        #move
        self._em.reg_cb(SendMoveEvt, self.on_localavmove)
        self._em.reg_cb(RemoteCharactorMoveEvent, self.on_remotecharmove)
        #resu
        self._em.reg_cb(LocalAvRezEvt, self.on_localavrez)        
        self._em.reg_cb(RemoteCharactorRezEvt, self.on_resurrect)
        

    def build_screen(self):
        """ init the pygame window, and build the world screen """
        
        # init pygame's screen
        pygame.init() #calling init() multiple times does not mess anything
        self.win_size = self.win_w, self.win_h = config_get_screenres()
        if self.win_w != 4 * self.win_h / 3:
            log.warn('Resolution ' + str(self.win_size) + ' is not 4x3.')

        # make the window screen
        self.window = pygame.display.set_mode(self.win_size)
        pygame.display.set_caption('CC')
        
        # blit the loading screen: a black screen
        self.background = pygame.Surface(self.window.get_size()) 
        bgcolor = config_get_loadingscreen_bgcolor()
        self.background.fill(bgcolor) 
        self.window.blit(self.background, (0, 0))
        
        # reveal
        pygame.display.flip()

        self.charactor_sprites = RenderUpdatesDict() # all in game charactors 
        self.active_charactor_sprites = RenderUpdatesDict() # chars currently visible on screen
        self.dmg_sprites = RenderUpdates() # dmg to display on screen


    def build_gui(self):
        """ Add widgets to the screen """


        # start adding widgets
        self.gui_sprites = RenderUpdates()   

        # -- add quit button  at bottom-right 
        rect = pygame.Rect((self.win_w * 7 / 8, self.win_h * 11 / 12),
                           (self.win_w / 8 - 1, self.win_h / 12 - 1)) 
        quitEvent = QuitEvent()
        quit_btn = ButtonWidget(self._em, "Quit", rect=rect,
                                onUpClickEvent=quitEvent)
        self.gui_sprites.add(quit_btn)
        
        
        # -- meh_btn at bottom right
        rect = pygame.Rect((self.win_w * 6 / 8, self.win_h * 11 / 12),
                            (self.win_w / 8 - 1, self.win_h / 12 - 1)) 
        msgEvent = SubmitChat('meh...') #ask to send 'meh' to the server
        meh_btn = ButtonWidget(self._em, "Meh.", rect=rect,
                                   onUpClickEvent=msgEvent)
        self.gui_sprites.add(meh_btn)
        
        
        line_h = config_get_fontsize()
        
        
        # -- name label at top-right of the screen
        rect = pygame.Rect((self.win_w * 3 / 4, 0),
                           (self.win_w / 4 - 1, line_h - 1))
        evt_txt_dict = {MMyNameChangedEvent: 'newname', MGreetNameEvt:'newname'}
        namebox = TextLabelWidget(self._em, '', events_attrs=evt_txt_dict, rect=rect)
        self.gui_sprites.add(namebox)
                
                
        # -- list of connected players at right of the screen
        rect = pygame.Rect((self.win_w * 3 / 4, line_h),
                           (self.win_w / 4 - 1, line_h - 1))
        whosonlinetitle = TextLabelWidget(self._em, 'Connected players:', rect=rect)
        self.gui_sprites.add(whosonlinetitle)
        
        rect = pygame.Rect((self.win_w * 3 / 4, 2 * line_h),
                            (self.win_w / 4 - 1, self.win_h / 2 - 2 * line_h - 1))
        numlines = int(rect.height / line_h) 
        whosonlinebox = PlayerListWidget(self._em, numlines, rect=rect)
        self.gui_sprites.add(whosonlinebox)
        
        
        # -- chat box input at bottom-right of the screen
        rect = pygame.Rect((self.win_w * 3 / 4, self.win_h * 11 / 12 - line_h),
                           (self.win_w / 4 - 1, line_h - 1)) 
        chatbox = InputFieldWidget(self._em, rect=rect)
        self.gui_sprites.add(chatbox)
        

        # -- chat window display, just above the chat input field
        rect = pygame.Rect((self.win_w * 3 / 4, self.win_h * 6 / 12),
                           (self.win_w / 4 - 1, self.win_h * 5 / 12 - line_h - 1))
        numlines = int(rect.height / line_h) 
        chatwindow = ChatLogWidget(self._em, numlines=numlines, rect=rect)
        self.gui_sprites.add(chatwindow)
        
        
        
        
    #################  gfx utils  ###############
    
    def center_screen_on_coords(self, cleft, ctop):
        """ Get the subsurface of interest to pick from the whole world surface
        and blit it on the window screen.
        """
        
        self.bg_shift_left = cleft
        self.bg_shift_top = ctop
        
        subsurf_left = cleft * self.cspr_size
        subsurf_top = ctop * self.cspr_size
        subsurf_dims = (self.visib_diam * self.cspr_size,
                        self.visib_diam * self.cspr_size) 
        visible_area = pygame.Rect((subsurf_left, subsurf_top), subsurf_dims)
        # make bg from that area of interest
        # subsurface() should not raise any error when moving on the world borders
        # since the screen is squared and the world padded with an extra visib_diam
        self.background = self.world_bg.subsurface(visible_area)
        self.window.blit(self.background, (0, 0))
        pygame.display.flip() 
        

    def game_to_screen_coords(self, gcoords):
        """ gcoords are cell coords, from the game model.
        Return the screen coords if in range, or None if outside of range. 
        """
        
        cleft, ctop = gcoords
        # cell distance from my av cell 
        cell_shift_left = cleft - self.bg_shift_left
        cell_shift_top = ctop - self.bg_shift_top
            
        if abs(cell_shift_left) <= self.visib_rad\
            and abs(cell_shift_top) <= self.visib_rad:
            # in range
            screenleft = (self.visib_diam / 2 + cell_shift_left) * self.cspr_size
            screentop = (self.visib_diam / 2 + cell_shift_top) * self.cspr_size
            return screenleft, screentop
        
        else: # out of range
            return None, None
        
        
    def display_char_if_inrange(self, char):
        """ display (or not) a charactor if it's in range.
        This function is called when the charactor model changes.
        """
        
        gamecoords = char.cell.coords 
        screenleft, screentop = self.game_to_screen_coords(gamecoords)
        
        if screenleft and screentop: # in screen range
            # ask the charactor's sprite to position itself
            charspr = self.charactor_sprites.get_spr(char)
            self.active_charactor_sprites.add(charspr) # activate the spr
            charspr.update_img(screenleft, screentop)
            
        else: # charactor got out of screen: desactivate the spr
            self.active_charactor_sprites.remove(charspr)
            
            
    def display_dmg_if_inrange(self, char, dmg):
        """ start displaying the dmg a charactor received """
        
        gcoords = char.cell.coords
        screenleft, screentop = self.game_to_screen_coords(gcoords) # center of the char spr

        if screenleft and screentop:
            centerpos = screenleft, screentop - self.cspr_size / 4
            scroll_height = self.cspr_size / 2 # how high should the text scroll until erased
            
            txt = str(dmg)
            duration = 500 # in millis
            ScrollingTextSprite(txt, duration, centerpos, scroll_height, self.dmg_sprites)
        
      
        
        
        
        
        
        
    ###################### RENDERING OF SPRITES and BG ######################
    

    def on_tick(self, event):    
        """ Render all the dirty sprites """
        
        # clear the window from all the sprites, replacing them with the bg
        self.active_charactor_sprites.clear(self.window, self.background)
        self.dmg_sprites.clear(self.window, self.background)
        self.gui_sprites.clear(self.window, self.background)
        
        # update all the sprites - calls update() on each sprite of the groups
        duration = event.duration # how long passed since last tick
        self.active_charactor_sprites.update(duration)
        self.dmg_sprites.update(duration)
        self.gui_sprites.update(duration)
        
        # collect the display areas that have changed
        dirty_rects_chars = self.active_charactor_sprites.draw(self.window)
        dirty_rects_dmg = self.dmg_sprites.draw(self.window)
        dirty_rects_gui = self.gui_sprites.draw(self.window)
        
        # and redisplay those areas only
        dirty_rects = dirty_rects_chars + dirty_rects_dmg + dirty_rects_gui 
        pygame.display.update(dirty_rects)
        
        
        


    ########### attack ###############
    
                
    def on_localavatk(self, event):
        """ Local avatar attacked: only display dmg, but 
        dont update defender's HP bar: the HP update comes from a server msg.
        """
        
        defer, dmg = event.defer, event.dmg
        self.display_dmg_if_inrange(defer, dmg)        
        
            
    def on_charatks(self, event):
        """ Display the charactor attacking. 
        The dmg are displayed by a char RECEIVING dmg. """
    
        log.info('%s attacked' % event.atker.name) 
        # TODO: FT display the charactor attacking instead of log.info

    
    def on_charrcvdmg(self, event):
        """ Display text with damage over charactor's sprite. """
        
        defer, dmg = event.defer, event.dmg
        fromremotechar = event.fromremotechar
        
        self.display_char_if_inrange(defer)
        if fromremotechar: # if atker was local, the dmg was already rendered
            self.display_dmg_if_inrange(defer, dmg)


    ####### creepjoin #########


    def add_creep(self, event):
        """ Add creep spr on screen. """
    
        creep = event.creep
        sprdims = (self.cspr_size, self.cspr_size)
        bgcolor = config_get_creep_bgcolor()
        CharactorSprite(creep, sprdims, bgcolor, self.charactor_sprites)
        # TODO: FT CreepSprite() instead of CharactorSprite()
        self.display_char_if_inrange(creep)


    ########## death ############
    
    def on_chardeath(self, event):
        """ A charactor died: hide it.
        Show it again when/if the charactor resurrects.
        """
                
        char = event.charactor
        self.display_char_if_inrange(char)
        log.info('%s died' % char.name)


    def on_charremove(self, event):
        """ A Charactor can be an avatar or a creep.
        Can be triggered because of local or remote events.
        """

        char = event.charactor
        charspr = self.charactor_sprites.get_spr(char)
        charspr.kill() # remove from all sprite groups
        del charspr
            

    ######################  greet  ###############################
    
    def on_mapbuilt(self, event):
        """ Build the bg from the map cells, and blit it.
        The pixel width and height of map cells comes from 
        the window's dimensions and the map's visibility radius.
        Called only once at the beginning, when model.map has been built.
        """
        
        worldmap = event.worldmap
        
        self.cellsprs = dict() # maps model.Cell to view.CellSprite
        
        # determine width and height of cell spr from map visibility 
        self.visib_rad = worldmap.visibility_radius
        self.visib_diam = 2 * self.visib_rad + 1
        self.cspr_size = int(self.win_h / self.visib_diam)
        
        # Build world background to be scrolled when the avatar moves
        # so that world_bg can be scrolled. 
        # Padding of visib_diam so that the screen bg can subsurface(world_bg)
        world_surf_w = self.cspr_size * (worldmap.width + 2 * self.visib_rad)
        world_surf_h = self.cspr_size * (worldmap.height + 2 * self.visib_rad)
        self.world_bg = pygame.Surface((world_surf_w, world_surf_h))
        self.world_bg.fill(config_get_nonwalkable_color())
        
        for i in range(worldmap.width):
            for j in range(worldmap.height):
                # don't forget the visib_rad of padding
                cspr_left = (self.visib_rad + i) * self.cspr_size
                cspr_top = (self.visib_rad + j) * self.cspr_size
                cspr_dims = (self.cspr_size, self.cspr_size)
                cellrect = pygame.Rect((cspr_left, cspr_top), cspr_dims)
                
                cell = worldmap.get_cell(i, j)
                cellspr = CellSprite(cell, cellrect)
                self.cellsprs[cell] = cellspr
                
                self.world_bg.blit(cellspr.image, cellspr.rect)
        
        # Center screen background on entrance cell, and blit
        eleft, etop = worldmap.entrance_coords
        self.center_screen_on_coords(eleft, etop)
        
    
         
    ############### join #############

    def on_localavplace(self, event):
        """ Center the map on the avatar's cell,
        build a charactor sprite in that cell, 
        and reblit background, charactor sprites, and GUI.
        """
    
        avatar = event.avatar
        sprdims = (self.cspr_size, self.cspr_size)
        bgcolor = config_get_myav_bgcolor()
        CharactorSprite(avatar, sprdims, bgcolor, self.charactor_sprites)
        cleft, ctop = avatar.cell.coords
        self.center_screen_on_coords(cleft, ctop) #must be done before display_char
        self.display_char_if_inrange(avatar)
        
    def on_remoteavplace(self, event):
        """ Make a sprite and center the sprite 
        based on the cell location of the remote avatar.
        """
        
        av = event.avatar
        sprdims = (self.cspr_size, self.cspr_size)
        bgcolor = config_get_avdefault_bgcolor()
        CharactorSprite(av, sprdims, bgcolor, self.charactor_sprites)
        self.display_char_if_inrange(av)


    ################# move ################
    
    def on_localavmove(self, event):
        """ move my avatar: scroll the background """
    
        myav = event.avatar
        cleft, ctop = myav.cell.coords
        self.center_screen_on_coords(cleft, ctop)
        # redisplay the charactors that are in range
        for charspr in self.charactor_sprites:
            char = charspr.char
            if char.cell: # char is still alive
                self.display_char_if_inrange(char)


    def on_remotecharmove(self, event):
        """ Move the spr of creeps or other avatars. """

        char = event.charactor
        self.display_char_if_inrange(char) 
        
        
    #################  resurrect  ############
    
    def on_localavrez(self, event):
        """ Resurrect my avatar: display my av, and center screen on my av. 
        Note: it can happen that, within the same frame, 
        the avatar resurrects and is killed again 
        (when the server sent rez and death msg in the same frame).
        Don't display the avatar if it is dead again/still dead. 
        """
        
        # center screen on my av and redisplay all chars if my av resurrected
        myav = event.avatar
        if myav.cell: # av has not been killed again in the same frame
            cleft, ctop = myav.cell.coords
            self.center_screen_on_coords(cleft, ctop) #must be done before display_char

            # redisplay all the charactors that are alive (includes me) 
            for charspr in self.charactor_sprites:
                char = charspr.char
                if char.cell: # char is still alive
                    self.display_char_if_inrange(char)
    

    def on_resurrect(self, event):
        """ Resurrect another charactor (creep or avatar) """
        
        char = event.charactor
        self.display_char_if_inrange(char)
        log.info('%s resurrected' % event.charactor.name)
        



###########################################################################

    
    
class CellSprite(Sprite):
    """ The representation of a map cell. 
    Used to draw the map background.
     """    
    
    def __init__(self, cell, rect, group=()):
        Sprite.__init__(self, group)
        
        self.dims = self.width, self.height = rect.width, rect.height

        # fill self.image filled with the appropriate color
        self.image = pygame.Surface(self.dims)
        if cell.isentrance:
            color = config_get_entrance_color()
        elif cell.islair:
            color = config_get_lair_color()
        elif cell.iswalkable:
            color = config_get_walkable_color()
        else: # non-walkable
            color = config_get_nonwalkable_color()
        self.image.fill(color) 
        self.rect = rect
        
        self.cell = cell
        

