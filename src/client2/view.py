from client2.config import config_get_screenres
from client2.events_client import ModelBuiltMapEvent, ClientTickEvent, QuitEvent, \
    SendChatEvent, CharactorRemoveEvent, OtherCharactorPlaceEvent, \
    LocalCharactorPlaceEvent, LocalCharactorMoveEvent, RemoteCharactorMoveEvent, \
    ClNameChangeEvent, ClGreetEvent
from client2.widgets import ButtonWidget, InputFieldWidget, ChatLogWidget, \
    TextLabelWidget
from pygame.sprite import RenderUpdates, Sprite
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
    
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        pygame.init() #calling init() multiple times does not mess anything
        self.win_size = config_get_screenres()[0]
        # make a square window screen
        self.window = pygame.display.set_mode((self.win_size, self.win_size))
        pygame.display.set_caption('CC')
        
        # blit the loading screen: a black screen
        self.background = pygame.Surface(self.window.get_size())
        self.background.fill((0, 0, 0)) #black
        self.window.blit(self.background, (0, 0))
     
        
        # -- add quit button  at bottom-right 
        rect = pygame.Rect((self.win_size * 5 / 6, self.win_size * 11 / 12),
                           (self.win_size / 6 - 1, self.win_size / 12 - 1)) 
        quitEvent = QuitEvent()
        quit_btn = ButtonWidget(evManager, "Quit", rect=rect,
                             onUpClickEvent=quitEvent)
        # -- meh_btn at bottom right
        rect = pygame.Rect((self.win_size * 5 / 6, self.win_size * 5 / 6),
                            (self.win_size / 6 - 1, self.win_size / 12 - 1)) 
        msgEvent = SendChatEvent('meh...') #ask to send 'meh' to the server
        meh_btn = ButtonWidget(evManager, "Meh.", rect=rect,
                                   onUpClickEvent=msgEvent)
        
        
        # -- name label at bottom-left of the screen
        rect = pygame.Rect((0, self.win_size - 20),
                            (self.win_size / 8 - 1, 19)) 
        evt_txt_dict = {ClNameChangeEvent: 'newname', ClGreetEvent: 'newname'}
        namebox = TextLabelWidget(evManager, '', events_attrs=evt_txt_dict, rect=rect)
                
        # -- chat box input at bottom-left of the screen
        rect = pygame.Rect((self.win_size / 8, self.win_size - 20),
                            (self.win_size * 5 / 6 - self.win_size / 8 - 1, 19)) 
        chatbox = InputFieldWidget(evManager, rect=rect)


        # -- chat window display, just above the chat input field
        numlines = int(self.win_size / 200) 
        # rough estimate: for 400px, 2 lines of chat don't take too much room,
        # and for 600px, 3 lines are still OK
        rect = pygame.Rect((0, self.win_size * 5 / 6),
                           (self.win_size * 5 / 6 - 1, self.win_size / 6 - 20 - 1)) 
        chatwindow = ChatLogWidget(evManager, numlines=numlines, rect=rect)
        
        pygame.display.flip()

        self.charactor_sprites = RenderUpdatesDict()
        self.gui_sprites = RenderUpdates()   
        self.gui_sprites.add(quit_btn)
        self.gui_sprites.add(meh_btn)
        self.gui_sprites.add(chatbox)
        self.gui_sprites.add(namebox)
        self.gui_sprites.add(chatwindow)

    
    
    ###################### map and charactor ###############################
    
    
    def show_map(self, worldmap):
        """ Build the bg from the map cells, and blit it.
        The pixel width and height of map cells comes from 
        the window's dimensions and the map's visibility radius.
        """
        
        self.cellsprs = dict() # maps model.Cell to view.CellSprite
        
        # determine width and height of cell spr from map visibility 
        self.visib_rad = worldmap.visibility_radius
        self.visib_diam = 2 * self.visib_rad + 1
        self.cspr_size = int(self.win_size / self.visib_diam)
        
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
        """ display a charactor on the screen given his cell coords """
        
        cell_shift_left = cleft - self.bg_shift_left
        cell_shift_top = ctop - self.bg_shift_top
        
        if abs(cell_shift_left) <= self.visib_rad\
        and abs(cell_shift_top) <= self.visib_rad:
            # charactor got out of screen
            pass
         
        # determine the screen position of the char's spr
        charleft = (self.visib_diam / 2 + cell_shift_left) * self.cspr_size
        chartop = (self.visib_diam / 2 + cell_shift_top) * self.cspr_size
        charspr.rect.center = (charleft, chartop)

    
    
    
    def add_remote_charactor(self, charactor):
        """ Make a sprite and center the sprite 
        based on the cell location of the charactor.
        """
        sprdims = (self.cspr_size, self.cspr_size)
        charspr = CharactorSprite(charactor, sprdims, self.charactor_sprites)
        cleft, ctop = charactor.cell.coords
        self.display_charactor(charspr, cleft, ctop)


    def add_local_charactor(self, charactor):
        """ Center the map on the charactor's cell,
        build a charactor sprite in that cell, 
        and reblit background, charactor sprites, and GUI.
        """
        sprdims = (self.cspr_size, self.cspr_size)
        charspr = CharactorSprite(charactor, sprdims, self.charactor_sprites)
        cleft, ctop = charactor.cell.coords
        self.center_screen_on_coords(cleft, ctop)
        self.display_charactor(charspr, cleft, ctop)
        

    def remove_remote_charactor(self, charactor):
        """ """
        char_spr = self.charactor_sprites.get_spr(charactor)
        char_spr.kill() # remove from all sprite groups
        del char_spr
    
    
    def move_local_charactor(self, charactor):
        """ move my charactor: scroll the background """
        cleft, ctop = charactor.cell.coords
        self.center_screen_on_coords(cleft, ctop)
        # redisplay the other charactors
        for charspr in self.charactor_sprites:
            cleft, ctop = charspr.charactor.cell.coords
            self.display_charactor(charspr, cleft, ctop)
        

    def move_remote_charactor(self, charactor):
        """ move the spr of other clients' charactors """
        charspr = self.charactor_sprites.get_spr(charactor)
        cleft, ctop = charactor.cell.coords
        self.display_charactor(charspr, cleft, ctop) 
        
        
    #####################################################################
    

    def render_dirty_sprites(self):    
        # clear the window from all the sprites, replacing them with the bg
        self.charactor_sprites.clear(self.window, self.background)
        self.gui_sprites.clear(self.window, self.background)
        
        # update all the sprites - calls update() on each sprite of the groups
        self.charactor_sprites.update()
        self.gui_sprites.update()
        
        # collect the display areas that have changed
        dirty_rects_chars = self.charactor_sprites.draw(self.window)
        dirty_rects_gui = self.gui_sprites.draw(self.window)
        
        # and redisplay those areas only
        dirty_rects = dirty_rects_chars + dirty_rects_gui
        pygame.display.update(dirty_rects)



    def notify(self, event):
        """ Display the map when it has been built by the model.
        At clock ticks, draw what needs to be drawn.
        When the game is loaded, display it. 
        """
        
        if isinstance(event, ClientTickEvent):
            self.render_dirty_sprites()

        elif isinstance(event, ModelBuiltMapEvent):
            # called only once at the beginning, when model.map has been built 
            self.show_map(event.worldmap)
            
        elif isinstance(event, OtherCharactorPlaceEvent):
            self.add_remote_charactor(event.charactor)

        elif isinstance(event, LocalCharactorPlaceEvent):
            self.add_local_charactor(event.charactor)
            
        elif isinstance(event, CharactorRemoveEvent):
            charactor = event.charactor
            self.remove_remote_charactor(charactor)

            
        elif isinstance(event, LocalCharactorMoveEvent):
            self.move_local_charactor(event.charactor)
            #coords = event.coords
        elif isinstance(event, RemoteCharactorMoveEvent):
            self.move_remote_charactor(event.charactor)
            #coords = event.coords




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



            
            
