''' 
The chatlog data is only updated in a local lag mode:
- it is not updated directly when the local client types something in
- it is only updated when the server broadcast the message.
This ensures that all messages in the client chatbox 
are displayed in the same order as they were received and treated on the server.
After all, a 1-sec lag is (hopefully) the max that's going to happen,
and chatters can accept a 1-sec delay for their msg to appear.
'''

from client.events_client import NwRcvChatEvt, ChatlogUpdatedEvent
from collections import deque


class ChatLog():
    """ store all that deals with the chat window """
    
    def __init__(self, evManager):
        self._em = evManager
        self._em.reg_cb(NwRcvChatEvt, self.add_chatmsg)
        
        #double-ended queue to remember the most recent 30 messages
        self.chatlog = deque(maxlen=30) 
            
    
    
    def add_chatmsg(self, event):
        """ Add a message to the chatlog.
        If full, remove oldest message. 
        """
        author, txt = event.pname, event.txt
        msg = {'pname':author, 'text':txt}
        self.chatlog.appendleft(msg) #will remove oldest msg automatically
        
        # tell the view/chatbox widget to display it 
        ev = ChatlogUpdatedEvent(author, txt)
        self._em.post(ev)


    
