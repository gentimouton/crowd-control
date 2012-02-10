from common.constants import DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, \
    DIRECTION_RIGHT
import logging
import os



class World():
    

    def __init__(self, evManager):
        """ ... """

        self._em = evManager
        #self._em.register_listener(self)
        
    def __str__(self):
        return '<World %s, %s x %s>' % (id(self), self.width, self.height) \
                + '\n' + self.worldrepr
    
    
    def build_world(self, mapname, buildevent):
        """ build the world from a map name, and notify when done """
        
        self.mapname = mapname
        
        try:    
            fname = os.path.join(os.pardir, 'maps', mapname)
            f = open(fname)
        except IOError:
            logging.critical('Map not found: ' + os.path.abspath(fname))
            
        lines = f.readlines() #might be optimized: for line in open("file.txt"):
        self.__cellgrid = [] #contains game board
        self.worldrepr = '' # string visually representing the world map
        
        # 1st line = diameter of the players' visible area
        self.visibility_radius = int(lines.pop(0))
        
        if self.visibility_radius <= 0:
            logging.error('Visibility radius should be greater than 0 in ' 
                          + os.path.abspath(fname))

        # sanity checks on map width and height
        self.height = len(lines)
        if self.height == 0:
            logging.error('Map ' + mapname + ' has no lines.')
        else:
            self.width = len(lines[1].strip().split(','))
            if self.width == 0:
                logging.error('The first row of map ' + mapname 
                              + ' has no cells.')
        
        # build the cell matrix
        for i in range(self.height): 
            tmprow = []
            line = lines[i].strip().split(',')
            self.worldrepr = self.worldrepr + lines[i]
            
            for j in range(len(line)):
                coords = j, i 
                # so that __cellgrid[i][j] = i-th cell from top, j-th from left
                cellvalue = line[j]
                if cellvalue == 'E':#entrance is walkable
                    self.entrance_coords = coords 
                    walkable = 1
                elif cellvalue == 'L':
                    self.lair_coords = coords
                    walkable = 1
                else:
                    walkable = int(cellvalue) # 0 or 1
                cell = Cell(self, coords, walkable, self._em)
                tmprow.append(cell)

            self.__cellgrid.append(tmprow)

        
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
        self._em.post(ev)
        
        
        
    def get_cell(self, lefttop, top=None):
        """ cell from coords;
        accepts get_cell(left,top) or get_cell(coords)
        """ 
        try:
            if top is not None: #top can be 0, and 0 != None
                if -1 in [lefttop, top]: # outside of the map
                    return None
                else:
                    return self.__cellgrid[top][lefttop]
            else: #top was specified
                if -1 in lefttop:
                    return None
                else:
                    l, t = lefttop
                    return self.__cellgrid[t][l]
        except IndexError: #outside of the map
            return None
        
        
        
##########################################################################

        
class Cell():
    
    def __init__(self, world, pos, walkable, evManager):
        self._em = evManager
        #self._em.register_listener( self )
        self.left, self.top = self.coords = pos
        self.world = world
        self.iswalkable = walkable
        self.isentrance = self.islair = False

    def __str__(self):
        return '<Cell %s %s>' % (self.coords, id(self))
    
    
    def get_adjacent_cell(self, direction):
        if direction == DIRECTION_UP:
            dest_coords = self.left, self.top - 1
        elif direction == DIRECTION_DOWN:
            dest_coords = self.left, self.top + 1 
        elif direction == DIRECTION_LEFT:
            dest_coords = self.left - 1, self.top 
        elif direction == DIRECTION_RIGHT:
            dest_coords = self.left + 1, self.top 
        
        dest_cell = self.world.get_cell(dest_coords) 
        if dest_cell and dest_cell.iswalkable:
            return dest_cell
        else: #non walkable or out of grid
            return None
            
    def set_entrance(self, value):
        self.isentrance = value
    def set_lair(self, value):
        self.islair = value
        

    
