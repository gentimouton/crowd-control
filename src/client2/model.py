from client2.constants import DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT, \
    DIRECTION_UP
from client2.events import CharactorMoveEvent, GameStartedEvent, \
    CharactorMoveRequest, TickEvent, MapBuiltEvent, CharactorPlaceEvent



class Game:
    """..."""

    STATE_PREPARING = 'preparing'
    STATE_RUNNING = 'running'
    STATE_PAUSED = 'paused'


    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        self.state = Game.STATE_PREPARING
        
        self.players = [ Player(evManager) ]
        self.map = Map(evManager)


    def start(self):
        self.map.build()
        self.state = Game.STATE_RUNNING
        ev = GameStartedEvent(self)
        self.evManager.post(ev)


    def notify(self, event):
        if isinstance(event, TickEvent):
            if self.state == Game.STATE_PREPARING:
                self.start()


class Player(object):
    """..."""
    def __init__(self, evManager):
        self.evManager = evManager
        self.game = None
        self.name = ""
        self.evManager.register_listener(self)

        self.charactors = [ Charactor(evManager) ]


    def __str__(self):
        return '<Player %s %s>' % (self.name, id(self))



    def notify(self, event):
        pass


class Charactor:
    """..."""

    STATE_INACTIVE = 0
    STATE_ACTIVE = 1

    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.register_listener(self)

        self.sector = None
        self.state = Charactor.STATE_INACTIVE


    def __str__(self):
        return '<Charactor %s>' % id(self)


    def move(self, direction):
        if self.state == Charactor.STATE_INACTIVE:
            return

        if self.sector.move_possible(direction):
            newSector = self.sector.neighbors[direction]
            self.sector = newSector
            ev = CharactorMoveEvent(self)
            self.evManager.post(ev)


    def place(self, sector):
        self.sector = sector
        self.state = Charactor.STATE_ACTIVE

        ev = CharactorPlaceEvent(self)
        self.evManager.post(ev)


    def notify(self, event):
        if isinstance(event, GameStartedEvent):
            gameMap = event.game.map
            self.place(gameMap.sectors[gameMap.startSectorIndex])

        elif isinstance(event, CharactorMoveRequest):
            self.move(event.direction)


class Map:
    """..."""

    STATE_PREPARING = 0
    STATE_BUILT = 1



    def __init__(self, evManager):
        self.evManager = evManager
        #self.evManager.register_listener( self )

        self.state = Map.STATE_PREPARING

        self.sectors = []
        self.startSectorIndex = 0


    def build(self):
        for i in range(9):
            self.sectors.append(Sector(self.evManager))

        self.sectors[3].neighbors[DIRECTION_UP] = self.sectors[0]
        self.sectors[4].neighbors[DIRECTION_UP] = self.sectors[1]
        self.sectors[5].neighbors[DIRECTION_UP] = self.sectors[2]
        self.sectors[6].neighbors[DIRECTION_UP] = self.sectors[3]
        self.sectors[7].neighbors[DIRECTION_UP] = self.sectors[4]
        self.sectors[8].neighbors[DIRECTION_UP] = self.sectors[5]

        self.sectors[0].neighbors[DIRECTION_DOWN] = self.sectors[3]
        self.sectors[1].neighbors[DIRECTION_DOWN] = self.sectors[4]
        self.sectors[2].neighbors[DIRECTION_DOWN] = self.sectors[5]
        self.sectors[3].neighbors[DIRECTION_DOWN] = self.sectors[6]
        self.sectors[4].neighbors[DIRECTION_DOWN] = self.sectors[7]
        self.sectors[5].neighbors[DIRECTION_DOWN] = self.sectors[8]

        self.sectors[1].neighbors[DIRECTION_LEFT] = self.sectors[0]
        self.sectors[2].neighbors[DIRECTION_LEFT] = self.sectors[1]
        self.sectors[4].neighbors[DIRECTION_LEFT] = self.sectors[3]
        self.sectors[5].neighbors[DIRECTION_LEFT] = self.sectors[4]
        self.sectors[7].neighbors[DIRECTION_LEFT] = self.sectors[6]
        self.sectors[8].neighbors[DIRECTION_LEFT] = self.sectors[7]

        self.sectors[0].neighbors[DIRECTION_RIGHT] = self.sectors[1]
        self.sectors[1].neighbors[DIRECTION_RIGHT] = self.sectors[2]
        self.sectors[3].neighbors[DIRECTION_RIGHT] = self.sectors[4]
        self.sectors[4].neighbors[DIRECTION_RIGHT] = self.sectors[5]
        self.sectors[6].neighbors[DIRECTION_RIGHT] = self.sectors[7]
        self.sectors[7].neighbors[DIRECTION_RIGHT] = self.sectors[8]

        self.state = Map.STATE_BUILT

        ev = MapBuiltEvent(self)
        self.evManager.post(ev)


class Sector:
    """..."""
    def __init__(self, evManager):
        self.evManager = evManager
        #self.evManager.register_listener( self )

        self.neighbors = dict()

        self.neighbors[DIRECTION_UP] = None
        self.neighbors[DIRECTION_DOWN] = None
        self.neighbors[DIRECTION_LEFT] = None
        self.neighbors[DIRECTION_RIGHT] = None


    def move_possible(self, direction):
        if self.neighbors[direction]:
            return True

