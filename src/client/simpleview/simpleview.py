from client.abstractview import AbstractView
from client.simpleview.avatar import AvatarSprite
from client.simpleview.hudbtn import HudBtn
from client.simpleview.renderer import SimpleRenderer
from client.simpleview.viewcontroller import SimpleViewCtrler
from weakref import WeakValueDictionary
import pygame.sprite

class SimpleView(AbstractView):
    """ A simple presentation layer using 2d rendering with sprites.
    Contains sprites to be rendered. Those sprites are also added 
    triggers to MainController behavior by the viewcontroller. """
    
    def __init__(self, chatlog, world, mainctrler):
        self.fps = 60 #render 60 times per sec
        # TODO: this self.fps should be taken into account in self.render()
        # TODO: self.fps should also be fetched from a simpleview config file

        self.hudsprites = pygame.sprite.Group() 
        self.worldsprites = pygame.sprite.Group()
        self.avatarsprites = WeakValueDictionary() 
        
        # TODO: hudsprs and worldsprs should be dictionaries, not Groups 
        self.rdrr = SimpleRenderer(self.worldsprites,
                                   self.avatarsprites,
                                   self.hudsprites,
                                   chatlog,
                                   world)
        self.ctrlr = SimpleViewCtrler(self.worldsprites,
                                      self.avatarsprites,
                                      self.hudsprites,
                                      mainctrler)

        # build the HUD - needs to be done AFTER Renderer()'s display.setmode()
        self.btn1 = HudBtn('star.png', (-1, -1), (0, 0), self.hudsprites)
        self.avatar = AvatarSprite('square.png', (-1, -1), (0, 0), self.worldsprites)
        self.rdrr.build_hud()
        self.rdrr.build_world()
        self.ctrlr.wire_hub()



    def render(self, frame_delay):
        self.rdrr.render(frame_delay)

    def process_click_event(self, pos):
        self.ctrlr.process_click_event(pos)
