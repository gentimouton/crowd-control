#! /usr/bin/env python3.2

from client.clock import CClockController
from client.config import config_get_fps, config_get_hostport, config_get_nick, \
    load_client_config
from client.events_client import ClientEventManager
from client.input import InputController
from client.logger import config_logger
from client.model.model import Game
from client.network import NetworkController
from client.view.view import MasterView
from threading import current_thread

    
def main():

    load_client_config() #config contains all the constants for the game

    # make sure that 2 clients running on the same machine log into 2 separate files
    clientid = str(current_thread().ident)
    clogger = config_logger(clientid)
    
    clogger.debug('Client started')
    
    em = ClientEventManager()
    
    # These components are shared with bots. Their config is given to them. 
    clock = CClockController(em, config_get_fps()) #main loop is in there
    n = NetworkController(em, config_get_hostport(), config_get_nick())
    g = Game(em)
    
    # These components are specific to human clients. 
    # They can grab the client config themselves. 
    kb = InputController(em)
    mv = MasterView(em)
    
    
    clock.start()
    
    clogger.debug('Client stopped')

if __name__ == "__main__":
    main()
