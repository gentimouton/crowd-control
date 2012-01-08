#! /usr/bin/env python3

from client2.controllers import InputController, ClockController
from client2.events import EventManager
from client2.model import Game
from client2.view import MasterView


def main():
    evManager = EventManager()

    kb = InputController(evManager)
    clock = ClockController(evManager) #the main loop is in there
    mv = MasterView(evManager)
    g = Game(evManager)

    clock.run()

if __name__ == "__main__":
    main()
