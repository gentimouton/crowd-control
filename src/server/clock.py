from common.clock import Clock
from common.events import TickEvent
from server.config import config_get_fps, config_get_logperiod
import logging
import os
import time
import resource

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
        self.slice_start_time = time.time() # the first slice starts now
        self.slice_work_time = 0 # cumulated time worked for a frame slice  
        self.cumul_ucpu_time = 0 # cumulated userland cpu time used since process started
        self.cumul_kcpu_time = 0 # cumulated kernel cpu time used since process started 
        self.cumul_vcsw = 0 # cumulated voluntary context switches, posix OS only
        self.cumul_nvcsw = 0 # cumulated involuntary switches, posix OS only
        
            
    def on_tick(self, workduration, totalduration):
        """ Log how much time during a frame was spent working, 
        and send a tick event with the whole loop duration.
        Both durations are in milliseconds.
        """
        
        self.slice_work_time += workduration
        frame_num = self.elapsed_frames # from superclass Clock
        slice_size = self.slice_size
        
        if frame_num % slice_size == 0 and frame_num != 0: # time to log
            
            # compute the average work time for the frames in this slice
            slice_work_time = self.slice_work_time
            now = time.time()
            slice_duration = now - self.slice_start_time
            self.slice_start_time = now
            self.slice_work_time = 0
            avg_frame_work_time = slice_work_time / slice_size
            
            # compute various metrics for this slice
            ram = None
            nvcsw_persec = None
            vcsw_persec = None
            os_is_posix = os.name == 'posix'
            
            if os_is_posix: # resource module only available on posix OS
                rusage = resource.getrusage(resource.RUSAGE_SELF)
                # get CPU usage since process started
                cumul_ucpu_time = rusage.ru_utime # in ms
                cumul_kcpu_time = rusage.ru_stime # in ms
                # RAM usage
                ram = rusage.ru_maxrss * resource.getpagesize() # in bytes
                ram = int(ram / 10 ** 6) # in MB
                # voluntary context switches such as waiting for IO
                vcsw = rusage.ru_nvcsw
                vcsw_persec = int((vcsw - self.cumul_vcsw) / slice_duration)
                self.cumul_vcsw = vcsw
                # non-voluntary context switches (due to scheduler)
                nvcsw = rusage.ru_nivcsw
                nvcsw_persec = int((nvcsw - self.cumul_nvcsw) / slice_duration)
                self.cumul_nvcsw = nvcsw
                
            else: # non-posix: CPU only
                cumul_cpu_times = os.times() #same as rusage.ru_time           
                cumul_ucpu_time = cumul_cpu_times[0] # time in userland
                cumul_kcpu_time = cumul_cpu_times[1] # time in kernel space
                
            # compute CPU % for all OS
            slice_ucpu_time = cumul_ucpu_time - self.cumul_ucpu_time
            self.cumul_ucpu_time = cumul_ucpu_time
            slice_ucpu_percent = int(100 * slice_ucpu_time / slice_duration)
            slice_kcpu_time = cumul_kcpu_time - self.cumul_kcpu_time
            self.cumul_kcpu_time = cumul_kcpu_time
            slice_kcpu_percent = int(100 * slice_kcpu_time / slice_duration)
            
            # build text to display
            txt = ('Work/frame: %4.3f ms, CPU: %2d+%2d %%'\
                   % (avg_frame_work_time, slice_ucpu_percent, slice_kcpu_percent))
            if ram:
                txt = txt + ', RAM: %3d MB' % ram
            if vcsw_persec is not None:
                txt = txt + ', VCSW: %3d/s' % vcsw_persec
            if nvcsw_persec is not None:
                txt = txt + ', NVCSW: %3d/s' % nvcsw_persec
            log.debug(txt)
            
        event = TickEvent(totalduration) #duration in millis
        self._em.post(event)
        
    
    def start(self):
        """ start the clock """
        log.debug('Clock starts to tick at ' + str(self.fps) + ' fps')
        Clock.start(self)
        
        
