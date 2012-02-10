from collections import deque, defaultdict
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
    pass


class EventManager:
    """this object is responsible for coordinating most communication
    between the Model, Views, and Controllers.
    See http://stackoverflow.com/questions/7249388/python-duck-typing-for-mvc-event-handling-in-pygame
    """

    def __init__(self):
        # map events to list of listener callbacks
        self._listener_callbacks = defaultdict(list)

        self.eventdq = deque()
        
        # Since a dict can't change size when iterated, when a listener is 
        # added during a loop iteration over the existing listeners,
        #  add temporarily that new listener to the _new_callbacks dict.
        self._new_callbacks = defaultdict(list)


        
    def reg_cb(self, eventClass, callback):
        """ Register callback.
        Turn the listener's callback function into a function weakly bound 
        to the listener it belongs to (weak ref to the listener's self),
        and then add that transformed callback to the temporary callbacks. 
        """
        if (hasattr(callback, '__self__') and
            hasattr(callback, '__func__')):
            callback = WeakBoundMethod(callback)
        
        try:
            self._new_callbacks[eventClass].append(callback)
        except KeyError:
            self._new_callbacks[eventClass] = [callback]

        
    def join_new_listeners(self):
        """ add new listener callbacks to the current ones """
        if self._new_callbacks:
            
            for evtClass in self._new_callbacks:
                try: #merge the new and current callback lists
                    self._listener_callbacks[evtClass] += self._new_callbacks[evtClass]
                except KeyError:
                    self._listener_callbacks[evtClass] = self._new_callbacks[evtClass]
                    
            self._new_callbacks.clear() 

            
    def post(self, event):
        """ do housekeeping of the listeners (remove/add those who requested it)
        then wait for clock ticks to notify listeners of all events 
        in chronological order 
        """
                
        # at each clock tick, notify all listeners of all the events 
        # in the order these events were received
        if event.__class__.__name__ == 'TickEvent':
            self.join_new_listeners() #necessary for at least the very first tick
            while self.eventdq:
                ev = self.eventdq.popleft()
                self.join_new_listeners()
                for callback in self._listener_callbacks[ev.__class__]: 
                    #some of those listeners may enqueue events on the fly
                    # those events will be treated within this while loop,
                    # they don't have to wait for the next tick event
                    callback(ev) 
                    
                self.join_new_listeners()
                
            # finally, post tick event
            for cb in self._listener_callbacks[event.__class__]:
                cb(event)
                
            self.join_new_listeners()
            
        else: # non-tick event
            self.eventdq.append(event)
            
