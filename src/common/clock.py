from time import sleep, time

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
        beforetick = aftertick = time()
        
        while self.keep_going:
            workduration = aftertick - beforetick #0 on first tick
            sleepduration = 1 / self.fps - workduration
            sleepduration = max(0, sleepduration)# dont sleep if late
            if sleepduration > 0: 
                sleep(sleepduration)
                
            beforetick = time()
            wholeloopdur = (sleepduration + workduration)
            self.on_tick(workduration * 1000, wholeloopdur * 1000)
            aftertick = time()
            
            self.elapsed_frames += 1


    
    def stop(self):
        self.keep_going = False
        
    def on_tick(self, worktime, totaltime):
        raise NotImplementedError
