from client2.events_client import DownClickEvent, UpClickEvent, MoveMouseEvent, \
    UnicodeKeyPushedEvent, NonprintableKeyEvent, SendChatEvent, ChatlogUpdatedEvent
from pygame.font import Font
from pygame.locals import K_BACKSPACE, K_RETURN
from pygame.rect import Rect
from pygame.sprite import Sprite
from pygame.surface import Surface
import pygame
from collections import deque


class Widget(Sprite):
    """ abstract class for other types of widgets """
    
    def __init__(self, evManager):
        Sprite.__init__(self)

        self.evManager = evManager
        self.evManager.register_listener(self)

        self.focused = False
        self.dirty = 1


    def set_focus(self, val):
        self.focused = val
        self.dirty = 1


    def notify(self, event):
        pass
            
            
            

#############################################################################



class ButtonWidget(Widget):
    """ clickable widget with text in it """
    
    def __init__(self, evManager, text, rect=None,
                 onDownClickEvent=None, onUpClickEvent=None,
                 onMouseMoveOutEvent=None):
        Widget.__init__(self, evManager) 
        # Widget init sets dirty to true, hence the actual text rendering 
        # will be done in ButtonWidget.update(), called by the view renderer.
        
        self.text = text
        self.font = Font(None, 40) #default font, 40 pixels high
        
        if rect:
            self.rect = rect
            self.image = Surface(self.rect.size) #container size from specified rect
            # if txtimg does not fit in rect, it'll get cut (good thing) 
        else:
            txtimg = self.font.render(self.text, True, (0, 0, 0))
            self.rect = txtimg.get_rect()
            self.image = Surface(self.rect.size) #container size from rendered text
            # if txt changes, the size of the button will stay the same

        # the event to be triggered when the button is clicked or mouse moved
        self.onUpClickEvent = onUpClickEvent
        self.onDownClickEvent = onDownClickEvent
        self.onMouseMoveOutEvent = onMouseMoveOutEvent


    def update(self):
        if self.dirty == 0:
            return

        if self.focused:
            color = (255, 0, 0) #txt is red when widget is focused
            bgcolor = (100, 100, 200)
        else:
            color = (0, 0, 255) #blue when not focused
            bgcolor = (100, 100, 0)
        
        # TODO: is bliting on existing faster than creating a new surface?
        self.image = Surface(self.rect.size) #rectangle container for the text
        self.image.fill(bgcolor)
        txtimg = self.font.render(self.text, True, color)
        textpos = txtimg.get_rect(centerx=self.image.get_width() / 2,
                                  centery=self.image.get_height() / 2)
        self.image.blit(txtimg, textpos)
        
        self.dirty = 0


    def ondownclick(self):
        """ button down focuses and triggers eventual behavior """
        self.dirty = 1 
        self.set_focus(True)
        
        if self.onDownClickEvent:
            self.evManager.post(self.onDownClickEvent)
            
                      
    def onupclick(self):
        """ button up loses focus and triggers eventual behavior """
        if self.focused:
            self.dirty = 1
            self.set_focus(False)
            
            if self.onUpClickEvent:
                self.evManager.post(self.onUpClickEvent)


    def onmousemovein(self):
        pass
    
    
    def onmousemoveout(self):
        """ if focused, lose focus when the mouse moves out """ 
        if self.focused:
            if not self.onMouseMoveOutEvent: #default behavior
                self.set_focus(False)
        
        
    def notify(self, event):
        if isinstance(event, DownClickEvent):
            if self.rect.collidepoint(event.pos):
                self.ondownclick()
        elif isinstance(event, UpClickEvent):
            if self.rect.collidepoint(event.pos):
                self.onupclick()
        elif isinstance(event, MoveMouseEvent):
            if self.rect.collidepoint(event.pos):
                self.onmousemovein()
            else:
                self.onmousemoveout()
                
        Widget.notify(self, event)






#############################################################################


