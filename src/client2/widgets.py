from client2.events import GUIFocusThisWidgetEvent, DownClickEvent, UpClickEvent, \
    MoveMouseEvent
from pygame.rect import Rect
from pygame.sprite import Sprite
from pygame.surface import Surface
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
        self.font = pygame.font.Font(None, 40) #default font, 40 pixels high
        txtimg = self.font.render(self.text, True, (0, 0, 0))

        if rect:
            self.rect = rect
            self.image = Surface(self.rect.size) #container size from specified rect
            # if txtimg does not fit in rect, it'll get cut (good thing) 
        else:
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
            print('button down clicked!')
            self.evManager.post(self.onDownClickEvent)
            
                      
    def onupclick(self):
        #self.dirty = True
        if self.onUpClickEvent and self.focused:
            print('button up clicked!')
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
    """ widget where user can enter text. 
    It loses focus when the user clicks somewhere else. 
    TODO: when focused, K_ENTER should do a 'submit' of some sort, and unfocus
    """
    
    def __init__(self, evManager, width, container=None):
        Widget.__init__(self, evManager, container)

        self.font = pygame.font.Font(None, 30)
        linesize = self.font.get_linesize() #height

        self.rect = pygame.Rect((0, 0, width, linesize + 4))
        boxImg = pygame.Surface(self.rect.size).convert_alpha()
        bgcolor = (255, 255, 255) #white
        pygame.draw.rect(boxImg, bgcolor, self.rect, 4)

        self.emptyImg = boxImg.convert_alpha()
        self.image = boxImg

        self.text = ''
        self.textPos = (22, 2) #TODO: why 22?
        self.textColor = (0, 0, 0) #black


    def update(self):
        if not self.dirty:
            return

        text = self.text
        if self.focused:
            text += '|'

        textImg = self.font.render(text, 1, textColor)
        self.image.blit(self.emptyImg, (0, 0))
        self.image.blit(textImg, self.textPos)

        self.dirty = False


    def onclick(self):
        self.focused = True
        self.dirty = True


    def set_text(self, newtext):
        self.text = newtext
        self.dirty = True


    def notify(self, event):

        if isinstance(event, ClickEvent): 
            if self.rect.collidepoint(event.pos):
                self.onclick()
            elif self.focused: #user clicked on something else
                self.set_focus(False)

        elif isinstance(event, UnicodeKeyPushedEvent) and self.focused:
            # add visible characters at the end of existing string
            newtxt = self.text + event.key
            self.set_text(newtxt)
        elif isinstance(event, BackspaceKeyPushedEvent) and self.focused:
            #strip last character
            newtxt = self.text[:(len(self.text) - 1)]
            self.set_text(newtxt)

        Widget.notify(self, event)

