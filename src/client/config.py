from common.config import load_config
import logging
import os

_dict = {} #store pairs of (config option, value)

def load_client_config():
    """ read configs from config file, and simulate a static config class """
    
    log = logging.getLogger('client')
    config_filepath = os.path.abspath("../client/client_config.conf")
    dic = load_config(log, config_filepath)
    for k, v in dic.items():
        _dict[k] = v



# --- graphics config

def config_get_fps():
    return int(_dict['fps'])

def config_get_screenres():
    res = _dict['screenres'].strip().split(',')
    w = int(res[0])
    h = int(res[1])
    return w, h


# --- network

def config_get_hostport():
    hostport = _dict['hostport'].strip().split(':')
    host = hostport[0]
    port = int(hostport[1])
    return host, port

def config_get_nick():
    return _dict['nick']


