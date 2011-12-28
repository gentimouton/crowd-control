
class MainController():
    
    def __init__(self, chatlog):
        self.chatlog = chatlog

    def setnwctrler(self, nwc):
        self.nwctrler = nwc
        
    def add_char_typed(self, char):
        self.chatlog.add_char_typed(char)
    
    def send_string_typed(self):
        fullstr = self.chatlog.send_string_typed() 
        self.nwctrler.send_chat(fullstr)
    
    def someone_said(self, author, txt):
        self.chatlog.someone_said(author, txt)
            
    def greenboxclick(self):
        # TODO: implement the viewctrler-to-mainctrler logic
        pass
        
        