

class SimpleViewCtrler():
    
    def __init__(self, rdr):
        """ create world and HUD sprites """
        self.renderer = rdr
        #set the onClicked behavior of btn1
        rdr.hudsprs.sprites()[0].onclicked = lambda: print("lambda")
        
                
    def process_click_event(self, pos):
        """ find the HUD or game-world UI element the user clicked on
        and trigger the MainController logic tied to the button """
        # TODO: there should be a smarter logic otherwise this is going to 
        #lag with 1k clickable monsters on the screen: first,
        # if pos falls under a zone usually reserved for the HUD
        # then only parse the HUD sprites,
        # otherwise, cut the screen in a dozen vertical segments 
        # (x<10, x in 10-20, etc) and only make a collision-search 
        # within this segment
        # this should limit the search to at most the 30-40 elements in the
        # segment that the click pos falls into
        print(pos)
        for btn in self.renderer.hudsprs:
            if btn.isinside(pos):
                btn.onclicked()
                return
        for btn in self.renderer.worldsprs:
            if btn.isinside(pos):
                btn.onclicked()
                return
        
        
