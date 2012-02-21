from client.config import config_get_fontsize, config_get_unfocusedbtn_bgcolor, \
    config_get_unfocusedinput_txtcolor, config_get_focusedbtn_bgcolor, \
    config_get_unfocusedbtn_txtcolor, config_get_unfocusedinput_bgcolor, \
    config_get_focusedinput_bgcolor, config_get_focusedbtn_txtcolor, \
    config_get_focusedinput_txtcolor, config_get_txtlabel_txtcolor, \
    config_get_txtlabel_bgcolor, config_get_chatlog_txtcolor, \
    config_get_chatlog_bgcolor
from client.events_client import DownClickEvent, UpClickEvent, MoveMouseEvent, \
    UnicodeKeyPushedEvent, NonprintableKeyEvent, SendChatEvent, ChatlogUpdatedEvent, \
    NwRecGameStartEvt, NwRecGreetEvt, NwRecPlayerJoinEvt, NwRecNameChangeEvt, \
    NwRecPlayerLeft, MdAddPlayerEvt, MyNameChangedEvent
from collections import deque
from pygame.font import Font
from pygame.locals import K_BACKSPACE, K_RETURN
from pygame.rect import Rect
from pygame.sprite import Sprite
from pygame.surface import Surface
import logging
import pygame


class Widget(Sprite):
    """ abstract class for other types of widgets """
    
    log = logging.getLogger('client')


    def __init__(self, evManager):
        Sprite.__init__(self)

        self._em = evManager

        self.focused = False
        self.dirty = 1


    def set_focus(self, val):
        self.focused = val
        self.dirty = 1


            
            
            

#############################################################################



class ButtonWidget(Widget):
    """ clickable widget with text in it """
    
    def __init__(self, evManager, text, rect=None,
                 onDownClickEvent=None, onUpClickEvent=None,
                 onMouseMoveOutEvent=None):
        Widget.__init__(self, evManager) 
        # Widget init sets dirty to true, hence the actual text rendering 
        # will be done in ButtonWidget.update(), called by the view renderer.
        
        self._em.reg_cb(DownClickEvent, self.on_downclick)
        self._em.reg_cb(UpClickEvent, self.on_upclick)
        self._em.reg_cb(MoveMouseEvent, self.on_mousemove)
        
        # the events to be triggered when the button is clicked or mouse moved
        self.onDownClickEvent = onDownClickEvent
        self.onUpClickEvent = onUpClickEvent
        self.onMouseMoveOutEvent = onMouseMoveOutEvent
        
        self.text = text
        self.font = Font(None, config_get_fontsize()) #default font, 40 pixels high
        
        if rect:
            self.rect = rect
            self.image = Surface(self.rect.size) #container size from specified rect
            # if txtimg does not fit in rect, it'll get cut (good thing) 
        else:
            txtimg = self.font.render(self.text, True, (0, 0, 0))
            self.rect = txtimg.get_rect()
            self.image = Surface(self.rect.size) #container size from rendered text
            # if txt changes, the size of the button will stay the same



    def update(self):
        if self.dirty == 0:
            return

        if self.focused:
            color = config_get_focusedbtn_txtcolor()
            bgcolor = config_get_focusedbtn_bgcolor() 
        else:
            color = config_get_unfocusedbtn_txtcolor()
            bgcolor = config_get_unfocusedbtn_bgcolor() 
                
        # TODO: is bliting on existing faster than creating a new surface?
        self.image = Surface(self.rect.size) #rectangle container for the text
        self.image.fill(bgcolor)
        txtimg = self.font.render(self.text, True, color)
        textpos = txtimg.get_rect(centerx=self.image.get_width() / 2,
                                  centery=self.image.get_height() / 2)
        self.image.blit(txtimg, textpos)
        
        self.dirty = 0


    def on_downclick(self, event):
        """ button down focuses and triggers eventual behavior """
        
        if self.rect.collidepoint(event.pos):
            self.dirty = 1 
            self.set_focus(True)
                
            if self.onDownClickEvent:
                self._em.post(self.onDownClickEvent)
            
                      
    def on_upclick(self, event):
        """ button up loses focus and triggers eventual behavior """
        if self.rect.collidepoint(event.pos):
            if self.focused:
                self.dirty = 1
                self.set_focus(False)
                
                if self.onUpClickEvent:
                    self.log.debug('Clicked on button widget ' + self.text)
                    self._em.post(self.onUpClickEvent)

        
    def on_mousemove(self, event):
        """ if focused, lose focus when the mouse moves out """ 
        if self.rect.collidepoint(event.pos): #mouse moved in
            pass
        else: # mouse moved out
            if self.focused:
                if not self.onMouseMoveOutEvent: #default behavior
                    self.set_focus(False)
            
            
        



