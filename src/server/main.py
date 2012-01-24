from server.config import load_srv_config
from server.controller.clock import SClockController
from server.controller.mediator import Mediator
from server.controller.network import NetworkController
from server.events_server import SEventManager



def main():

    load_srv_config()

    evManager = SEventManager()

    sclock = SClockController(evManager) #the loop is in there
    
    m = Mediator(evManager)
    n = NetworkController(evManager)
    #g = Game(evManager)
    
    sclock.tick()
        
        
if __name__ == '__main__': main()
