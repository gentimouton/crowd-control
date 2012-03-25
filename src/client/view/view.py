from client.config import config_get_screensize, \
    config_get_loadingscreen_bgcolor, config_get_fontsize, config_get_walkable_color, \
    config_get_nonwalkable_color, config_get_entrance_color, config_get_lair_color, \
    config_get_avdefault_bgcolor, config_get_myav_bgcolor, config_get_creep_bgcolor, \
    config_get_txtlabel_bgcolor, config_get_chatlog_txtcolor, \
    config_get_txtlabel_txtcolor
from client.events_client import CharactorRemoveEvent, OtherAvatarPlaceEvent, \
    LocalAvatarPlaceEvent, SendMoveEvt, RemoteCharactorMoveEvent, CreepPlaceEvent, \
    MMyNameChangedEvent, CharactorRcvDmgEvt, RemoteCharactorAtkEvt, LocalAvRezEvt, \
    CharactorDeathEvt, RemoteCharactorRezEvt, SendAtkEvt, MGreetNameEvt, \
    MBuiltMapEvt
from client.view.charspr import CharactorSprite, ScrollingTextSprite
from client.view.indexablespr import IndexedLayeredUpdates
from client.view.widgets import InputFieldWidget, ChatLogWidget, TextLabelWidget, \
    PlayerListWidget
from common.events import TickEvent
from pygame.sprite import LayeredUpdates, Sprite, LayeredDirty
import logging
import pygame


log = logging.getLogger('client')
        