#############################################################################


class InputFieldWidget(Widget):
    """ widget where the user can enter text. 
    The widget loses focus when the user clicks somewhere else. 
    """
        
    def __init__(self, evManager, rect=None):
        Widget.__init__(self, evManager)
        # Widget init sets dirty to true, hence the actual rendering 
        # will be done in InputFieldWidget.update(), called by the view renderer.

        self._em.reg_cb(NonprintableKeyEvent, self.on_invisiblekeypushed)    
        self._em.reg_cb(UnicodeKeyPushedEvent, self.on_visiblekeypushed)    
        self._em.reg_cb(DownClickEvent, self.on_downclick)    

        self.text = ''
        self.font = Font(None, config_get_fontsize())
        
        if rect:
            self.rect = rect
        else:
            self.rect = Rect((0, 0), (100, config_get_fontsize() + 4)) 
            #100px = default width,
            # 25px = font height, 4px = 1 px for each of border-bottom, 
            # padding bottom, padding top, and border top.  
        
        # rectangle to be drawn around the box as border 
        border_rect = Rect((0, 0), self.rect.size)
        # draw and store unfocused empty box
        emptyboxImg = Surface(self.rect.size)
        self.unfocused_bgcolor = config_get_unfocusedinput_bgcolor() 
        self.unfocused_txtcolor = config_get_unfocusedinput_txtcolor()
        emptyboxImg.fill(self.unfocused_bgcolor)
        pygame.draw.rect(emptyboxImg, self.unfocused_txtcolor, border_rect, 2)
        self.unfocused_emptyboxImg = emptyboxImg.convert_alpha()
        self.image = emptyboxImg
        # draw and store focused empty box
        emptyboxImg = Surface(self.rect.size)
        self.focused_bgcolor = config_get_focusedinput_bgcolor()
        self.focused_txtcolor = config_get_focusedinput_txtcolor() 
        emptyboxImg.fill(self.focused_bgcolor)
        pygame.draw.rect(emptyboxImg, self.focused_txtcolor, border_rect, 2)
        self.focused_emptyboxImg = emptyboxImg.convert_alpha()
        
        self.textPos = (4, 2) # 4px padding-left and 2px padding-top 


    def update(self):
        """ render the text in the box """
        if self.dirty == 0:
            return

        text = self.text
        if self.focused:
            text += '|'
            txtcolor = self.focused_txtcolor
            emptyboximg = self.focused_emptyboxImg
        else:
            txtcolor = self.unfocused_txtcolor
            emptyboximg = self.unfocused_emptyboxImg
                        
        textImg = self.font.render(text, True, txtcolor)
        # cover the previous img instead of creating a new one
        # TODO: is bliting on existing faster than creating a new surface?
        self.image.blit(emptyboximg, (0, 0))
        self.image.blit(textImg, self.textPos)

        self.dirty = 0



    def set_text(self, newtext):
        """ change the content of the text input field """
        self.text = newtext
        self.dirty = 1


    def submit_text(self):
        """ send the string typed, and reset the text input field """
        self.log.debug('Widget submit text: ' + self.text)
        ev = SendChatEvent(self.text)
        self.set_text('')
        self._em.post(ev)
        

    ###### CALLBACKS 
    
     
    def on_downclick(self, event):
        """ Get focus if clicked, lose focus if something else is clicked """
        if self.rect.collidepoint(event.pos): # box was clicked
            self.set_focus(True)
            self.dirty = 1
        elif self.focused: #user clicked on something else
            self.set_focus(False)

    
    def on_invisiblekeypushed(self, event):
        """ Add/remove characters and 'submit' the string."""
        if self.focused:
            if event.key == K_BACKSPACE:# erase last character
                newtxt = self.text[:-1]
                self.set_text(newtxt)
            elif event.key == K_RETURN: #submit non-empty string
                if self.text:
                    self.submit_text()
                else: # lose focus
                    self.set_focus(False)
                
        else: # not focused => grab focus if K_RETURN pushed
            if event.key == K_RETURN:
                self.set_focus(True)
        
    
    def on_visiblekeypushed(self, event):
        """ Type characters inside the box. """
        if self.focused:
            # add visible characters at the end of existing string
            newtxt = self.text + event.unicode
            self.set_text(newtxt)
            


