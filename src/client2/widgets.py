from client2.events import GUIFocusThisWidgetEvent, ClickEvent
import pygame
from pygame.sprite import Sprite



class Widget(Sprite):
    """ abstract class for other types of widgets """
    
    def __init__(self, evManager, container=None):
        Sprite.__init__(self)

        self.evManager = evManager
        self.evManager.register_listener(self)

        self.container = container
        self.focused = False
        self.dirty = True


    def set_focus(self, val):
        self.focused = val
        self.dirty = True


    def kill(self):
        self.container = None
        del self.container #why?
        Sprite.kill(self)


    def notify(self, event):
        """ TODO: not sure this is needed right now """
        if isinstance(event, GUIFocusThisWidgetEvent):
            if event.widget is self:
                self.set_focus(True)
            elif self.focused: #user clicked on an other widget
                self.set_focus(False)
            
            
            



class TextBoxWidget(Widget):
    """ widget where user can enter text 
    loses focus when user clicks somewhere else 
    TODO: enter when focused should do a 'submit' of some sort """
    
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






class ButtonWidget(Widget):
    """ widget with eventual text that can be clicked """
    
    def __init__(self, evManager, text, container=None, onClickEvent=None):
        Widget.__init__(self, evManager, container)

        self.font = pygame.font.Font(None, 30)
        self.text = text
        self.image = self.font.render(self.text, 1, (0, 0, 255)) #blue
        #self.rect = self.image.get_rect()
        self.rect = container 
        
        self.onClickEvent = onClickEvent


    def update(self):
        if not self.dirty:
            return

        if self.focused:
            color = (255, 0, 0) #txt is red when widget is focused
        else:
            color = (0, 0, 255) #blue when not focused
        self.image = self.font.render(self.text, 1, color)
        #self.rect  = self.image.get_rect()

        self.dirty = False


    def onclick(self):
        self.dirty = 1
        if self.onClickEvent:
            print('button clicked!')
            self.evManager.post(self.onClickEvent)


    def notify(self, event):
        if isinstance(event, ClickEvent) and self.rect.collidepoint(event.pos):
            self.onclick()

        Widget.notify(self, event)
