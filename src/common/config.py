import configparser
import os


def load_config(logger, config_filepath):
    """ Generic config file loading. Return the config as a dict. """
    dic = {}
     
    config = configparser.ConfigParser()
    files_read = config.read(config_filepath)
    if not files_read: #config.read() could not find the config file
        logger.critical('Could not find config file at' + 
              os.path.abspath(config_filepath))
        exit()
        
    for section in config.sections():
        options = config.options(section)
        for option in options:
            try:
                dic[option] = config.get(section, option)
                if dic[option] == -1:
                    logger.error("Skipped option: %s" % option)
            except:
                dic[option] = None
                logger.error("Exception on option %s" % option)
    
    logger.debug('Loaded config')
    
    return dic
