import configparser
import logging

__dict = {} #store pairs of (config option, value)



def load_srv_config():
    """ read configs from config file, and simulate a static config class """
    
    log = logging.getLogger('server')

    config_filepath = "srv_config.conf"
    config = configparser.ConfigParser()
    config.read(config_filepath)
    for section in config.sections():
        options = config.options(section)
        for option in options:
            try:
                __dict[option] = config.get(section, option)
                if __dict[option] == -1:
                    log.error("Skipped option: %s" % option)
            except:
                log.error("Exception on option %s" % option)
                __dict[option] = None
                
    return



############################################################################


# main config
def config_get_fps():
    return int(__dict['fps'])
def config_get_mapname():
    return __dict['mapname']

# network
def config_get_hostport():
    hostport = __dict['hostport'].strip().split(':')
    host = hostport[0]
    port = int(hostport[1])
    return host, port

