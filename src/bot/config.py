from common.config import load_config
import logging
import os

_dict = {}

def load_bot_config():
    """ read configs from config file, and simulate a static config class """
    
    log = logging.getLogger('client')
    config_filepath = "bot_config.conf"
    dic = load_config(log, os.path.abspath(config_filepath))
    for k, v in dic.items():
        _dict[k] = v
    
    
# --- logging

def config_get_logfolder():
    return _dict['logfolder']

def config_get_loglevel():
    return _dict['loglevel']


# --- graphics config

def config_get_fps():
    return int(_dict['fps'])

def config_get_movefreq():
    return int(_dict['movefreq'])


# --- network

def config_get_hostport():
    hostport = _dict['hostport'].strip().split(':')
    host = hostport[0]
    port = int(hostport[1])
    return host, port

def config_get_nick():
    return _dict['nick']
