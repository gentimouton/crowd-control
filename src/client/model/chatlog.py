
class ChatLog():
    
    def __init__(self):
        self.typedchars = []
        
    def add_char_typed(self, char):
        self.typedchars.append(char)
        
    def send_string_typed(self):
        # join is fast - see http://www.skymind.com/~ocrow/python_string/
        fullstr = ''.join(self.typedchars)
        self.typedchars = []
        return fullstr
