

class SimpleViewCtrler():
    
    def __init__(self, worldsprites, hudsprites, mc):
        """ assign behavior to world and HUD sprites """        
        # world and hud sprites point to the sprites from simpleview
        self.worldsprites = worldsprites
        self.hudsprites = hudsprites        
        self.mc = mc # main controller


    def wire_hub(self):
        #set the onClicked behavior of btn1
        self.hudsprites.sprites()[0].onclicked = self.mc.greenboxclick

        
    def process_click_event(self, pos):
        """ find the HUD or game-world UI element the user clicked on
        and trigger the MainController logic tied to the button """
        # TODO: there should be a smarter logic otherwise this is going to 
        #lag with 1k clickable monsters on the screen: 
        # if pos falls under a zone usually reserved for the HUD
        # then only parse the HUD sprites,
        # otherwise, cut the screen in a dozen vertical segments 
        # (x<10, x in 10-20, etc) and only make a collision-search 
        # within this segment
        # this should limit the search to at most the 30-40 elements in the
        # segment that the click pos falls into
        for btn in self.hudsprites:
            if btn.isinside(pos):
                btn.onclicked()
                return
        for btn in self.worldsprites:
            if btn.isinside(pos):
                btn.onclicked()
                return
        
        
