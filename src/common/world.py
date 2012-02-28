from common.constants import DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, \
    DIRECTION_RIGHT
import logging
import os
import random



class World():
    

    def __init__(self, evManager, log):
        """ ... """

        self.log = log
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
          
        
        ev = buildevent(self)
        self._em.post(ev)
        
        
    def buildpath(self):
        """ Starting from entrance (d=0),
        a cell's distance to the entrance is d+1
        if the shortest distance of its neighbor cells to the entrance is d.
        """
        def recursive_dist_fill(cell, d):
            try:
                assert self.iswalkable(cell.coords)
            except AssertionError:
                self.log.warning('Cell ' + str(cell) + ' should not be reachable')
                return
            
            if cell.entrance_dist is not None and cell.entrance_dist <= d:
                return
            else:
                cell.entrance_dist = d
                [recursive_dist_fill(c, d + 1) for c in cell.get_neighbors()]            
        
        recursive_dist_fill(self.get_entrance(), 0)
        
    
    
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
                if left < 0 or top < 0:
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
        self._occupants = dict() # ids of things currently on this cell



    def __str__(self):
        return '<Cell %s %s>' % (self.coords, id(self))
    
    
    def get_neighbors(self):
        """ Return the neighbor cells. """
        directions = [DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT]
        adjs = []
        for  d in directions:
            c = self.get_adjacent_cell(d)
            if c:
                adjs.append(c)
        return adjs
        # could be done in 1 line, but would require 2 calls to each non-None cell:
        # return [c for c in self.get_adjacent_cell(d) if self.get_adjacent_cell(d)]
        
        
         
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
        """ Return a cell that is on the path towards the map entrance. """
        neighbors = self.get_neighbors()
        random.shuffle(neighbors) #shuffle for randomness
        if not neighbors:#no adjacent cell is walkable
            return None 
        else: # return the neighbor closest to entrance
            return min(neighbors, key=lambda c: c.entrance_dist)
            
            
    def set_entrance(self, value):
        self.isentrance = value
    def set_lair(self, value):
        self.islair = value
        

    #### OCCUPANTS
    
    def add_occ(self, occ):
        """ add occupant """
        self._occupants[occ] = 1
        
    def rm_occ(self, occ):
        """ remove occupant """
        try:
            del self._occupants[occ]
        except KeyError: # TODO: should log.warning instead!
            self.log.error('Failed to remove ' + str(occ) 
                           + ' from cell ' + str(self.coords))
    
    def occ_chngname(self, oldname, newname):
        """ An occupant changed name/id. """
        del self._occupants[oldname]
        self._occupants[newname] = 1 
        
    def get_occ(self):
        """ TODO: return the weakest cell occupant """
        if self._occupants:
            return list(self._occupants.keys())[0] # ugly!
        else:
            return None
