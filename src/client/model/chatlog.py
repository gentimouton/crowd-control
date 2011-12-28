
class ChatLog():
    
    def __init__(self):
        self.typedchars = []
        self.lastmsg = {}
    
    ######### LOCAL TYPING #############
        
    def add_char_typed(self, char):
        self.typedchars.append(char)
        
    def send_string_typed(self):
        # join is fast - see http://www.skymind.com/~ocrow/python_string/
        fullstr = ''.join(self.typedchars)
        self.typedchars = []
        return fullstr

    ######### FUL CHAT WINDOW ########
    
    def someone_said(self, author, txt):
        self.lastmsg = {'author': author, 'txt':txt}
        
    def get_last_msg(self):
        return self.lastmsg