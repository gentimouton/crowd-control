#! /usr/bin/env python3.2
from client.config import load_config
from client.controllers import CClockController
from client.events_client import ClientEventManager
from client.model import Game
from client.network import NetworkController
import logging.config



def main():
    logging.config.fileConfig('bot_logging.conf')
    clogger = logging.getLogger('client')
    clogger.debug('Client started')
    
    load_config("bot_config.conf") #config contains all the constants for the game
    
    evManager = ClientEventManager()

    # TODO: should simulate inputs 
    #kb = InputController(evManager)
    
    clock = CClockController(evManager) #the main loop is in there
    g = Game(evManager)
    n = NetworkController(evManager)
    
    clock.start()
    
    clogger.debug('Client stopped')


    
if __name__ == "__main__":
    main()