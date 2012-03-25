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



####################################  TEST  ##############################

if __name__ == "__main__":
    import unittest
    
    # load config from file only once (not for each test)
    load_bot_config()
    
    class TestBotConfig(unittest.TestCase):
        
        def setUp(self):
            pass
        
        def test_logfolder(self):
            # check that it returns a string, and the folder exists.
            folder = config_get_logfolder()
            self.assertIs(type(folder), str)

        def test_loglevel(self):
            # level is int or str. 
            lvl = config_get_loglevel()
            self.assertIn(type(lvl), [str, int])
        
        def test_fps(self):
            # fps is int
            fps = config_get_fps()
            self.assertIn(type(fps), [int, float])

        def test_movefreq(self):
            # movefreq is int
            f = config_get_movefreq()
            self.assertIs(type(f), int)

        def test_hostport(self):
            # host = str, port = int
            host, port = config_get_hostport()
            self.assertIs(type(host), str)
            self.assertIs(type(port), int)
            
        def test_nick(self):
            # nick is str
            nick = config_get_nick()
            self.assertIs(type(nick), str)
            
        def tearDown(self):
            pass
        
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBotConfig)
    unittest.TextTestRunner(verbosity=2).run(suite)
      
