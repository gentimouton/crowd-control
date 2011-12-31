from collections import deque

class ChatLog():
    
    def __init__(self):
        self.typedchars = []
        self.log = deque() #double-ended queue
        self.maxloglen = 5 #chat history of 5 msgs max
        self.helloed = False # whether the last msg on chat is my hello
        # TODO: remove this whole helloed crap
    
    ######### my local typing of a line #############
        
    def add_char_typed(self, char):
        self.typedchars.append(char)
        
    def remove_char_typed(self):
        if len(self.typedchars) > 0:
            self.typedchars.pop()
        
    def end_of_line(self):
        """ put all the characters together to form a line """
        # join is fast - see http://www.skymind.com/~ocrow/python_string/
        line = ''.join(self.typedchars)
        if len(line) > 0:    
            self.typedchars = []
            self.helloed = False
        return line

    ######### chat log ########
    
    def someone_said(self, author, txt):
        self.helloed = False
        msg = {'author': author, 'txt':txt}
        self.log.appendleft(msg)
        if len(self.log) > self.maxloglen:
            self.log.pop()
    
    def get_complete_log(self):
        return self.log
    
    # TODO: remove this helloed crap
    def sent_hello(self):
        self.helloed = True
        
    def is_helloed(self):
        """ getter for the renderer """
        return self.helloed
