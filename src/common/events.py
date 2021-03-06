from collections import deque, defaultdict
import logging
import weakref



class WeakBoundMethod:
    """ Hold only a weak reference to self
    from http://stackoverflow.com/questions/7249388/python-duck-typing-for-mvc-event-handling-in-pygame 
    """
    
    def __init__(self, meth):
        self._self = weakref.ref(meth.__self__)
        self._parentclass = meth.__self__
        self._func = meth.__func__

    def __call__(self, *args, **kwargs):
        self._func(self._self(), *args, **kwargs)





class TickEvent:
    def __init__(self, millis):
        self.duration = millis # how long since last tick


class EventManager:
    """this object is responsible for coordinating most communication
    between the Model, Views, and Controllers.
    See http://stackoverflow.com/questions/7249388/python-duck-typing-for-mvc-event-handling-in-pygame
    """

    def __init__(self):
        # maps events to list of listener callbacks
        self._callbacks = defaultdict(set)
        # when a listener dies, callbacks have to be removed manually 
        # from their set, otherwise memory leaks!

        self.eventdq = deque()
        
        # Since a dict can't change size when iterated, when a listener is 
        # added during a loop iteration over the existing listeners,
        # add temporarily that new listener to the new callbacks.
        self._new_callbacks = defaultdict(set)

        self.log = logging.getLogger('client')

        
    def reg_cb(self, eventClass, callback):
        """ Register a callback for a particular event.
        Turn the listener's callback function into a function weakly bound 
        to the listener it belongs to (weak ref to the listener's self),
        and then add that transformed callback to the temporary callbacks. 
        """
        if (hasattr(callback, '__self__') and
            hasattr(callback, '__func__')):
            callback = WeakBoundMethod(callback)
        
        # defaultdict: if the set does not exist, create it on the fly.
        # Add the callback to the set in any case.
        self._new_callbacks[eventClass].add(callback)
        

        
    def join_new_listeners(self):
        """ add new listener callbacks to the current ones """
        
        if self._new_callbacks:
            
            for evClass in self._new_callbacks:
                self._callbacks[evClass] = self._callbacks[evClass].union(self._new_callbacks[evClass])
                
            self._new_callbacks.clear() 


            
    def post(self, event):
        """ do housekeeping of the listeners (remove/add those who requested it)
        then wait for clock ticks to notify listeners of all events 
        in chronological order 
        """
                
        # at each clock tick, notify all listeners of all the events 
        # in the order these events were received
        if event.__class__ == TickEvent:
            self.join_new_listeners() #necessary for at least the very first tick
            while self.eventdq:
                ev = self.eventdq.popleft()
                
                self.join_new_listeners()
                for callback in self._callbacks[ev.__class__]: 
                    #some of those listeners may enqueue events on the fly
                    # those events will be treated within this while loop,
                    # they don't have to wait for the next tick event
                    callback(ev) 
                    
                self.join_new_listeners()
                
            # finally, post tick event
            for cb in self._callbacks[event.__class__]:
                cb(event)
                
            self.join_new_listeners()
            
        else: # non-tick event
            self.eventdq.append(event)
            
