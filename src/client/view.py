from client.config import config_get_screenres
from client.events_client import ModelBuiltMapEvent, QuitEvent, SendChatEvent, \
    CharactorRemoveEvent, OtherCharactorPlaceEvent, LocalCharactorPlaceEvent, \
    LocalCharactorMoveEvent, RemoteCharactorMoveEvent, ClNameChangeEvent, \
    ClGreetEvent
from client.widgets import ButtonWidget, InputFieldWidget, ChatLogWidget, \
    TextLabelWidget
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
        self._em.reg_cb(RemoteCharactorMoveEvent, self.move_remote_charactor)
        self._em.reg_cb(LocalCharactorMoveEvent, self.move_local_charactor)
        self._em.reg_cb(CharactorRemoveEvent, self.remove_remote_charactor)
        self._em.reg_cb(LocalCharactorPlaceEvent, self.add_local_charactor)
        self._em.reg_cb(OtherCharactorPlaceEvent, self.add_remote_charactor)
        self._em.reg_cb(ModelBuiltMapEvent, self.show_map)
        self._em.reg_cb(TickEvent, self.render_dirty_sprites)

        # -- init pygame's screen
        pygame.init() #calling init() multiple times does not mess anything
        self.win_size = self.win_w, self.win_h = config_get_screenres()
        if self.win_w != 4 * self.win_h / 3:
            self.log.warn('Resolution ' + str(self.win_size) + ' is not 4x3.')

        # make a square window screen
        self.window = pygame.display.set_mode(self.win_size)
        pygame.display.set_caption('CC')
        
        # blit the loading screen: a black screen
        self.background = pygame.Surface((self.win_h, self.win_h)) #or self.window.get_size()?
        self.background.fill((0, 0, 0)) #black
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
        msgEvent = SendChatEvent('meh...') #ask to send 'meh' to the server
        meh_btn = ButtonWidget(evManager, "Meh.", rect=rect,
                                   onUpClickEvent=msgEvent)
        
        
        # -- name label at top-right of the screen
        rect = pygame.Rect((self.win_w * 3 / 4, 0),
                            (self.win_w / 4 - 1, 19)) 
        evt_txt_dict = {ClNameChangeEvent: 'newname', ClGreetEvent: 'newname'}
        namebox = TextLabelWidget(evManager, '', events_attrs=evt_txt_dict, rect=rect)
                
        line_h = 20
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
        self.gui_sprites.add(chatwindow)

    
    
    ###################### map and charactor ###############################
    
    
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
        
        # Build world background to be scrolled when the charactor moves
        # so that world_bg can be scrolled 
        # padding of visib_diam so that the bg can subsurface(world_bg)
        world_surf_w = self.cspr_size * (worldmap.width + 2 * self.visib_rad)
        world_surf_h = self.cspr_size * (worldmap.height + 2 * self.visib_rad)
        self.world_bg = pygame.Surface((world_surf_w, world_surf_h))
        
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
        """ display (or not) a charactor on the screen given his cell coords """
        
        cell_shift_left = cleft - self.bg_shift_left
        cell_shift_top = ctop - self.bg_shift_top
        
        if abs(cell_shift_left) <= self.visib_rad\
        and abs(cell_shift_top) <= self.visib_rad:
            self.active_charactor_sprites.add(charspr)
            # char is near: display his spr on the screen
            charleft = (self.visib_diam / 2 + cell_shift_left) * self.cspr_size
            chartop = (self.visib_diam / 2 + cell_shift_top) * self.cspr_size
            charspr.rect.center = (charleft, chartop)
            
        else: # charactor got out of screen: remove his spr from the groups
            self.active_charactor_sprites.remove(charspr)
    
    
    
    def add_remote_charactor(self, event):
        """ Make a sprite and center the sprite 
        based on the cell location of the charactor.
        """
        charactor = event.charactor
        sprdims = (self.cspr_size, self.cspr_size)
        charspr = CharactorSprite(charactor, sprdims, self.charactor_sprites)
        cleft, ctop = charactor.cell.coords
        self.display_charactor(charspr, cleft, ctop)


    def add_local_charactor(self, event):
        """ Center the map on the charactor's cell,
        build a charactor sprite in that cell, 
        and reblit background, charactor sprites, and GUI.
        """
        charactor = event.charactor
        sprdims = (self.cspr_size, self.cspr_size)
        charspr = CharactorSprite(charactor, sprdims, self.charactor_sprites)
        cleft, ctop = charactor.cell.coords
        self.center_screen_on_coords(cleft, ctop) #must be done before display_char
        self.display_charactor(charspr, cleft, ctop)
        

    def remove_remote_charactor(self, event):
        """ """
        charactor = event.charactor
        char_spr = self.charactor_sprites.get_spr(charactor)
        char_spr.kill() # remove from all sprite groups
        del char_spr
    
    
    def move_local_charactor(self, event):
        """ move my mychar: scroll the background """
        mychar = event.charactor
        cleft, ctop = mychar.cell.coords
        self.center_screen_on_coords(cleft, ctop)
        # redisplay the other charactors 
        for charspr in self.charactor_sprites:
            cleft, ctop = charspr.charactor.cell.coords
            self.display_charactor(charspr, cleft, ctop)
        

    def move_remote_charactor(self, event):
        """ move the spr of other clients' charactors """
        charactor = event.charactor
        charspr = self.charactor_sprites.get_spr(charactor)
        cleft, ctop = charactor.cell.coords
        self.display_charactor(charspr, cleft, ctop) 
        
        
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
    
    # rgb cell colors
    walkable_cell_color = 139, 119, 101 
    nonwalkable_cell_color = 0, 0, 0 
    entrance_cell_color = 139, 0, 101 
    lair_cell_color = 139, 119, 0 
    
    
    def __init__(self, cell, rect, group=()):
        Sprite.__init__(self, group)
        
        self.dims = self.width, self.height = rect.width, rect.height

        # fill self.image filled with the appropriate color
        self.image = pygame.Surface(self.dims)
        if cell.isentrance:
            color = self.entrance_cell_color
        elif cell.islair:
            color = self.lair_cell_color
        elif cell.iswalkable:
            color = self.walkable_cell_color
        else: # non-walkable
            color = self.nonwalkable_cell_color
        self.image.fill(color) 
        self.rect = rect
        
        self.cell = cell
        


###########################################################################



class CharactorSprite(IndexableSprite):
    """ The representation of a character """
    
    def __init__(self, charactor, sprdims, groups=None):
        self.key = charactor # must be set before adding the spr to group(s)
        Sprite.__init__(self, groups)
        
        charactorSurf = pygame.Surface(sprdims)
        charactorSurf = charactorSurf.convert_alpha()
        charactorSurf.fill((0, 0, 0, 0)) #make transparent
        # draw a circle as big as dims
        w, h = sprdims
        ctr_coords = int(w / 2), int(h / 2)
        radius = int(min(w / 2, h / 2)) #don't overflow the given sprdims
        pygame.draw.circle(charactorSurf, (255, 140, 0), ctr_coords, radius)
        self.image = charactorSurf
        self.rect = charactorSurf.get_rect()

        self.charactor = charactor
        self.dest = None

    
    def update(self):
        """ movement could be smoother and last for longer than 1 frame """
        if self.dest:
            self.rect.center = self.dest
            self.dest = None



            
            
