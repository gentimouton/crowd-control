from client.config import config_get_screenheight, config_get_screenwidth
import operator

class World():
    def __init__(self):
        self.mypos = None
        #TODO: boundaries is a temporary stub
        self.boundaries = (config_get_screenwidth() - 10,
                           config_get_screenheight() - 10) 
        self.other_players = dict()
        
        
    def update_state(self):
        pass
    
    def set_myname(self, newname):
        self.myname = newname
        # TODO: myname = duplicate data from chatlog; should be at only one place
        
    # movement
    
    def get_mypos(self):
        return self.mypos
    def set_mypos(self, pos):
        self.mypos = pos
        
    def is_walkable(self, pos):
        ''' True if pos fits in world boundaries '''        
        return (pos[0] > 0 
                and pos[1] > 0 
                and pos[0] < self.boundaries[0] 
                and pos[1] < self.boundaries[1])

    def newpos_if_in_world(self, delta):
        ''' False if the movement is not allowed, new position otherwise '''
        newpos = tuple(map(operator.add, self.mypos, delta))
        if self.is_walkable(newpos):
            self.mypos = newpos
            return newpos
        else:
            return False
        
    def i_go_up(self):
        return self.newpos_if_in_world((0, -1))
    def i_go_down(self):
        return self.newpos_if_in_world((0, 1))

    def set_start_pos(self,pos):
        self.mypos = pos 
        
    # other players
    
    def init_playerlist(self, onlineppl):
        self.other_players = onlineppl
        
    def someone_moved(self, author, dest):
        ''' only keep track of other players' movement; 
        my movement are taken care of locally when i push keys or click '''
        if author != self.myname:
            print(author, 'moved to', dest)
            self.other_players[author] = dest
            
    def get_other_players(self):
        return self.other_players
    
