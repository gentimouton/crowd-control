
class ChatLog():
    
    def __init__(self):
        self.typedchars = []
        self.lastmsg = {}
        self.helloed = False # whether the last msg on chat is my hello
    
    ######### LOCAL TYPING #############
        
    def add_char_typed(self, char):
        self.typedchars.append(char)
        
    def send_string_typed(self):
        # join is fast - see http://www.skymind.com/~ocrow/python_string/
        fullstr = ''.join(self.typedchars)
        self.typedchars = []
        self.helloed = False
        return fullstr

    ######### CHAT WINDOW ########
    
    def someone_said(self, author, txt):
        self.helloed = False
        self.lastmsg = {'author': author, 'txt':txt}
        
    def get_last_msg(self):
        return self.lastmsg
    
    def sent_hello(self):
        self.helloed = True
        
    def is_helloed(self):
        """ getter for the renderer """
        return self.helloed