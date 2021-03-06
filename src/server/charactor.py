
class SCharactor():
    """ Abstract class representing game charactors, 
    such as player avatars or creeps. 
    """
    def __init__(self, name, cell, facing, hp, atk):
        self.name = name
        self.facing = facing #direction the player is facing
        self.hp = self.maxhp = hp
        self.atk = atk
    
    
    def __str__(self):
        return '%s at %s, hp=%d' % (self.name, self.cell.coords, self.hp)
        
    
    def serialize(self):
        """ Serialize: Return coords, facing, atk, and hp for this charactor. """
        dic = {'coords':self.cell.coords,
               'facing':self.facing,
               'atk':self.atk,
               'maxhp':self.maxhp,
               'hp':self.hp}
        return dic
    
    
    ############################  hp  ############################
    
    def update_hps(self, hp, mhp):
        """ If alive, update hp and maxhp.
        Make sure hp never gets bigger than max hp.
        """
        if self.hp > 0:
            if mhp and mhp > 0: # can't set mhp to 0 or less
                self.maxhp = mhp
                self.hp = min(mhp, self.hp) # eventually reduce self.hp to mhp
            if hp and hp > 0: # can't suicide
                self.hp = min(hp, self.maxhp)
            if hp == None and mhp == None:
                self.hp = self.maxhp # full heal
            # broadcast new state
            myinfo = self.serialize()
            self._nw.bc_hps(self.name, myinfo)
        
        
    ################ ABSTRACT METHODS TO BE OVERRIDEN ########################

    def move(self, newcell, facing):
        """ should be overriden by Creep or Avatar. Return nothing. """
        self.log.error('Charactor %s does not have a method to move' % self.name)
        raise NotImplementedError
                    
    def attack(self, defer):
        """ should be overriden by Creep or Avatar. Return amount of dmg. """
        self.log.error('Charactor %s does not have a method to attack' % self.name)
        raise NotImplementedError
    
    def rcv_atk(self, atker):
        """ Should be overriden by Creep or Avatar. Return amount of dmg. """
        self.log.error('Charactor %s does not have a method to receive atk' % self.name)
        raise NotImplementedError

    def rcv_dmg(self, atker):
        """ Should be overriden by Creep or Avatar. Return amount of dmg. """
        self.log.error('Charactor %s does not have a method to receive dmg' % self.name)
        raise NotImplementedError

    def die(self):
        """ Should be overriden by Creep or Avatar. Return nothing. """
        self.log.error('Charactor %s does not have a method to die' % self.name)
        raise NotImplementedError
    
    

