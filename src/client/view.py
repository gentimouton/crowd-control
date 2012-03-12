from client.config import config_get_screenres, config_get_loadingscreen_bgcolor, \
    config_get_fontsize, config_get_walkable_color, config_get_nonwalkable_color, \
    config_get_entrance_color, config_get_lair_color, config_get_avdefault_bgcolor, \
    config_get_myav_bgcolor, config_get_creep_bgcolor
from client.events_client import ModelBuiltMapEvent, QuitEvent, SendChatEvt, \
    CharactorRemoveEvent, OtherAvatarPlaceEvent, LocalAvatarPlaceEvent, SendMoveEvt, \
    RemoteCharactorMoveEvent, NwRcvGreetEvt, CreepPlaceEvent, MyNameChangedEvent, \
    CharactorRcvDmgEvt, CharactorAtksEvt, LocalAvRezEvt
from client.widgets import ButtonWidget, InputFieldWidget, ChatLogWidget, \
    TextLabelWidget, PlayerListWidget
from common.events import TickEvent
from pygame.sprite import RenderUpdates, Sprite
import logging
import pygame


class IndexableSprite(Sprite):
    """ Sprite that can be fetched from a RenderUpdatesDict"""
    def __init__(self, key=None):
        Sprite.__init__(self)
        self.key = key
    
class RenderUpdatesDict(RenderUpdates):
    """ Group class that extends RenderUpdates to enable associating a spr 
    to a user name """
     
    def __init__(self, *sprites):
        RenderUpdates.__init__(self, *sprites)
        self.__dict = dict() 

    def add_internal(self, spr):
        """ add sprite to the group,
        and index it if it's an IndexableSprite """
        RenderUpdates.add_internal(self, spr)
        if isinstance(spr, IndexableSprite):
            self.__dict[spr.key] = spr
            
    def get_spr(self, key):
        return self.__dict[key]

        
###########################################################################

