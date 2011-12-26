

class SimpleViewCtrler():
    
    def __init__(self, rdr):
        """ create world and HUD sprites """
        self.renderer = rdr
        
    def process_click_event(self, pos):
        print("click: " + str(pos))
        for btn in self.renderer.all_sprites:
            if btn.isinside(pos):
                btn.clicked()
        
        
