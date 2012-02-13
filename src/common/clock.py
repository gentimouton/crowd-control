from time import sleep

class Clock():
    
    def __init__(self, fps=20):
        """ Default: 20Hz frequency. """
        self.fps = fps
        self.elapsed_frames = 0
        
    
    def start(self):
        """ When all actions are done, wait for a few milliseconds. 
        This makes the frequency *at most* as fast as the specified frame rate.
        Irregular frames: those with more work will take longer than those with fewer. 
        """
        self.keep_going = True
        
        while self.keep_going:
            sleep(1. / self.fps)
            self.on_tick(self.elapsed_frames)
            self.elapsed_frames += 1
            # TODO: make the clock more accurate, 
            # by sleeping less if on_tick lasted longer 
    
    def stop(self):
        self.keep_going = False
        
    def on_tick(self, frame_num):
        raise NotImplementedError
