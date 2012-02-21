from server.config import load_srv_config
from server.clock import SClockController
from server.network import NetworkController
from server.events_server import SrvEventManager
from server.model import SGame
import logging.config



def main():
    
    logging.config.fileConfig('srv_logging.conf')
    log = logging.getLogger('server')

    log.info('Server started')
    
    load_srv_config()

    evManager = SrvEventManager()

    sclock = SClockController(evManager) #the loop is in there
    
    n = NetworkController(evManager)
    g = SGame(evManager)
    
    sclock.start()
        
    log.info('Server stopped')

        
if __name__ == '__main__': 
    main()