############################################################################


class TextLabelWidget(Widget):
    """ display static text """ 
    
    def __init__(self, evManager, text, events_attrs=None, rect=None,
                 txtcolor=None, bgcolor=None):
        
        Widget.__init__(self, evManager)
            
        # When receiving an event containing text, 
        # replace self.text by that event's text.
        # events_attrs maps event classes to event text attributes. 
        self.events_attrs = events_attrs
        if events_attrs:
            for evtClass in events_attrs:
                self._em.reg_cb(evtClass, self.on_textevent)
        
        # gfx
        self.font = Font(None, config_get_fontsize())
        if rect:
            self.rect = rect
        else:
            self.rect = Rect((0, 0), (100, config_get_fontsize() + 4)) 
            #default width = 100px,
            # 4px from 1px each of  border bottom,
            # padding bottom, padding top, and border top 
        
        
        if not txtcolor:
            txtcolor = config_get_txtlabel_txtcolor()
        self.txtcolor = txtcolor 

        if not bgcolor:
            bgcolor = config_get_txtlabel_bgcolor()
        self.bgcolor = bgcolor

        self.text = text
        self.image = Surface(self.rect.size)
        

    def set_text(self, text):
        self.text = text
        self.dirty = 1

    def get_text(self):
        return self.text
    

    def on_textevent(self, event):
        """ Widget has to change its text. """        
        evt_txt_attr = self.events_attrs[event.__class__]
        txt = getattr(event, evt_txt_attr)
        self.set_text(txt)
        
        
    def update(self):
        if self.dirty == 0:
            return
        
        # TODO: is bliting on existing surf faster than creating a new surface?
        self.image = Surface(self.rect.size) #rectangle container for the text
        self.image.fill(self.bgcolor)
        txtimg = self.font.render(self.text, True, self.txtcolor)
        textpos = txtimg.get_rect(left=2,
                                  centery=self.image.get_height() / 2)
        self.image.blit(txtimg, textpos)
        
        self.dirty = 0
        
        
    

############################################################################
class PlayerListWidget(Widget):
    """ Display lines of text. Some events tell which lines should be removed. 
    Other events tell which lines should be added.
    """
    
    def __init__(self, evManager, numlines=3, rect=None):
        Widget.__init__(self, evManager)
        
        # When receiving an event containing text, 
        # add or remove that text to the widget's set of text lines to display.
        
        # addevents_attrs maps event classes to the text attr of events 
        # that add text to display.
        self.addevents_attrs = {MdAddPlayerEvt:'pname',  
                                NwRecNameChangeEvt:'newname'}
        for evtClass in self.addevents_attrs:
            self._em.reg_cb(evtClass, self.on_addtextevent)
        
        # rmevents_attrs maps event classes to the text attributes of events 
        # that remove text to display.
        self.rmevents_attrs = {NwRecPlayerLeft: 'pname', 
                               NwRecNameChangeEvt:'oldname'}
        for evtClass in self.rmevents_attrs:
            self._em.reg_cb(evtClass, self.on_rmtextevent)
        
        self.texts = [] # Each text is a player name.
        
        # gfx
        self.font = Font(None, config_get_fontsize())
        if rect:
            self.rect = rect
        else:
            self.rect = Rect((0, 0), (100, config_get_fontsize() + 4)) 
            #default width = 100px,
            # 4px from 1px each of  border bottom,
            # padding bottom, padding top, and border top 
        
        self.txtcolor = config_get_chatlog_txtcolor()
        self.bgcolor = config_get_chatlog_bgcolor()
        self.image = Surface(self.rect.size).fill(self.bgcolor)
        
        self.maxnumlines = numlines
        self.linewidgets = deque(maxlen=numlines) # deque of TextLabelWidgets
        
        
        

    def on_addtextevent(self, event):
        """ add the event's text to the current set of texts """
        evt_txt_attr = self.addevents_attrs[event.__class__]
        linetxt = getattr(event, evt_txt_attr)
        self.texts.append(linetxt) # no need to check if txt was already in 
        
        # add lines from the top
        if len(self.linewidgets) < self.maxnumlines: 
            # there's room to add another text widget under the existing ones
            lines_from_top = len(self.linewidgets)
            line_height = self.rect.height / self.maxnumlines
            newline_top = lines_from_top * line_height
            newline_rect = Rect(0, newline_top, self.rect.width, line_height)
            txtwidget = TextLabelWidget(self._em, '', rect=newline_rect)
            # this empty text will be replaced when we shift all the texts upwards
            self.linewidgets.append(txtwidget)
        
        self.dirty = 1 # causes all text widgets to be updated
        
        
        
    def on_rmtextevent(self, event):
        """ remove the event's text from the current set of texts """
        evt_txt_attr = self.rmevents_attrs[event.__class__]
        txt = getattr(event, evt_txt_attr)
        try:
            self.texts.remove(txt)
        except ValueError:
            self.log.warning('Tried to remove ' + txt + ', but it was not in the widget.')
            return
        # remove the most recently added line widget if there are less texts than line widgets 
        if len(self.texts) < len(self.linewidgets):
            self.linewidgets.pop()
        # refill all lines with text and reblit all line widgets
        self.dirty = 1
        
        
        
        
    def update(self):
        """ update all the contained linewidgets """
        
        if self.dirty == 0:
            return
        
        self.image = Surface(self.rect.size) 
        self.image.fill(self.bgcolor)
        
        numelemts = min(len(self.texts), self.maxnumlines)
        for i in range(numelemts):
            wid = self.linewidgets[i]
            wid.set_text(self.texts[-i - 1])
            wid.update()
            self.image.blit(wid.image, wid.rect)

        self.dirty = 0
        
        


