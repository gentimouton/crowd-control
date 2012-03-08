

class SCharactor():
    """ Abstract class representing game charactors, 
    like player avatars or creeps. 
    """
    def __init__(self, name, cell, facing, hp, atk):
        self.name = name
        self.cell = cell
        self.cell.add_occ(self)
        self.facing = facing #direction the player is facing
        self.hp = hp
        self.atk = atk
        
    
    def __str__(self):
        return '%s at %s, hp=%d' % (self.name, self.cell.coords, self.hp)
        
    def change_name(self, newname):
        """ change charactor name, and notify the cell """ 
        self.name = newname
    
    def get_serializablepos(self):
        """ Return coords and facing for this charactor. """
        return self.cell.coords, self.facing
    
    ################ ABSTRACT METHODS TO BE OVERRIDEN ########################

    
    def move(self, cell):
        """ should be overriden by Creep or Avatar. Return nothing. """
        self.log.error('Charactor %s does not have a method to move' % self.name)
        raise NotImplementedError
    
    def attack(self, defer):
        """ should be overriden by Creep or Avatar. Return amount of dmg. """
        self.log.error('Charactor %s does not have a method to attack' % self.name)
        raise NotImplementedError
    
    def rcv_atk(self, atker):
        """ Should be overriden by Creep or Avatar. Return nothing. """
        self.log.error('Charactor %s does not have a method to receive dmg' % self.name)
        raise NotImplementedError

    def die(self):
        """ Should be overriden by Creep or Avatar. Return nothing. """
        self.log.error('Charactor %s does not have a method to die' % self.name)
        raise NotImplementedError
    
    

