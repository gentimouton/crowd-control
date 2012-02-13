from common.config import load_config
import logging
import os

_dict = {} #store pairs of (config option, value)

def load_srv_config():
    """ read configs from config file, and simulate a static config class """
    
    log = logging.getLogger('server')
    config_filepath = "srv_config.conf"
    dic = load_config(log, os.path.abspath(config_filepath))
    for k,v in dic.items():
        _dict[k] = v
    


# main config
def config_get_fps():
    return int(_dict['fps'])
def config_get_mapname():
    return _dict['mapname']

# network
def config_get_hostport():
    hostport = _dict['hostport'].strip().split(':')
    host = hostport[0]
    port = int(hostport[1])
    return host, port

