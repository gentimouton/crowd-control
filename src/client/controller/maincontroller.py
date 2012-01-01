
class MainController():
    
    def __init__(self, chatlog):
        self.chatlog = chatlog

    def setnwctrler(self, nwc):
        self.nwctrler = nwc
        
    def add_char_typed(self, char):
        self.chatlog.add_char_typed(char)
    
    def remove_char_typed(self):
        self.chatlog.remove_char_typed()
        
    def send_string_typed(self):
        fullstr = self.chatlog.end_of_line()
        # don't send empty strings
        if len(fullstr) > 0: 
            self.nwctrler.send_chat(fullstr)
    
    
    # network controller callbacks
    
    def someone_said(self, author, txt):
        self.chatlog.someone_said(author, txt)
    
    def someone_admin(self, name, actiontype):
        print("admin:", name, actiontype)
            
    # view controller callbacks
    
    def greenboxclick(self):
        self.nwctrler.send_chat("* clicked on green button! *")
        self.chatlog.sent_hello()
        pass
        
        