class MasterView:
    """ links to presentations of game world and HUD """

    def __init__(self, evManager):
        """ when view starts, register callbacks to events and build the GUI """
         
        self._em = evManager
        self.register_callbacks()
        
        # init pygame's screen
        pygame.init() #calling init() multiple times does not mess anything

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
        
        # make the window screen
        w, h = config_get_screensize()
        if w < h:
            log.warn('Screen width (%d px) should be larger'
                     + ' than screen height (%d px).' % (w, h))
        self.gui_offset = max(w - h, 0) # left screen space = GUI
        
        self.win_size = w, h
        resolution = w, h
        self.window = pygame.display.set_mode(resolution)
        pygame.display.set_caption('CC')
        
        # blit the loading screen: a black screen
        bg = pygame.Surface(resolution) 
        bgcolor = config_get_loadingscreen_bgcolor()
        bg.fill(bgcolor)
        bg = bg.convert()
        self.screen_bg = bg 
        self.window.blit(bg, (0, 0))
        
        # reveal
        pygame.display.flip()

        self.charactor_sprites = IndexedLayeredUpdates() # all in game charactors 
        self.active_charactor_sprites = IndexedLayeredUpdates() # chars currently visible on screen
        self.dmg_sprites = LayeredUpdates() # dmg to display on screen


    def build_gui(self):
        """ Add widgets to the screen.
        Widgets on the left need only be reblitted when they get dirty.
        Widgets that overlay the world screen need to be reblitted every frame.
        """

        # start adding widgets
        leftgui = LayeredDirty() # only reblit when dirty=1
        overlaygui = LayeredUpdates() # reblit every frame
        w, h = self.win_size
        line_h = config_get_fontsize()
        gui_w = self.gui_offset
        
        # -- name label at top-left of the screen
        rec = pygame.Rect(0, 0, gui_w - 1, line_h - 1)
        evt_txt_dict = {MMyNameChangedEvent: 'newname', MGreetNameEvt:'newname'}
        txtcol = config_get_txtlabel_txtcolor()
        bgcol = config_get_txtlabel_bgcolor()
        namebox = TextLabelWidget(self._em, '', events_attrs=evt_txt_dict,
                                  rect=rec, txtcolor=txtcol, bgcolor=bgcol)
        leftgui.add(namebox)
        
        # -- list of connected players, until middle of the screen
        rec = pygame.Rect(0, line_h, gui_w - 1, line_h - 1)
        txt = 'Connected players:'
        txtcol = config_get_txtlabel_txtcolor()
        bgcol = config_get_txtlabel_bgcolor()
        whosonlinetitle = TextLabelWidget(self._em, txt, rect=rec,
                                          txtcolor=txtcol, bgcolor=bgcol)
        leftgui.add(whosonlinetitle)
        rec = pygame.Rect(0, 2 * line_h, gui_w - 1, h / 2 - 2 * line_h - 1)
        numlines = int(rec.height / line_h)
        txtcol = config_get_chatlog_txtcolor()
        bgcol = None #config_get_chatlog_bgcolor()
        whosonlinebox = PlayerListWidget(self._em, numlines, rect=rec,
                                         txtcolor=txtcol, bgcolor=bgcol)
        leftgui.add(whosonlinebox)
        
        # -- chat window overlay at bottom of the world screen
        chat_height = h / 4  
        numlines = int(chat_height / line_h)
        if numlines > 0: # text input field
            rec = pygame.Rect(gui_w + 1, h - line_h, w - gui_w - 1, line_h - 1) 
            chatbox = InputFieldWidget(self._em, rect=rec)
            overlaygui.add(chatbox)
        if numlines > 1: # text display line
            rec = pygame.Rect(gui_w + 1, h * 3 / 4,
                              w - gui_w - 1, h / 4 - line_h - 1)            
            txtcol = config_get_chatlog_txtcolor()
            # no bg color to disply on top of world screen
            chatwindow = ChatLogWidget(self._em, numlines=numlines, rect=rec,
                                       txtcolor=txtcol)
            overlaygui.add(chatwindow)
        
        self.left_gui_sprites = leftgui
        self.overlay_gui_sprites = overlaygui
        
        
        
        
    #################  gfx utils  ###############
    
    def center_screen_on_coords(self, cleft, ctop):
        """ Get the subsurface of interest to pick from the whole world surface
        and blit it on the window screen.
        """
        
        self.bg_shift_left = cleft
        self.bg_shift_top = ctop
        # compute the rect of the world bg to subsurface from
        celsize = self.cspr_size
        subsurf_left = cleft * celsize
        subsurf_top = ctop * celsize
        v_diam = self.visib_diam
        subsurf_dims = (v_diam * celsize, v_diam * celsize) 
        visible_area = pygame.Rect((subsurf_left, subsurf_top), subsurf_dims)
        # make bg from that area of interest
        # subsurface() should not raise any error when moving on the world borders
        # since the screen is squared and the world padded with an extra visib_diam
        visible_bg = self.world_bg.subsurface(visible_area)
        visible_bg = visible_bg.convert()
        self.screen_bg.blit(visible_bg, (self.gui_offset, 0))
        self.window.blit(visible_bg, (self.gui_offset, 0))
        pygame.display.flip() 
        

    def game_to_screen_coords(self, gcoords):
        """ gcoords are cell coords, from the game model.
        Return the screen coords if in range, or None if outside of range. 
        """
        
        cleft, ctop = gcoords
        # cell distance from my av cell 
        cell_shift_left = cleft - self.bg_shift_left
        cell_shift_top = ctop - self.bg_shift_top
        
        v_radius = self.visib_rad
        if abs(cell_shift_left) <= v_radius\
            and abs(cell_shift_top) <= v_radius:
            # in range
            v_diam = self.visib_diam
            celsize = self.cspr_size
            gui_offset = self.gui_offset
            screenleft = (v_diam / 2 + cell_shift_left) * celsize + gui_offset
            screentop = (v_diam / 2 + cell_shift_top) * celsize
            return screenleft, screentop
        
        else: # out of range
            return None, None
        
        
    def display_char_if_inrange(self, char):
        """ display (or not) a charactor if it's in range.
        This function is called when the charactor model changes.
        """
        
        gamecoords = char.cell.coords 
        screenleft, screentop = self.game_to_screen_coords(gamecoords)
        charspr = self.charactor_sprites.get_spr(char)
        
        if screenleft and screentop: # in screen range
            # ask the charactor's sprite to position itself
            self.active_charactor_sprites.add(charspr) # activate the spr
            charspr.update_img(screenleft, screentop)
            
        else: # charactor got out of screen: desactivate the spr
            self.active_charactor_sprites.remove(charspr)
            
            
    def display_dmg_if_inrange(self, char, dmg):
        """ start displaying the dmg a charactor received """
        
        gcoords = char.cell.coords
        screenleft, screentop = self.game_to_screen_coords(gcoords) # center of the char spr

        if screenleft and screentop:
            celsize = self.cspr_size
            centerpos = screenleft, screentop - celsize / 4
            scroll_height = celsize / 2 # how high should the text scroll until erased
            
            txt = str(dmg)
            duration = 500 # in millis # TODO: move to config
            ScrollingTextSprite(txt, duration, centerpos, scroll_height, self.dmg_sprites)
        
      
        
        
        
        
    ###################### RENDERING OF SPRITES and BG ######################
    

    def on_tick(self, event):
        """ Render all the dirty sprites.
        The order is important: blit charactors first, then damage, then GUI.
        """
        
        chars = self.active_charactor_sprites
        dmgs = self.dmg_sprites
        leftgui = self.left_gui_sprites
        ovgui = self.overlay_gui_sprites
        
        win, bg = self.window, self.screen_bg
        
        # clear the window from all the sprites, replacing them with the bg
        chars.clear(win, bg)
        dmgs.clear(win, bg)
        leftgui.clear(win, bg)
        ovgui.clear(win, bg)
        
        # update all the sprites - calls update() on each sprite of the groups
        duration = event.duration # how long passed since last tick
        chars.update(duration)
        dmgs.update(duration)
        leftgui.update(duration)
        ovgui.update(duration)
        
        # collect the display areas that need to be redrawn
        dirty_chars = chars.draw(win) # ie, all char sprites
        dirty_dmg = dmgs.draw(win) # all dmg being displayed
        dirty_lgui = leftgui.draw(win) # but only the left widgets that are dirty
        dirty_ovgui = ovgui.draw(win) # and all overlay widgets

        # and redisplay those areas only
        dirty_rects = dirty_chars + dirty_dmg + dirty_lgui + dirty_ovgui
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
        layer = 1 # which layer to put that spr into
        CharactorSprite(creep, sprdims, bgcolor, layer, self.charactor_sprites)
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
        r = worldmap.visibility_radius
        self.visib_rad = r
        diam = 2 * r + 1
        self.visib_diam = diam
        height = self.win_size[1]
        celsize = int(height / diam)
        self.cspr_size = celsize
        
        # Build world screen_bg to be scrolled when the avatar moves
        # so that world_bg can be scrolled. 
        # Padding of visib_diam so that the screen bg can subsurface(world_bg)
        v_rad = self.visib_rad
        w_w, w_h = worldmap.width, worldmap.height
        w_surf_w = celsize * (w_w + 2 * v_rad)
        w_surf_h = celsize * (w_h + 2 * v_rad)
        worldbg = pygame.Surface((w_surf_w, w_surf_h))
        worldbg.fill(config_get_nonwalkable_color())
        
        for i in range(w_w):
            for j in range(w_h):
                # don't forget the visib_rad of padding
                cspr_left = (v_rad + i) * celsize
                cspr_top = (v_rad + j) * celsize
                cellrect = pygame.Rect(cspr_left, cspr_top, celsize, celsize)                
                cell = worldmap.get_cell(i, j)
                cellspr = CellSprite(cell, cellrect)
                self.cellsprs[cell] = cellspr
                # blit the cell to world bg
                worldbg.blit(cellspr.image, cellspr.rect)
        
        worldbg = worldbg.convert()
        self.world_bg = worldbg
        # Center screen screen_bg on entrance cell, and blit
        eleft, etop = worldmap.entrance_coords
        self.center_screen_on_coords(eleft, etop)
        
    
         
    ############### join #############

    def on_localavplace(self, event):
        """ Center the map on the avatar's cell,
        build a charactor sprite in that cell, 
        and reblit screen_bg, charactor sprites, and GUI.
        """
    
        avatar = event.avatar
        sprdims = (self.cspr_size, self.cspr_size)
        bgcolor = config_get_myav_bgcolor()
        layer = 3 # local avatar sprite is over other avs, and over creeps 
        CharactorSprite(avatar, sprdims, bgcolor, layer, self.charactor_sprites)
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
        layer = 2 # other av sprites are over creeps but below the local av spr 
        CharactorSprite(av, sprdims, bgcolor, layer, self.charactor_sprites)
        self.display_char_if_inrange(av)


    ################# move ################
    
    def on_localavmove(self, event):
        """ move my avatar: scroll the screen_bg """
    
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
    Used to draw the map screen_bg.
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
        



