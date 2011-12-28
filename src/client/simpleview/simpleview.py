from client.abstractview import AbstractView
from client.simpleview.renderer import SimpleRenderer
from client.simpleview.viewcontroller import SimpleViewCtrler

class SimpleView(AbstractView):
    """ A simple presentation layer using 2d rendering with sprites.
    Contains sprites to be rendered. Those sprites are also added 
    triggers to MainController behavior by the viewcontroller. """
    
    def __init__(self, chatlog):
        self.fps = 60 #render 60 times per sec
        self.rdrr = SimpleRenderer(chatlog)
        self.ctrlr = SimpleViewCtrler(self.rdrr)

    def render(self):
        self.rdrr.render()

    def process_click_event(self, pos):
        self.ctrlr.process_click_event(pos)
        