from client.config import config_get_fontsize, config_get_unfocusedbtn_bgcolor, \
    config_get_unfocusedinput_txtcolor, config_get_focusedbtn_bgcolor, \
    config_get_unfocusedbtn_txtcolor, config_get_unfocusedinput_bgcolor, \
    config_get_focusedinput_bgcolor, config_get_focusedbtn_txtcolor, \
    config_get_focusedinput_txtcolor, config_get_chatlog_txtcolor
from client.events_client import DownClickEvent, UpClickEvent, MoveMouseEvent, \
    UnicodeKeyPushedEvent, NonprintableKeyEvent, SubmitChat, ChatlogUpdatedEvent, \
    MdAddPlayerEvt, MPlayerLeftEvt, MNameChangedEvt, MMyNameChangedEvent, \
    MNameChangeFailEvt, MGameAdminEvt, MdHpsChangeEvt
from collections import deque
from pygame.font import Font
from pygame.locals import K_BACKSPACE, K_RETURN, RLEACCEL, SRCALPHA
from pygame.rect import Rect
from pygame.sprite import DirtySprite
from pygame.surface import Surface
import logging
import pygame


class Widget(DirtySprite):
    """ abstract class for other types of widgets """
    
    log = logging.getLogger('client')


    def __init__(self, evManager):
        DirtySprite.__init__(self)

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



    def update(self, duration):
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
        txtimg = txtimg.convert()
        textpos = txtimg.get_rect(centerx=self.image.get_width() / 2,
                                  centery=self.image.get_height() / 2)
        self.image.blit(txtimg, textpos)
        
        # self.dirty is set to 0 by LayeredDirty.update


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


    def update(self, duration):
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

        #self.dirty = 0



    def set_text(self, newtext):
        """ change the content of the text input field """
        self.text = newtext
        self.dirty = 1


    def submit_text(self):
        """ send the string typed, and reset the text input field """
        self.log.debug('Widget submit text: ' + self.text)
        ev = SubmitChat(self.text)
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
    
    def __init__(self, evManager, text, events_attrs=[], rect=None,
                 txtcolor=(255, 0, 0), bgcolor=None):
        
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
                
        self.txtcolor = txtcolor
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
        
        
    def update(self, duration):
        
        if self.dirty == 0:
            return
        
        # TODO: is bliting on existing surf faster than creating a new surface?
        size = self.rect.size
        txtcolor = self.txtcolor
        bgcolor = self.bgcolor
        if bgcolor: # opaque bg
            txtimg = self.font.render(self.text, True, txtcolor, bgcolor)
            txtimg = txtimg.convert()
            img = Surface(size)
            img.fill(bgcolor)
        else: # transparent bg
            txtimg = self.font.render(self.text, True, txtcolor)
            txtimg = txtimg.convert_alpha()
            img = Surface(size, SRCALPHA) # handle transparency
            img.fill((0, 0, 0, 0)) # 0 = transparent, 255 = opaque
        
        # center the txt inside its box
        ctr_y = size[1] / 2
        textpos = txtimg.get_rect(left=2, centery=ctr_y)
        img.blit(txtimg, textpos)
        self.image = img
        
        #self.dirty = 0
        
        
    

############################################################################
class PlayerListWidget(Widget):
    """ Display lines of text. Some events tell which lines should be removed. 
    Other events tell which lines should be added.
    """
    
    def __init__(self, evManager, numlines=3, rect=(0, 0, 100, 20),
                 txtcolor=(255, 0, 0), bgcolor=None):
        Widget.__init__(self, evManager)
        
        # When receiving an event containing text, 
        # add or remove that text to the widget's set of text lines to display.
        
        # addevents_attrs maps event classes to the text attr of events 
        # that add text to display.
        self.addevents_attrs = {MdAddPlayerEvt:'pname',
                                MNameChangedEvt:'newname',
                                MMyNameChangedEvent:'newname'}
        for evtClass in self.addevents_attrs:
            self._em.reg_cb(evtClass, self.on_addtextevent)
        
        # rmevents_attrs maps event classes to the text attributes of events 
        # that remove text to display.
        self.rmevents_attrs = {MPlayerLeftEvt: 'pname',
                               MNameChangedEvt:'oldname',
                               MMyNameChangedEvent:'oldname'}
        for evtClass in self.rmevents_attrs:
            self._em.reg_cb(evtClass, self.on_rmtextevent)
        
        self.texts = [] # Each text is a player name.
        
        # gfx
        self.font = Font(None, config_get_fontsize())
        self.rect = rect
        self.txtcolor = txtcolor
        self.bgcolor = bgcolor
        img = Surface(rect.size)
        if bgcolor:
            img.fill(bgcolor)
        else:
            img.set_alpha(0, RLEACCEL) # fully transparent
        self.image = img
        
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
            txtcol, bgcol = self.txtcolor, self.bgcolor
            txtwidget = TextLabelWidget(self._em, '', rect=newline_rect,
                                        txtcolor=txtcol, bgcolor=bgcol)
            # this empty text will be replaced when we shift all the texts upwards
            self.linewidgets.append(txtwidget)
        
        self.dirty = 1 # causes all text widgets to be updated
        
        
        
    def on_rmtextevent(self, event):
        """ remove the event's text from the current set of texts """
        evt_txt_attr = self.rmevents_attrs[event.__class__]
        txt = getattr(event, evt_txt_attr)
        try:
            self.texts.remove(txt)
        except ValueError: #txt was not present in self.texts
            self.log.warning('Tried to remove %s, but it was not in the widget.'
                             % txt)
            return
        # remove the most recently added line widget if there are less texts than line widgets 
        if len(self.texts) < len(self.linewidgets):
            self.linewidgets.pop()
        # refill all lines with text and reblit all line widgets
        self.dirty = 1
        
        
        
        
    def update(self, duration):
        """ update all the contained linewidgets
        TODO: check that it works with transparent bg
        """
        
        if self.dirty == 0:
            return
        
        # make the box
        size = self.rect.size
        bgcol = self.bgcolor
        if bgcol: # only display a bg img if bgcolor specified
            img = Surface(size)
            img.fill(bgcol)
            img = img.convert()
        else: # more or less transparent
            img = Surface(size, SRCALPHA) # handles transparency
            transparency = 50 # 0 = transparent, 255 = opaque
            img.fill((0, 0, 0, transparency))
            img = img.convert_alpha()
        
        # blit each line
        numelemts = min(len(self.texts), self.maxnumlines)
        for i in range(numelemts):
            wid = self.linewidgets[i]
            wid.set_text(self.texts[-i - 1])
            wid.update(duration)
            img.blit(wid.image, wid.rect)
            
        self.image = img
        #self.dirty = 0 # set by LayeredDirty
        
        


