from server.config import config_get_fps, load_srv_config
from server.networkengine import ServerNetworkEngine
import pygame


def main():

    load_srv_config()
    # network
    nEngine = ServerNetworkEngine()
    
    # mechanics
    clock = pygame.time.Clock()
    elapsed_frames = 0
    fps = config_get_fps()

    while 1:
        clock.tick(fps)
        
        # network updates: pump all client channels
        nEngine.Pump()
        
        # TODO: NPC and mechanics updates

        elapsed_frames += 1


if __name__ == '__main__': main()

