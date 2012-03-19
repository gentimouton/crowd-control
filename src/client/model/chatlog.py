''' 
The chatlog is part of the model. It is only updated in a local lag mode:
- it is not updated directly when the local client types something in
- it is only updated when the server broadcast the message.
This ensures that all messages in the client chatbox 
are displayed in the same order as they were received and treated on the server.
After all, a 1-sec lag is (hopefully) the max that's going to happen,
and chatters can accept a 1-sec delay for their msg to appear.
'''

from client.events_client import NwRcvChatEvt, ChatlogUpdatedEvent, SubmitChat, \
    SendChatEvt
from collections import deque


class ChatLog():
    """ store all that deals with the chat window """
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(NwRcvChatEvt, self.on_remotechat)
        self._em.reg_cb(SubmitChat, self.on_submitchat)
        
        #double-ended queue to remember the most recent 30 messages
        self.chatlog = deque(maxlen=30) 
            
    
    
    def on_remotechat(self, event):
        """ Add a message to the chatlog.
        If full, remove oldest message. 
        Anyway, notify the view.
        """
        author, txt = event.pname, event.txt
        msg = {'pname':author, 'text':txt}
        self.chatlog.appendleft(msg) #will remove oldest msg automatically
        
        # tell the view/chatbox widget to display it 
        ev = ChatlogUpdatedEvent(author, txt)
        self._em.post(ev)


    def on_submitchat(self, event):
        """ Widget or input controller wants to send text to server """
        
        # TODO: FT check if user enters a local command (e.g. /quit or /nofx)
        # and send appropriate event (e.g. QuitEvent)
        
        txt = event.txt
        ev = SendChatEvt(txt) # send to server
        self._em.post(ev)
