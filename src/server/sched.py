from collections import defaultdict
from common.events import TickEvent
from server.config import config_get_aifps, config_get_ailatentframes
import logging



class Scheduler():
    """ Created when server starts, 
    started by player command,
    stopped by player command or gameover.
    """
    
    log = logging.getLogger('server')

    
    def __init__(self, evManager, world):

        self._em = evManager
        self._em.reg_cb(TickEvent, self.on_tick)
        
        # how much time does a frame contain
        self.timestep = int(1000 / config_get_aifps()) # in milliseconds
        
        #how much time overflowed from the previous frame (if cpu is late)
        # when overflow > timestep, cursor to next frame(s) should ++ 
        self.frameoverflow = 0
        
        # Each frame of actionframes contains a mapping actor->callback(s)
        # for duration of timestep
        num_frames = config_get_ailatentframes()
        self.actionframes = [defaultdict(list) for x in range(num_frames)]   
        self.actioncursor = 0 #loops over the actionframes
        
        # actions so distant in the future that they dont fit in actionframes
        self.distantactions = defaultdict(list) 
        
    
    
    def __str__(self):
        return 'timestep=%d' % self.timestep
    
    def __repr__(self):
        return self.__str__()
        
        
    def schedule_action(self, millis, actor, callback):
        """ Add an entity's callback to be called in millis +/- timestep ms."""
        if millis < len(self.actionframes) * self.timestep:
            # if millis < timestep, schedule for next frame (not this current frame)
            index = self.actioncursor + max(1, int(millis / self.timestep))
            index = index % len(self.actionframes)
            frame = self.actionframes[index]
            frame[actor].append(callback)

        else: # adding far-future actions should happen rarely
            # so it's OK if it costs a tiny bit
            timed_cb = millis, callback
            self.distantactions[actor].append(timed_cb)
    
    
    def unschedule_actor(self, actor):
        """ Remove the actor's actions from the near-future actionframes 
        and from the distant-future actions.
        """
        for frame in self.actionframes:
            frame.pop(actor, None) #remove actor's actions from the frame
        self.distantactions.pop(actor, None) # None prevents KeyError if not found
        
        
        
    def on_tick(self, event):
        """ Iterate over the near-future frames (= actionframes). 
        When reaching the last frame,
        reschedule the distant-future actions,
        and restart iterating the near-future frames.
        """
        
        self.frameoverflow += event.duration
        
        while self.frameoverflow >= self.timestep: #current frame's time is over
            
            # call the callbacks scheduled for this frame;
            # frame is a dict of (actor, callbacks for this actor)
            frame = self.actionframes[self.actioncursor]
            while frame: # until frame is empty dict
                actor, callbacks = frame.popitem() # pick a random (actor, callbacks) 
                for cb in callbacks: # call all the callbacks for that actor
                    cb()
            # now, frame is empty
            
            # last frame of the near-future: add far-future actions if they fit
            if self.actioncursor == len(self.actionframes) - 1:
                self.actioncursor = 0
                
                # set aside the far-future actions
                oldcbs = self.distantactions.copy()
                self.distantactions.clear()
                
                # try to insert all the far-future actions in the near-future frames
                for actor, timed_cbs in oldcbs.items():
                    for millis, cb in timed_cbs:
                        newmillis = millis - len(self.actionframes) * self.timestep
                        self.schedule_action(newmillis, actor, cb)
            
            else: #usual near-future frame
                self.actioncursor += 1
            
            self.frameoverflow -= self.timestep
      
