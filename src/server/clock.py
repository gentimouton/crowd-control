from common.clock import Clock
from common.events import TickEvent
from server.config import config_get_fps, config_get_logperiod
import logging
import os
import time

log = logging.getLogger('server')

class SClockController(Clock):
    """ sends tick events - capped at 100 Hz """

    def __init__(self, evManager):

        self._em = evManager
        
        fps = config_get_fps()
        if fps <= 0 or fps > 100:
            fps = 100 #100 fps is the maximum timer resolution anyway
        Clock.__init__(self, fps)
        
        # slice = set of frames between 2 logging
        self.slice_size = config_get_logperiod() * fps # number of frames in the slice
        self.slice_work_time = 0 # cumulated time worked for a frame slice  
        self.slice_start_time = time.time() # when did I last log? now!
        self.cumul_cpu_time = 0 # cumulated cpu time used since process started 

            
    def on_tick(self, workduration, totalduration):
        """ Log how much time during a frame was spent working, 
        and send a tick event with the whole loop duration.
        """
        
        self.slice_work_time += workduration
        frame_num = self.elapsed_frames # from superclass Clock
        slice_size = self.slice_size
        
        if frame_num % slice_size == 0 and frame_num != 0: # time to log
            # compute the average work time for the frames in this slice
            slice_work_time = self.slice_work_time
            self.slice_work_time = 0
            avg_frame_work_time = slice_work_time / slice_size
            # compute the cpu time for this whole slice 
            cumul_cpu_times = os.times()            
            cumul_cpu_time = cumul_cpu_times[0] # only keep total cpu time
            slice_cpu_time = cumul_cpu_time - self.cumul_cpu_time
            self.cumul_cpu_time = cumul_cpu_time
            # reset slice start time
            now = time.time()
            slice_time = now - self.slice_start_time
            self.slice_start_time = now
            # compute cpu %
            slice_cpu_percent = 100 * slice_cpu_time / slice_time
            
            begin = frame_num - slice_size
            end = frame_num
            log.debug('Frames %d-%d worked on average %3.3f ms, using %2.0f%% CPU' 
                      % (begin, end, avg_frame_work_time, slice_cpu_percent))
        
        event = TickEvent(totalduration) #duration in millis
        self._em.post(event)
        
    
    def start(self):
        """ start the clock """
        log.debug('Clock starts to tick at ' + str(self.fps) + ' fps')
        Clock.start(self)
        
        
