from client.config import config_get_logfolder
import logging.config
import os

def config_logger(cid):
    """Customize the logging handler for this bot instance:
    The file to log in ends with the thread id. 
    """
    
    logging.config.fileConfig('client_logging.conf')
    clogger = logging.getLogger('client')
    clogger.setLevel('DEBUG')
    
    filepath = os.path.join(config_get_logfolder(), 'client-' + cid + '.log')
    hdlr = logging.FileHandler(filepath, 'w')
    
    formatter = logging.Formatter('%(asctime)s, %(levelname)-8s,'
                                  + ' %(filename)-16s, %(message)s')
    hdlr.setFormatter(formatter)
    
    clogger.addHandler(hdlr)
    
    return clogger