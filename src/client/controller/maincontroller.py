
class MainController():
    
    def __init__(self, chatlog):
        self.chatlog = chatlog

    def setnwctrler(self, nwc):
        self.nwctrler = nwc
    
    # CHAT
        
    def add_char_typed(self, char):
        self.chatlog.add_char_typed(char)
    
    def remove_char_typed(self):
        self.chatlog.remove_char_typed()
        
    def send_string_typed(self):
        fullstr = self.chatlog.end_of_line()
        # don't send empty strings
        if len(fullstr) > 0: 
            self.nwctrler.send_chat(fullstr)

    def someone_said(self, author, txt):
        self.chatlog.someone_said(author, txt)
    

    
    # connection, disconnection and name change
    
    def someone_admin(self, name, actiontype):
        txt = name + ' ' + actiontype
        self.chatlog.someone_said('server', txt)

    ''' connection and name changing protocol:
    When the server end detects a client connection, 
    the server sends to the client a greeting containing that client's 
    temporary name. Received greets first triggers 
    i_changed_name(server-given-name), and then it asks for the client's
    preferred name to the server. The client knows if the server accepted the
    name change by a server broadcast which triggers 
    someone_changed_name(oldname=server-given-name) '''

    def i_changed_name(self, newname):
        self.chatlog.set_my_name(newname)

    def someone_changed_name(self, oldname, newname):
        if self.chatlog.get_my_name() == oldname:
            self.i_changed_name(newname)
            txt = 'You are now known as ' + newname
            txt = txt + ' (old name: ' + oldname + ').'
            self.chatlog.someone_said('server', txt)
        else:
            txt = oldname + ' is now known as ' + newname
            self.chatlog.someone_said('server', txt)
        
    
    # HUD callbacks
    
    def greenboxclick(self):
        self.nwctrler.send_chat("* clicked on green button! *")
        self.chatlog.sent_hello()
        pass
        
        
