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


def int_tuple(str_):
    """ transform a string of integers into a tuple
    example: '1,2,3' becomes (1,2,3)
    """
    strlist = str_.strip().split(',') # ['1','2','3']
    return tuple([int(i) for i in strlist]) #tuple of int: (1,2,3)

    
# --- graphics config

def config_get_fps():
    return int(_dict['fps'])

def config_get_screenres():
    a = int_tuple(_dict['screenres'])
    return a


# --- colors

def config_get_fontsize():
    return int(_dict['fontsize'])
def config_get_scrollfontsize():
    return int(_dict['scrollfontsize'])
def config_get_scrollfontcolor():
    return int_tuple(_dict['scrollfontcolor'])

def config_get_hpbarfullcolor():
    return int_tuple(_dict['hpbarfullcolor'])
def config_get_hpbaremptycolor():
    return int_tuple(_dict['hpbaremptycolor'])
    
def config_get_loadingscreen_bgcolor():
    return int_tuple(_dict['loadingscreen_bgcolor'])
def config_get_avdefault_bgcolor():
    return int_tuple(_dict['avdefault_bgcolor'])
def config_get_myav_bgcolor():
    return int_tuple(_dict['myav_bgcolor'])
def config_get_creep_bgcolor():
    return int_tuple(_dict['creep_bgcolor'])

# --- cell colors
def config_get_walkable_color():
    return int_tuple(_dict['walkable_color'])
def config_get_nonwalkable_color():
    return int_tuple(_dict['nonwalkable_color'])
def config_get_entrance_color():
    return int_tuple(_dict['entrance_color'])
def config_get_lair_color():
    return int_tuple(_dict['lair_color'])



# --- widget colors

def config_get_focusedbtn_txtcolor():
    return int_tuple(_dict['focusedbtn_txtcolor'])
def config_get_focusedbtn_bgcolor():
    return int_tuple(_dict['focusedbtn_bgcolor'])
def config_get_unfocusedbtn_txtcolor():
    return int_tuple(_dict['unfocusedbtn_txtcolor'])
def config_get_unfocusedbtn_bgcolor():
    return int_tuple(_dict['unfocusedbtn_bgcolor'])

def config_get_unfocusedinput_txtcolor():
    return int_tuple(_dict['unfocusedinput_txtcolor'])
def config_get_unfocusedinput_bgcolor():
    return int_tuple(_dict['unfocusedinput_bgcolor'])
def config_get_focusedinput_txtcolor():
    return int_tuple(_dict['focusedinput_txtcolor'])
def config_get_focusedinput_bgcolor():
    return int_tuple(_dict['focusedinput_bgcolor'])
        
def config_get_txtlabel_txtcolor():
    return int_tuple(_dict['txtlabel_txtcolor'])
def config_get_txtlabel_bgcolor():
    return int_tuple(_dict['txtlabel_bgcolor'])

def config_get_chatlog_txtcolor():
    return int_tuple(_dict['chatlog_txtcolor'])
def config_get_chatlog_bgcolor():
    return int_tuple(_dict['chatlog_bgcolor'])



# --- network

def config_get_hostport():
    hostport = _dict['hostport'].strip().split(':')
    host = hostport[0]
    port = int(hostport[1])
    return host, port

def config_get_nick():
    return _dict['nick']



# ---- logging

def config_get_logfolder():
    return _dict['logfolder']

