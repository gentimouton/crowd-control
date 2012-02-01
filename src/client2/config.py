import configparser
import os

__dict = {} #store pairs of (config option, value)

def load_config():
    """ read configs from config file, and simulate a static config class """
    
    config_filepath = "client_config.ini"
    config = configparser.ConfigParser()
    files_read = config.read(config_filepath)
    if not files_read: #config.read() could not find the config file
        print('Error: Could not find config file at', 
              os.path.abspath(config_filepath))
        exit()
        
    for section in config.sections():
        options = config.options(section)
        for option in options:
            try:
                __dict[option] = config.get(section, option)
                if __dict[option] == -1:
                    print("[ERROR]: skipped option: %s" % option)
            except:
                print("[ERROR]: exception on option %s" % option)
                __dict[option] = None 
    return


# --- graphics config

def config_get_fps():
    return int(__dict['fps'])

def config_get_screenres():
    res = __dict['screenres'].strip().split(',')
    w = int(res[0])
    h = int(res[1])
    return w, h


# --- network

def config_get_hostport():
    hostport = __dict['hostport'].strip().split(':')
    host = hostport[0]
    port = int(hostport[1])
    return host, port

def config_get_nick():
    return __dict['nick']
