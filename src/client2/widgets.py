from client2.events import GUIFocusThisWidgetEvent, DownClickEvent, UpClickEvent, \
    MoveMouseEvent, UnicodeKeyPushedEvent, BackspaceKeyPushedEvent
from pygame.rect import Rect
from pygame.sprite import Sprite
from pygame.surface import Surface
from pygame.font import Font
import pygame


class Widget(Sprite):
    """ abstract class for other types of widgets """
    
    def __init__(self, evManager):
        Sprite.__init__(self)

        self.evManager = evManager
        self.evManager.register_listener(self)

        self.focused = False
        self.dirty = True


    def set_focus(self, val):
        self.focused = val
        self.dirty = True


    def notify(self, event):
        """ Focus me if I was the target """
        if isinstance(event, GUIFocusThisWidgetEvent):
            if event.widget is self:
                self.set_focus(True)
            elif self.focused: #user clicked on an other widget
                self.set_focus(False)
            
            
            





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
        if not self.dirty:
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
        
        self.dirty = False


    def ondownclick(self):
        """ button down focuses the widget"""
        self.dirty = True
        focus_event = GUIFocusThisWidgetEvent(self) 
        # this event will be caught by Widget.notify() 
        # when it comes back to that ButtonWidget 
        self.evManager.post(focus_event)
        
        if self.onDownClickEvent:
            self.evManager.post(self.onDownClickEvent)
            
                      
    def onupclick(self):
        #self.dirty = True
        if self.onUpClickEvent and self.focused:
            self.evManager.post(self.onUpClickEvent)


    def onmousemovein(self):
        pass
    
    def onmousemoveout(self):
        """ default behavior: unfocus the button 
        when the mouse moves out of it 
        """ 
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









class TextBoxWidget(Widget):
    """ widget where the user can enter text. 
    The widget loses focus when the user clicks somewhere else. 
    TODO: when focused, K_ENTER should do a 'submit' of some sort, and unfocus
    """
        
    def __init__(self, evManager, rect=None):
        Widget.__init__(self, evManager)
        # Widget init sets dirty to true, hence the actual rendering 
        # will be done in TextBoxWidget.update(), called by the view renderer.

        self.text = ''
        self.font = Font(None, 25)
        
        if rect:
            self.rect = rect
        else:
            self.rect = Rect((0, 0), (100, 25 + 4)) #default width = 100px,
            # 25px = font height, 
            # 4px = border bottom + padding bottom + padding top + border top  
        
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
        if not self.dirty:
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

        self.dirty = False


    def ondownclick(self):
        self.focused = True
        self.dirty = True


    def set_text(self, newtext):
        self.text = newtext
        self.dirty = True


    def notify(self, event):

        if isinstance(event, DownClickEvent): 
            if self.rect.collidepoint(event.pos):
                self.ondownclick()
            elif self.focused: #user clicked on something else
                self.set_focus(False)

        elif isinstance(event, UnicodeKeyPushedEvent) and self.focused:
            # add visible characters at the end of existing string
            newtxt = self.text + event.unicode
            self.set_text(newtxt)
        elif isinstance(event, BackspaceKeyPushedEvent) and self.focused:
            # erase last character
            newtxt = self.text[:(len(self.text) - 1)]
            self.set_text(newtxt)

        Widget.notify(self, event)

