from common.constants import DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, \
    DIRECTION_RIGHT
import os


class World():
    

    def __init__(self, evManager):
        """ ... """

        self.evManager = evManager
        #self.evManager.register_listener(self)
        
    def __str__(self):
        return '<World %s>' % (id(self))
    
    
    def build_world(self, mapname, buildevent):    
        f = open(os.path.join(os.pardir, 'maps', mapname))
        lines = f.readlines() #might be optimized: for line in open("file.txt"):
        self.cellgrid = [] #contains game board

        # sanity checks on map width and height
        self.width = len(lines)
        if self.width == 0:
            print('Warning: map', mapname, 'has no lines.')
        else:
            self.height = len(lines[0].strip().split(','))
            if self.height == 0:
                print('Warning: the first line of map', mapname, 'has no cells.')
        
        # build the cell matrix
        for j in range(self.width): 
            tmprow = []
            line = lines[j].strip().split(',')
            
            for i in range(len(line)):
                coords = j, i
                cellvalue = line[i]
                if cellvalue == 'E':#entrance is walkable
                    self.entrance_coords = coords # TODO: should be a list of coords
                    walkable = 1
                elif cellvalue == 'L':
                    self.lair_coords = coords # TODO: should be a list of coords
                    walkable = 1
                else:
                    walkable = int(cellvalue) # 0 or 1
                cell = Cell(self, coords, walkable, self.evManager)
                tmprow.append(cell)
            
            self.cellgrid.append(tmprow) 
            #such that cellgrid[i][j] = i-th cell from top, j-th from left
        
        # set the entrances and lair cells
        e_coords = self.entrance_coords
        if e_coords:
            cell = self.get_cell(e_coords)
            cell.set_entrance(True)
        l_coords = self.lair_coords
        if l_coords:
            cell = self.get_cell(l_coords)
            cell.set_lair(True)
        
        ev = buildevent(self)
        self.evManager.post(ev)
        
        
        
    def get_cell(self, tl, left=None):
        """ cell from coords;
        accepts get_cell(top,left) or get_cell(coords)
        """ 
        try:
            if left is not None: #left can be 0, and 0 != None
                if -1 in [tl, left]: # outside of the map
                    return None
                else:
                    return self.cellgrid[tl][left]
            else: #left was specified
                if -1 in tl:
                    return None
                else:
                    top, left = tl
                    return self.cellgrid[top][left]
        except IndexError: #outside of the map
            return None
        
        
        
##########################################################################

        
class Cell():
    
    def __init__(self, world, coords, walkable, evManager):
        self.evManager = evManager
        #self.evManager.register_listener( self )
        self.top, self.left = self.coords = coords
        self.world = world
        self.iswalkable = walkable


    def __str__(self):
        return '<Cell %s %s>' % (self.coords, id(self))
    
    
    def get_adjacent_cell(self, direction):
        if direction == DIRECTION_UP: # TODO: use 'is' instead of '=='?
            dest_coords = self.top - 1, self.left
        elif direction == DIRECTION_DOWN:
            dest_coords = self.top + 1, self.left
        elif direction == DIRECTION_LEFT:
            dest_coords = self.top, self.left - 1
        elif direction == DIRECTION_RIGHT:
            dest_coords = self.top, self.left + 1
        
        dest_cell = self.world.get_cell(dest_coords) 
        if dest_cell and dest_cell.iswalkable:
            return dest_cell
        else: #non walkable or out of grid
            return None
            
    def set_entrance(self, value):
        self.isentrance = value
    def set_lair(self, value):
        self.islair = value
        

    