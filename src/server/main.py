from common.events import EventManager
from server.config import load_srv_config
from server.controller.clock import SClockController
from server.controller.network import NetworkController
from server.model.game import SGame



def main():

    load_srv_config()

    evManager = EventManager()

    sclock = SClockController(evManager) #the loop is in there
    
    n = NetworkController(evManager)    
    g = SGame(evManager)
    
    sclock.tick()
        
        
if __name__ == '__main__': main()