class MasterView:
    """ links to presentations of game world and HUD """
    
    log = logging.getLogger('client')

    def __init__(self, evManager):
        # -- set the callbacks
        self._em = evManager
        
        # local = my avatar
        self._em.reg_cb(LocalAvatarPlaceEvent, self.on_localavplace)
        self._em.reg_cb(SendMoveEvt, self.on_localavmove)
        self._em.reg_cb(LocalAvRezEvt, self.on_localavrez)
        
        # remote = creeps + other avatars
        # different creation, but same movement and removal
        self._em.reg_cb(OtherAvatarPlaceEvent, self.on_remoteavplace)
        self._em.reg_cb(CreepPlaceEvent, self.add_creep)
        self._em.reg_cb(RemoteCharactorMoveEvent, self.on_remotecharmove)
        self._em.reg_cb(CharactorRemoveEvent, self.on_remotecharremove)
        self._em.reg_cb(CharactorRcvDmgEvt, self.on_charrcvdmg)
        self._em.reg_cb(CharactorAtksEvt, self.on_charatks)
        # misc
        self._em.reg_cb(ModelBuiltMapEvent, self.show_map)
        self._em.reg_cb(TickEvent, self.render_dirty_sprites)

        # -- init pygame's screen
        pygame.init() #calling init() multiple times does not mess anything
        self.win_size = self.win_w, self.win_h = config_get_screenres()
        if self.win_w != 4 * self.win_h / 3:
            self.log.warn('Resolution ' + str(self.win_size) + ' is not 4x3.')

        # make the window screen
        self.window = pygame.display.set_mode(self.win_size)
        pygame.display.set_caption('CC')
        
        # blit the loading screen: a black screen
        self.background = pygame.Surface(self.window.get_size()) 
        self.background.fill(config_get_loadingscreen_bgcolor()) 
        self.window.blit(self.background, (0, 0))
     
        
        # -- add quit button  at bottom-right 
        rect = pygame.Rect((self.win_w * 7 / 8, self.win_h * 11 / 12),
                           (self.win_w / 8 - 1, self.win_h / 12 - 1)) 
        quitEvent = QuitEvent()
        quit_btn = ButtonWidget(evManager, "Quit", rect=rect,
                                onUpClickEvent=quitEvent)
        # -- meh_btn at bottom right
        rect = pygame.Rect((self.win_w * 6 / 8, self.win_h * 11 / 12),
                            (self.win_w / 8 - 1, self.win_h / 12 - 1)) 
        msgEvent = SendChatEvt('meh...') #ask to send 'meh' to the server
        meh_btn = ButtonWidget(evManager, "Meh.", rect=rect,
                                   onUpClickEvent=msgEvent)
        
        line_h = config_get_fontsize()
        
        # -- name label at top-right of the screen
        rect = pygame.Rect((self.win_w * 3 / 4, 0),
                           (self.win_w / 4 - 1, line_h - 1))
        evt_txt_dict = {MyNameChangedEvent: 'newname', NwRcvGreetEvt: 'newname'}
        namebox = TextLabelWidget(evManager, '', events_attrs=evt_txt_dict, rect=rect)
                
        # -- list of connected players at right of the screen
        rect = pygame.Rect((self.win_w * 3 / 4, line_h),
                           (self.win_w / 4 - 1, line_h - 1))
        whosonlinetitle = TextLabelWidget(evManager, 'Connected players:', rect=rect)
        
        rect = pygame.Rect((self.win_w * 3 / 4, 2 * line_h),
                            (self.win_w / 4 - 1, self.win_h / 2 - 2 * line_h - 1))
        numlines = int(rect.height / line_h) 
        whosonlinebox = PlayerListWidget(evManager, numlines, rect=rect)
        
        
        # -- chat box input at bottom-right of the screen
        rect = pygame.Rect((self.win_w * 3 / 4, self.win_h * 11 / 12 - line_h),
                           (self.win_w / 4 - 1, line_h - 1)) 
        chatbox = InputFieldWidget(evManager, rect=rect)


        # -- chat window display, just above the chat input field
        rect = pygame.Rect((self.win_w * 3 / 4, self.win_h * 6 / 12),
                           (self.win_w / 4 - 1, self.win_h * 5 / 12 - line_h - 1))
        numlines = int(rect.height / line_h) 
        chatwindow = ChatLogWidget(evManager, numlines=numlines, rect=rect)
        
        pygame.display.flip()

        self.charactor_sprites = RenderUpdatesDict() # all in game charactors 
        self.active_charactor_sprites = RenderUpdatesDict() # chars currently visible on screen
        
        self.gui_sprites = RenderUpdates()   
        self.gui_sprites.add(quit_btn)
        self.gui_sprites.add(meh_btn)
        self.gui_sprites.add(chatbox)
        self.gui_sprites.add(namebox)
        self.gui_sprites.add(whosonlinetitle)
        self.gui_sprites.add(whosonlinebox)
        self.gui_sprites.add(chatwindow)

    
    
    ###################### map and avatar ###############################
    
    
    def show_map(self, event):
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
        


    def display_charactor(self, charspr, cleft, ctop):
        """ display (or not) a avatar on the screen given his cell coords """
        
        cell_shift_left = cleft - self.bg_shift_left
        cell_shift_top = ctop - self.bg_shift_top
        
        if abs(cell_shift_left) <= self.visib_rad\
        and abs(cell_shift_top) <= self.visib_rad:
            self.active_charactor_sprites.add(charspr)
            # char is near: display his spr on the screen
            charleft = (self.visib_diam / 2 + cell_shift_left) * self.cspr_size
            chartop = (self.visib_diam / 2 + cell_shift_top) * self.cspr_size
            charspr.rect.center = (charleft, chartop)
            
        else: # avatar got out of screen: remove his spr from the groups
            self.active_charactor_sprites.remove(charspr)


    ################ local avatar ###########################################
    
    def on_localavplace(self, event):
        """ Center the map on the avatar's cell,
        build a charactor sprite in that cell, 
        and reblit background, charactor sprites, and GUI.
        """
        avatar = event.avatar
        sprdims = (self.cspr_size, self.cspr_size)
        bgcolor = config_get_myav_bgcolor()
        charspr = CharactorSprite(avatar, sprdims, bgcolor, self.charactor_sprites)
        cleft, ctop = avatar.cell.coords
        self.center_screen_on_coords(cleft, ctop) #must be done before display_char
        self.display_charactor(charspr, cleft, ctop)


    def on_localavmove(self, event):
        """ move my avatar: scroll the background """
        myav = event.avatar
        cleft, ctop = myav.cell.coords
        self.center_screen_on_coords(cleft, ctop)
        # redisplay the other charactors 
        for charspr in self.charactor_sprites:
            cleft, ctop = charspr.char.cell.coords
            self.display_charactor(charspr, cleft, ctop)
            
            
    def on_localavrez(self, event):
        """ rez my avatar: center screen where my av is """
        myav = event.avatar
        cleft, ctop = myav.cell.coords
        self.center_screen_on_coords(cleft, ctop)
        # redisplay the other charactors 
        for charspr in self.charactor_sprites:
            cleft, ctop = charspr.char.cell.coords
            self.display_charactor(charspr, cleft, ctop)
    
    

    ##################### REMOTE CHARACTORS #################################        

    def on_remoteavplace(self, event):
        """ Make a sprite and center the sprite 
        based on the cell location of the remote avatar.
        """
        avatar = event.avatar
        sprdims = (self.cspr_size, self.cspr_size)
        bgcolor = config_get_avdefault_bgcolor()
        charspr = CharactorSprite(avatar, sprdims, bgcolor, self.charactor_sprites)
        cleft, ctop = avatar.cell.coords
        self.display_charactor(charspr, cleft, ctop)


    def add_creep(self, event):
        """ Add creep spr on screen. """
        creep = event.creep
        sprdims = (self.cspr_size, self.cspr_size)
        bgcolor = config_get_creep_bgcolor()
        creepspr = CharactorSprite(creep, sprdims, bgcolor, self.charactor_sprites)
        # TODO: CreepSprite() instead of CharactorSprite()
        cleft, ctop = creep.cell.coords
        self.display_charactor(creepspr, cleft, ctop)
        
        
    def on_remotecharmove(self, event):
        """ Move the spr of creeps or other avatars. """
        char = event.charactor
        charspr = self.charactor_sprites.get_spr(char)
        cleft, ctop = char.cell.coords
        self.display_charactor(charspr, cleft, ctop) 
        

    def on_remotecharremove(self, event):
        """ A Charactor can be an avatar or a creep. """
        char_spr = self.charactor_sprites.get_spr(event.charactor)
        char_spr.kill() # remove from all sprite groups
        del char_spr
            


    ###################### ATTACKS ###########################
    
    def on_charrcvdmg(self, event):
        """ Display text with damage over charactor's sprite. """
        # TODO: FT display text with damage over charactor's sprite.
        defer = self.charactor_sprites.get_spr(event.defer)
        dmg = event.dmg
        
    
    def on_charatks(self, event):
        """ Display the charactor attacking. """
        # TODO: FT display the charactor attacking
        atker = self.charactor_sprites.get_spr(event.atker)
        
        
        
    ###################### RENDERING OF SPRITES and BG ######################
    

    def render_dirty_sprites(self, event):    
        # clear the window from all the sprites, replacing them with the bg
        self.active_charactor_sprites.clear(self.window, self.background)
        self.gui_sprites.clear(self.window, self.background)
        
        # update all the sprites - calls update() on each sprite of the groups
        self.active_charactor_sprites.update()
        self.gui_sprites.update()
        
        # collect the display areas that have changed
        dirty_rects_chars = self.active_charactor_sprites.draw(self.window)
        dirty_rects_gui = self.gui_sprites.draw(self.window)
        
        # and redisplay those areas only
        dirty_rects = dirty_rects_chars + dirty_rects_gui
        pygame.display.update(dirty_rects)





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
        


###########################################################################



class CharactorSprite(IndexableSprite):
    """ The representation of a character """
    
    def __init__(self, char, sprdims, bgcolor, groups=None):
        self.key = char # must be set before adding the spr to group(s)
        Sprite.__init__(self, groups)
        
        charactorSurf = pygame.Surface(sprdims)
        charactorSurf = charactorSurf.convert_alpha()
        charactorSurf.fill((0, 0, 0, 0)) #make transparent
        # draw a circle as big as dims
        w, h = sprdims
        ctr_coords = int(w / 2), int(h / 2)
        radius = int(min(w / 2, h / 2)) #don't overflow the given sprdims
        pygame.draw.circle(charactorSurf, bgcolor, ctr_coords, radius)
        self.image = charactorSurf
        self.rect = charactorSurf.get_rect()

        self.char = char
        self.dest = None

    
    def update(self):
        """ movement could be smoother and last for longer than 1 frame """
        if self.dest:
            self.rect.center = self.dest
            self.dest = None
