#! /usr/bin/env python3.2
from bot.config import load_bot_config, config_get_fps, config_get_hostport, \
    config_get_nick
from bot.input import BotInputController
from bot.logger import config_logger
from client.clock import CClockController
from client.events_client import ClientEventManager
from client.model import Game
from client.network import NetworkController
from threading import current_thread



def main():
    
    load_bot_config() # bot-specific config (e.g. logger)
    
    tid = current_thread().ident
    logger = config_logger(str(tid))
    
    logger.debug('Client started')
    
    evManager = ClientEventManager()

    ic = BotInputController(evManager) # simulate inputs    
    clock = CClockController(evManager, config_get_fps()) #the main loop is in there
    g = Game(evManager)
    n = NetworkController(evManager, config_get_hostport(), config_get_nick())
    
    clock.start()
    
    logger.debug('Client stopped')


    
if __name__ == "__main__":
    main()
