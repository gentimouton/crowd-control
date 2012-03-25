from bot.config import config_get_loglevel
from bot.config import config_get_logfolder
import logging.config
import os

def config_logger(botname):
    """Customize the logging handler for this bot instance:
    The file to log in ends with the thread id. 
    """
    
    logging.config.fileConfig('bot_logging.conf')
    clogger = logging.getLogger('client')
    clogger.setLevel(config_get_loglevel())
    
    filepath = os.path.join(config_get_logfolder(), 'bot-' + botname + '.log')
    hdlr = logging.FileHandler(filepath, 'w')
    
    formatter = logging.Formatter('%(asctime)s, %(levelname)-8s,'
                                  + ' %(filename)-16s, %(message)s')
    hdlr.setFormatter(formatter)
    
    clogger.addHandler(hdlr)
    
    return clogger

##################################################


if __name__ == "__main__":
    import unittest
    from logging import Logger
    from bot.config import load_bot_config
    
    class TestBotConfig(unittest.TestCase):
    
        def setUp(self):
            load_bot_config()
        
        def test_buildlogger(self):
            # check that the returned object is a logger
            logger = config_logger('botname')
            self.assertIsInstance(logger, Logger)            
            
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBotConfig)
    unittest.TextTestRunner(verbosity=2).run(suite)
      