############################################################################


class ChatLogWidget(Widget):
    """ display chat messages """ 
    
    def __init__(self, evManager, numlines=3, rect=(0, 0, 100, 20),
                 txtcolor=(255, 0, 0), bgcolor=None):
        Widget.__init__(self, evManager)

        self._em.reg_cb(ChatlogUpdatedEvent, self.on_remotechat)
        self._em.reg_cb(MGameAdminEvt, self.on_gameadmin)
        self._em.reg_cb(MNameChangeFailEvt, self.on_namechangefail)
        self._em.reg_cb(MMyNameChangedEvent, self.on_namechangesuccess)
        self._em.reg_cb(MNameChangedEvt, self.on_namechangesuccess)
        self._em.reg_cb(MdHpsChangeEvt, self.on_updatehps)

        self.font = Font(None, config_get_fontsize())
        self.rect = rect
        size = rect.size
        self.txtcolor = txtcolor
        self.bgcolor = bgcolor
        if bgcolor: # completely opaque bg
            img = Surface(size)
            img.fill(self.bgcolor)
            img = img.convert()
        else: # more or less transparent
            img = Surface(self.rect.size, SRCALPHA) # handles transparency
            transparency = 50 # 0 = transparent, 255 = opaque
            img.fill((0, 0, 0, transparency)) # black
            img = img.convert_alpha()
        self.image = img
        
        self.maxnumlines = numlines
        self.linewidgets = deque(maxlen=numlines) # deque of TextLabelWidgets
        
        
        
    def on_remotechat(self, event):
        """ display a chat msg """
        linetxt = event.pname + ': ' + event.txt        
        self.addline(linetxt)
        
        
    def on_gameadmin(self, event):
        """ print in chatlog that the game has started """
        linetxt = event.pname + ' ' + event.cmd + ' the game' #game start or stop
        self.addline(linetxt)
        
        
        
    def on_namechangefail(self, event):
        """ The name the player wanted to change to was not accepted.
        Explain why. 
        """
        failname, reason = event.failname, event.reason
        linetxt = 'Can\'t change to ' + failname + ' : ' + reason 
        self.addline(linetxt)
        
        
    def on_namechangesuccess(self, event):
        """ Notify that the player changed name. """
        oldname, newname = event.oldname, event.newname
        linetxt = '%s -> %s' % (oldname, newname)
        self.addline(linetxt)
        
        
    def on_updatehps(self, event):
        """ notify that a char changed hps. """
        char = event.charactor
        linetxt = '%s now has %d/%d hp' % (char.name, char.hp, char.maxhp)
        self.addline(linetxt)
            
            
    def addline(self, linetxt):
        """ If there's room, add a line on top, 
        and then shift all widget texts upwards.
        If there's no room, only shift the texts upwards,
        no need to add new widgets. 
        """
        
        if len(self.linewidgets) < self.maxnumlines: 
            # there's room to add another text widget on top of existing ones
            lines_from_top = self.maxnumlines - len(self.linewidgets) - 1 
            line_height = self.rect.height / self.maxnumlines
            newline_top = lines_from_top * line_height
            newline_rect = Rect(0, newline_top, self.rect.width, line_height)
            tcol, bgcol = self.txtcolor, self.bgcolor
            txtwidget = TextLabelWidget(self._em, '', rect=newline_rect,
                                        txtcolor=tcol, bgcolor=bgcol)
            # this empty text will be replaced when we shift all the texts upwards
            self.linewidgets.append(txtwidget)
        
        # shift the widgets' texts to their upper neighbor
        nextlinetxt = linetxt
        for wid in self.linewidgets:
            # swap nextlinetxt with widget's text
            tmptxt = wid.get_text()
            wid.set_text(nextlinetxt) #makes the widget dirty  
            nextlinetxt = tmptxt
        
        self.log.debug('Chatlog widget printed line: ' + linetxt)
        self.dirty = 1 # causes all linewidgets to be updated
        
        
    def update(self, duration):
        """ update all the contained linewidgets.
        Return right away if no text has changed.
        """
        
        if self.dirty == 0: # no new text has been added
            return
        
        # make the box
        size = self.rect.size
        bgcolor = self.bgcolor
        if bgcolor: # completely opaque bg
            img = Surface(size)
            img.fill(self.bgcolor)
            img = img.convert()
        else: # more or less transparent
            img = Surface(size, SRCALPHA) # handles transparency
            transparency = 50 # 0 = transparent, 255 = opaque
            img.fill((0, 0, 0, transparency)) # black
            img = img.convert_alpha()
        
        # blit each line
        for wid in self.linewidgets:
            wid.update(duration)
            img.blit(wid.image, wid.rect)

        self.image = img
        self.dirty = 0
        
        

