from server.config import config_get_fps, config_get_host, config_get_port, \
    load_srv_config
from server.networkengine import ServerNetworkEngine
import pygame


def main():

    load_srv_config()

    # network
    addr = config_get_host(), config_get_port()
    nEngine = ServerNetworkEngine(localaddr=addr)
    
    # mechanics
    clock = pygame.time.Clock()
    elapsed_frames = 0
    fps = config_get_fps()
    
    #Main Loop
    while 1:     
        clock.tick(fps)
        # network updates
        nEngine.Pump() #pump all channels
        
        # mechanics updates
        #if elapsed_frames % 90 == 1:
        #    nEngine.send_chatmsg_all("server is alive")
        elapsed_frames += 1

        # sending to a client
        # clientchannel.Send({"action": "hello", "message": "hello client!"})

if __name__ == '__main__': main()

