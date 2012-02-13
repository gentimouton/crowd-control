#! /usr/bin/env python3.2
from bot.logger import config_logger
from client.clock import CClockController
from client.config import load_config
from client.events_client import ClientEventManager
from client.model import Game
from client.network import NetworkController
from threading import current_thread

    
    
def main():
    
    load_config("bot_config.conf") #config contains all the constants for the game
    
    tid = current_thread().ident
    logger = config_logger(str(tid))
    
    logger.debug('Client started')
    
    evManager = ClientEventManager()

    # TODO: should simulate inputs 
    #kb = InputController(evManager)
    
    clock = CClockController(evManager) #the main loop is in there
    g = Game(evManager)
    n = NetworkController(evManager)
    
    clock.start()
    
    logger.debug('Client stopped')


    
if __name__ == "__main__":
    main()
