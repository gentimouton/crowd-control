#! /usr/bin/env python3

from client2.config import load_config
from client2.controllers import InputController, ClockController
from client2.events_client import ClientEventManager
from client2.model import Game
from client2.network import NetworkController
from client2.view import MasterView
import logging.config


def main():
    
    logging.config.fileConfig('client_logging.conf')

    clogger = logging.getLogger('client')

    clogger.debug('Client started')
    
    load_config() #config contains all the constants for the game
    
    evManager = ClientEventManager()

    kb = InputController(evManager)
    clock = ClockController(evManager) #the main loop is in there
    mv = MasterView(evManager)
    g = Game(evManager)
    n = NetworkController(evManager)
    
    clock.run()
    
    clogger.debug('Client stopped')

if __name__ == "__main__":
    main()
