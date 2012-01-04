from client.config import config_get_my_name

class MainController():
    
    def __init__(self, chatlog, world):
        self.chatlog = chatlog
        self.world = world

    def setnwctrler(self, nwc):
        self.nwctrler = nwc
    
    # CHAT
        
    def add_char_typed(self, char):
        self.chatlog.add_char_typed(char)
    
    def backspace(self):
        self.chatlog.remove_char_typed()
        
    def validate(self):
        fullstr = self.chatlog.end_of_line()
        # don't send empty strings
        if len(fullstr) > 0: 
            self.nwctrler.send_chat(fullstr)

    def someone_said(self, author, txt):
        self.chatlog.someone_said(author, txt)
    
    
    # MOVEMENT
    
    def set_startpos(self,pos):
        ''' should only happen at start, not during the game '''
        self.world.set_start_pos(pos)    
        
    ''' TODO: factorize go_up and go_down together into movement('up'/'down') '''
    
    def go_up(self):
        newpos = self.world.i_go_up()
        if newpos: # legal move
            self.nwctrler.send_move(newpos)
        # TODO: send 'i'm moving towards newpos' to the server
    def go_down(self):
        newpos = self.world.i_go_down()
        if newpos: # legal move
            self.nwctrler.send_move(newpos)
        # TODO: send msg to server
    
    def someone_moved(self, author, dest):
        self.world.someone_moved(author, dest)

    
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
        self.world.set_myname(newname)
        self.nwctrler.ask_for_name_change(config_get_my_name())


    def someone_changed_name(self, oldname, newname):
        if self.chatlog.get_my_name() == oldname:
            self.i_changed_name(newname)
            txt = 'You are now known as ' + newname
            txt = txt + ' (old name: ' + oldname + ').'
            self.chatlog.someone_said('server', txt)
        else:
            txt = oldname + ' is now known as ' + newname
            self.chatlog.someone_said('server', txt)
    
    def init_players(self, onlineppl):
        self.world.init_playerlist(onlineppl)
    
    # HUD callbacks
    
    def greenboxclick(self):
        self.nwctrler.send_chat("* clicked on green button! *")
        self.chatlog.sent_hello()
        pass