class InputFieldWidget(Widget):
    """ widget where the user can enter text. 
    The widget loses focus when the user clicks somewhere else. 
    TODO: when focused, K_ENTER should do a 'submit' of some sort, and unfocus
    """
        
    def __init__(self, evManager, rect=None):
        Widget.__init__(self, evManager)
        # Widget init sets dirty to true, hence the actual rendering 
        # will be done in InputFieldWidget.update(), called by the view renderer.

        self.text = ''
        self.font = Font(None, 22)
        
        if rect:
            self.rect = rect
        else:
            self.rect = Rect((0, 0), (100, 22 + 4)) #100px = default width,
            # 25px = font height, 4px = 1 px for each of border-bottom, 
            # padding bottom, padding top, and border top.  
        
        # rectangle to be drawn around the box as border 
        border_rect = Rect((0, 0), self.rect.size)
        # draw and store unfocused empty box
        emptyboxImg = Surface(self.rect.size)
        self.unfocused_bgcolor = (111, 111, 111) #grey
        self.unfocused_txtcolor = (255, 255, 255) #white
        emptyboxImg.fill(self.unfocused_bgcolor)
        pygame.draw.rect(emptyboxImg, self.unfocused_txtcolor, border_rect, 2)
        self.unfocused_emptyboxImg = emptyboxImg.convert_alpha()
        self.image = emptyboxImg
        # draw and store focused empty box
        emptyboxImg = Surface(self.rect.size)
        self.focused_bgcolor = (255, 255, 255) #white
        self.focused_txtcolor = (0, 0, 0) #black
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


    def ondownclick(self):
        """ when down click, focus widget """
        self.set_focus(True)
        self.dirty = 1


    def set_text(self, newtext):
        """ change the content of the text input field """
        self.text = newtext
        self.dirty = 1


    def submit_text(self):
        """ send the string typed, and reset the text input field """
        ev = SendChatEvent(self.text)
        self.set_text('')
        self.evManager.post(ev)
        
        
    def notify(self, event):
        # get focus if clicked, lose focus if something else is clicked
        if isinstance(event, DownClickEvent): 
            if self.rect.collidepoint(event.pos):
                self.ondownclick()
            elif self.focused: #user clicked on something else
                self.set_focus(False)

        # add/remove characters and 'submit' the string
        elif isinstance(event, UnicodeKeyPushedEvent) and self.focused:
            # add visible characters at the end of existing string
            newtxt = self.text + event.unicode
            self.set_text(newtxt)
        elif isinstance(event, NonprintableKeyEvent) and self.focused:
            if event.key == K_BACKSPACE:# erase last character
                newtxt = self.text[:(len(self.text) - 1)]
                self.set_text(newtxt)
            elif event.key == K_RETURN: #submit string
                self.submit_text()
            
        Widget.notify(self, event)



############################################################################


class TextLabelWidget(Widget):
    """ display static text """ 
    
    def __init__(self, evManager, text, rect=None, txtcolor=(255, 255, 0),
                 bgcolor=(111, 111, 0)):
        Widget.__init__(self, evManager)

        self.font = Font(None, 22)
        if rect:
            self.rect = rect
        else:
            self.rect = Rect((0, 0), (100, 22 + 4)) #default width = 100px,
            # 22px = font height, 4px from 1px each of  border bottom,
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
        

    def notify(self, event):
        Widget.notify(self, event)


############################################################################



class ChatLogWidget(Widget):
    """ display static text """ 
    
    def __init__(self, evManager, numlines=3, rect=None):
        Widget.__init__(self, evManager)

        self.font = Font(None, 22)
        if rect:
            self.rect = rect
        else:
            self.rect = Rect((0, 0), (100, (22 + 4) * numlines)) 
            #100px = default width,
            # 22px = font height, 4px = 1px for each of border bottom,
            # padding bottom, padding top, and border top, 
        
        self.txtcolor = (255, 255, 0) #yellow
        self.bgcolor = (111, 111, 0) #brown
        self.image = Surface(self.rect.size).fill(self.bgcolor)
        
        self.maxnumlines = numlines
        self.linewidgets = deque(maxlen=numlines) # deque of TextLabelWidgets
        
        
        
    def addline(self, linetxt):
        """ If there's room, add a line on top, and then shift all widget texts upwards.
        If there's no room, only shift the texts upwards (don't add new widgets). 
        """
        
        if len(self.linewidgets) < self.maxnumlines: 
            # there's room to add another text widget on top of existing ones
            lines_from_top = self.maxnumlines - len(self.linewidgets)
            line_height = self.rect.height / self.maxnumlines
            newline_top = (lines_from_top - 1) * line_height
            newline_rect = Rect(0, newline_top, self.rect.width, line_height)
            txtwidget = TextLabelWidget(self.evManager, '', newline_rect)
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
        
        
        
    def notify(self, event):
        if isinstance(event, ChatlogUpdatedEvent):
            self.addline(event.author + ': ' + event.txt)
            
        Widget.notify(self, event)
        



