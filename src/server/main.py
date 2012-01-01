from server.config import config_get_fps, load_srv_config
from server.controller.network import NetworkController
import pygame
from server.controller.mediator import Mediator

def main():

    load_srv_config()
    mediator = Mediator()
    # network
    nw = NetworkController(mediator)
    mediator.setnetwork(nw)
     
    # mechanics
    clock = pygame.time.Clock()
    elapsed_frames = 0
    fps = config_get_fps()

    while 1:
        clock.tick(fps)
        
        # network updates: pump all client channels
        nw.Pump()
        
        # TODO: NPC and mechanics updates

        elapsed_frames += 1


if __name__ == '__main__': main()

