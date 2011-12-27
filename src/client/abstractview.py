
class AbstractView():
    """A view implementation should supply:
    - the frequency of rendering (max 60 fps): the fps attr (default:30)
    - the rendering to do each frame: the render() method
    - a mapping from a click position to a MainController method (see 
    MainController API)
    """
    
    def __init__(self):
        self.fps = 30 #you should override this attr in your view
    
    def render(self):
        raise NotImplementedError("render() should be implemented")
        # see http://docs.python.org/library/exceptions.html#exceptions.NotImplementedError

    def process_click_event(self, pos):
        raise NotImplementedError("process_click_event() should be implemented")
