import configparser

__dict = {} #store pairs of (config option, value)

def load_config():
    """ read configs from config file, and simulate a static config class """
    config_filepath = "client_config.ini"
    config = configparser.ConfigParser()
    config.read(config_filepath)
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

def config_get_screencaption():
    return __dict['screencaption']

def config_get_screenwidth():
    return int(__dict['screenwidth'])

def config_get_screenheight():
    return int(__dict['screenheight'])

def config_get_mapname():
    return __dict['mapname']

# --- network

def config_get_host():
    return __dict['host']

def config_get_port():
    return int(__dict['port'])

def config_get_push_freq():
    return int(__dict['push_freq'])

def config_get_my_name():
    return __dict['myname']