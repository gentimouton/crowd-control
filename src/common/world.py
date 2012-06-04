from collections import deque
from common.constants import DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, \
    DIRECTION_RIGHT, DIRECTIONS
import logging
import os
import random

class World():
    

    def __init__(self, evManager, log):
        """ ... """

        self.log = log
        self._em = evManager

        
    def __str__(self):
        return '%s, %d x %d' % (self.mapname, self.width, self.height) \
                + '\n' + self.worldrepr
    
    
    def build_world(self, mapname, notifevt=None, callbacks=[]):
        """ build the world from a map name, and notify by event
        or by callbacks when done """
        
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
            self.width = len(lines[0].strip().split(','))
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
                cell = Cell(self.log, self, coords, walkable, self._em)
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
          
        if notifevt: # client-side
            ev = notifevt(self)
            self._em.post(ev)
        elif callbacks: # server-side
            for cb in callbacks:
                cb()
                  

        
    
    def buildpath(self):
        """ A cell is a vertex in the world graph. 
        Edges are the links cells have with each other, using cell.get_neighbors. 
        Using a breadth-first visit of the world graph 
        makes path building linear with the number of cells.
        """
        
        fifo = deque()
        # add entrance
        entrance = self.get_entrance()
        entrance.entrance_dist = 0
        fifo.append(entrance) # any cell added has its distance set
        
        while fifo: # until empty 
            cell = fifo.popleft()
            dist = cell.entrance_dist
            for c in cell.get_neighbors():
                if c.entrance_dist == None:
                    c.entrance_dist = dist + 1
                    fifo.append(c)
                
        
    
    def get_lair(self):
        return self.get_cell(self.lair_coords)
    def get_entrance(self):
        return self.get_cell(self.entrance_coords)
    
    
    
    def get_cell(self, lefttop, top=None):
        """ Get a cell from its coords.
        Accepts get_cell(left,top) or get_cell(coords).
        Returns None if out of map.        
        """ 
        try:
            if top is not None: #top is specified ('is not None' because top can be 0)
                left = lefttop
                if left < 0 or top < 0: # outside of the map
                    return None
                else:
                    return self.__cellgrid[top][left]
            else: #top was not specified
                left, top = lefttop
                if left < 0 or top < 0:# outside of the map
                    return None
                else:
                    return self.__cellgrid[top][left]
        except IndexError: #outside of the map
            return None
        
        
    def iswalkable(self, coords):
        """ return whether a cell is walkable or not """
        return self.get_cell(coords).iswalkable
        
##########################################################################

        
class Cell():
    
    def __init__(self, log, world, pos, walkable, evManager):
        self.log = log
        self._em = evManager
        #self._em.register_listener( self )
        self.left, self.top = self.coords = pos
        self.world = world
        
        self.isentrance = self.islair = False
        self.entrance_dist = None # server-side: to be filled in world.buildpath
        
        self.iswalkable = walkable
        self._avs = dict() # ids of things currently on this cell
        self._creeps = dict()


    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return '<Cell %s, %d occs>' % (self.coords, len(self._avs) + len(self._creeps))

    
    def get_neighbors(self, withdirs=False):
        """ Return a a list of the cells neighboring a cell. """
        adjcells = {}
        for direc in DIRECTIONS:
            cell = self.get_adjacent_cell(direc)
            if cell:
                adjcells[direc] = cell
        if not withdirs:
            return list(adjcells.values())
        else:
            return adjcells
        
        
         
    def get_adjacent_cell(self, direction):
        """ Return the adjacent cell in that direction.
        Return None if not walkable or out of grid.
        """
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
        
        
        
    def get_nextcell_inpath(self):
        """ Return the direction to the cell on the path towards the entrance,
        and the cell itself.
        Return a tuple (direction, cell)
        """
        nbs = self.get_neighbors(withdirs=True)
        # transform dict into list of tuples
        neighbors = [(direc, cell) for direc, cell in nbs.items()]
        random.shuffle(neighbors) #shuffle for randomness
        if not neighbors:#no adjacent cell is walkable
            return None 
        else: # return the cell closest to entrance + the direction to that cell
            return min(neighbors, key=lambda tup: tup[1].entrance_dist)

            
    def set_entrance(self, value):
        self.isentrance = value
    def set_lair(self, value):
        self.islair = value
        

    #### avatars
    
    def add_av(self, av):
        """ Add avatar. """
        self._avs[av] = 1

    def rm_av(self, av):
        """ remove Avatar from cell. """
        try:
            del self._avs[av]
        except KeyError: 
            pass

    def get_avs(self):
        """ Return all the Avs in the cell. """
        return list(self._avs.keys())



    #### creeps
    
    def add_creep(self, c):
        """ Add creep to cell. """
        self._creeps[c] = 1
        
    def rm_creep(self, c):
        """ remove creep from cell. """
        try:
            del self._creeps[c]
        except KeyError: 
            self.log.warning('Failed to remove Creep %s from cell %s' 
                             % (c.name, self.coords))
            
    def get_creeps(self):
        """ Return all the Creeps in the cell. """
        return list(self._creeps.keys())
    