############################# TESTS ##################################


if __name__ == "__main__":
    import pygame
    from pygame.sprite import Sprite
    from pygame.surface import Surface
    from pygame.locals import KEYDOWN, RLEACCEL, SRCALPHA
    from pygame.font import Font
        
    pygame.init()
    screen = pygame.display.set_mode((300, 300))

    bg = Surface((200, 200))
    bg.fill((255, 0, 0))    
    bg = bg.convert()
    screen.blit(bg, (50, 50))

    font = Font(None, 25)
    txt = 'qwertyuiop'
    txtimg = font.render(txt, 1, (255, 255, 255)) # antialiasing w/o bg => alpha 
    
    b = Surface((100, 100), SRCALPHA)
    b.fill((111, 111, 111, 128))
    b.blit(txtimg, (10, 10))
    b = b.convert_alpha()
    screen.blit(b, (25, 25))
    
    # what's below has better perf, but bad output when antialias + transparency 
    c = Surface((100, 100))
    colkey = (255, 0, 255)
    c.set_colorkey(colkey, RLEACCEL)
    c.fill(colkey) # make the surface bg invisible
    
    c2 = Surface((100, 100))
    c2.fill((111, 111, 111))
    c2.set_alpha(128, RLEACCEL) # semi-transparent gray bg
    #c.blit(c2, (0, 0))
    c2 = c2.convert()
    txtimg2 = txtimg.convert(c) # sucks if txtimg is antialiased
    c.blit(txtimg2, (10, 10))
    c = c.convert() 
    screen.blit(c2, (125, 25))
    screen.blit(c, (125, 25))
    pygame.display.update()
    
    while pygame.event.poll().type != KEYDOWN:
        pygame.time.delay(10)
