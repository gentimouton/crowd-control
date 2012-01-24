from _weakrefset import WeakSet
from collections import deque



class Event:
    """superclass for events sent to the EventManager"""
    def __init__(self):
        self.name = "Generic Event"


class TickEvent(Event):
    def __init__(self):
        self.name = "CPU Tick Event"






class EventManager:
    """this object is responsible for coordinating most communication
    between the Model, View, and Controller."""
    def __init__(self):
        self.listeners = WeakSet()
        self.eventdq = deque()
        
        # Since a dict can't change size when iterated, when a listener is 
        # added during a loop iteration over the existing listeners,
        #  add temporarily that new listener to the newlisteners dict.
        self.newlisteners = WeakSet()  

        
    def register_listener(self, listener):
        self.newlisteners.add(listener)


    def join_new_listeners(self):
        """ add new listeners to the actual listeners """
        if len(self.newlisteners):
            for newlistener in self.newlisteners:
                self.listeners.add(newlistener)
            self.newlisteners.clear() 

            
    def post(self, event):
        """ do housekeeping of the listeners (remove/add those who requested it)
        then wait for clock ticks to notify listeners of all events 
        in chronological order 
        """
                
        # at each clock tick, notify all listeners of all the events 
        # in the order these events were received
        if isinstance(event, TickEvent):
            while len(self.eventdq):
                ev = self.eventdq.popleft()
                self.join_new_listeners()
                for listener in self.listeners: 
                    #some of those listeners may enqueue events on the fly
                    # those events will be treated within this while loop,
                    # they don't have to wait for the next tick event
                    listener.notify(ev) 
                    
                self.join_new_listeners()
                
            # post tick event
            for listener in self.listeners:
                listener.notify(event)
            self.join_new_listeners()
            
        else:
            self.eventdq.append(event)
            
