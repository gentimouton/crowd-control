#! /usr/bin/env python3.2

from client.clock import CClockController
from client.config import config_get_fps, config_get_hostport, config_get_nick, \
    load_client_config
from client.events_client import ClientEventManager
from client.input import InputController
from client.model import Game
from client.network import NetworkController
from client.view import MasterView
import logging.config


def main():
    
    logging.config.fileConfig('client_logging.conf')

    clogger = logging.getLogger('client')

    clogger.debug('Client started')
    
    load_client_config() #config contains all the constants for the game
    
    evManager = ClientEventManager()

    # These components are shared with bots. Their config is given to them. 
    clock = CClockController(evManager, config_get_fps()) #the main loop is in there
    n = NetworkController(evManager, config_get_hostport(), config_get_nick())
    g = Game(evManager)
    
    # These components are specific to human clients; they can grab the client config themselves. 
    kb = InputController(evManager)
    mv = MasterView(evManager)
    
    
    clock.start()
    
    clogger.debug('Client stopped')

if __name__ == "__main__":
    main()