############################################################################


class ChatLogWidget(Widget):
    """ display chat messages """ 
    
    def __init__(self, evManager, numlines=3, rect=None):
        Widget.__init__(self, evManager)

        self._em.reg_cb(ChatlogUpdatedEvent, self.on_chatmsg)
        self._em.reg_cb(NwRecGameStartEvt, self.on_game_start)

        self.font = Font(None, config_get_fontsize())
        if rect:
            self.rect = rect
        else:
            self.rect = Rect((0, 0), (100, (config_get_fontsize() + 4) * numlines)) 
            #100px = default width,
            #4px = 1px for each of border bottom,
            # padding bottom, padding top, and border top, 
        
        self.txtcolor = config_get_chatlog_txtcolor()
        self.bgcolor = config_get_chatlog_bgcolor()
        self.image = Surface(self.rect.size).fill(self.bgcolor)
        
        self.maxnumlines = numlines
        self.linewidgets = deque(maxlen=numlines) # deque of TextLabelWidgets
        
        
        
    def on_chatmsg(self, event):
        """ display a chat msg """
        linetxt = event.pname + ': ' + event.txt        
        self.log.debug('Chatlog widget printed chat line: ' + linetxt)
        self.addline(linetxt)
        
        
    def on_game_start(self, event):
        """ print in chatlog that the game has started """
        linetxt = '-- Game started by ' + event.pname
        self.log.debug('Chatlog widget printed game line: ' + linetxt)
        self.addline(linetxt)
        
        
    def addline(self, linetxt):
        """ If there's room, add a line on top, and then shift all widget texts upwards.
        If there's no room, only shift the texts upwards (don't add new widgets). 
        """
        
        if len(self.linewidgets) < self.maxnumlines: 
            # there's room to add another text widget on top of existing ones
            lines_from_top = self.maxnumlines - len(self.linewidgets) -1 
            line_height = self.rect.height / self.maxnumlines
            newline_top = lines_from_top * line_height
            newline_rect = Rect(0, newline_top, self.rect.width, line_height)
            txtwidget = TextLabelWidget(self._em, '', rect=newline_rect)
            # this empty text will be replaced when we shift all the texts upwards
            self.linewidgets.append(txtwidget)
        
        # shift the widgets' texts to their upper neighbor
        nextlinetxt = linetxt
        for wid in self.linewidgets:
            # swap nextlinetxt with widget's text
            tmptxt = wid.get_text()
            wid.set_text(nextlinetxt) #makes the widget dirty  
            nextlinetxt = tmptxt
        
        self.dirty = 1 # causes all linewidgets to be updated
        
        
    def update(self):
        """ update all the contained linewidgets """
        
        if self.dirty == 0:
            return
        
        self.image = Surface(self.rect.size) 
        self.image.fill(self.bgcolor)
        
        for wid in self.linewidgets:
            wid.update()
            self.image.blit(wid.image, wid.rect)

        self.dirty = 0
        
        

