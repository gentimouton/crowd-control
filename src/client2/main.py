#! /usr/bin/env python3

from client2.config import load_config
from client2.controllers import InputController, ClockController
from client2.events import EventManager
from client2.model import Game
from client2.network import NetworkController
from client2.view import MasterView


def main():
    
    load_config() #config contains all the constants for the game
    
    evManager = EventManager()

    kb = InputController(evManager)
    clock = ClockController(evManager) #the main loop is in there
    mv = MasterView(evManager)
    g = Game(evManager)
    n = NetworkController(evManager)
    
    clock.run()

if __name__ == "__main__":
    main()
