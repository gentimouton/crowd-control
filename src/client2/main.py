#! /usr/bin/env python3

from client2.controllers import InputController, CPUSpinnerController
from client2.events import EventManager
from client2.model import Game
from client2.view import GameView

def main():
    """..."""
    evManager = EventManager()

    kb = InputController(evManager)
    spinner = CPUSpinnerController(evManager)
    v = GameView(evManager)
    g = Game(evManager)

    spinner.run()

if __name__ == "__main__":
    main()
