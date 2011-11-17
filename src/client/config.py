import configparser

__dict = {} #store pairs of (config option, value)

def load_config():
    """ read configs from config file, and simulate a static config class """
    config_filepath = "config.ini"
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

# main config
def config_get_fps():
    return int(__dict['fps'])

def config_get_screencaption():
    return __dict['screencaption']


# board config
def config_get_screenwidth():
    return int(__dict['screenwidth'])

def config_get_screenheight():
    return int(__dict['screenheight'])

