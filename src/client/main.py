#! /usr/bin/env python3

from client.config import load_config
from client.controllers import InputController, ClockController
from client.events_client import ClientEventManager
from client.model import Game
from client.network import NetworkController
from client.view import MasterView
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
