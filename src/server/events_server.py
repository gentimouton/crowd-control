from common.events import EventManager
import logging




class SrvEventManager(EventManager):
    """ On the server side, the evt mgr is only used to forward tick events. """

    log = logging.getLogger('server')

    def __init__(self):
        EventManager.__init__(self)
        
    def reg_cb(self, eventClass, callback):
        """ just to log """
        EventManager.reg_cb(self, eventClass, callback)
        self.log.debug(eventClass.__name__ + ' will trigger ' 
                       + callback.__self__.__class__.__name__ + '.' 
                       + callback.__name__)
        
    def post(self, event):
        """ only log non-tick and non-moving events """
        
        if event.__class__.__name__ == 'TickEvent':
            pass
        else:
            #self.log.debug('Event: ' + event.__class__.__name__)
            pass
            
        # notify listeners in any case
        EventManager.post(self, event)
