"""
Main user interaction module.

GUI is the main class. For example, it contains a ControlPanel, which in turn contains a tabbed pane,
which in turn contains tabs, which in turn contains buttons. Drawing and event handling
are piped down the chain.

Drawer is in a separate file and is instantiated externally to GUI. Eventually we might want
to refactor this: put ControlPanel in it's own file; GUI contains Drawer.
"""
import sys
import math
import pygame
from gui_commands import *
from drawer import Drawer

class GUI(object):
    """
    Whole graphical user interface, including drawer and control panel.
    
    Drawer objects can be instantiated and manipulated separately--it just needs a reference
    to the window field and the boundaries of its space.
    
    ControlPanel is manipulated directly by the GUI.
    """
    
    def __init__(self, machine):
        """
        Initializes pygame window,
        including the drawing space and control panel
        """
        self.machine = machine
        
        pygame.init() 
        pygame.display.set_caption("Desktop CNC Miller")
        #create the screen
        self.max_x = 1200
        self.max_y = 600
        self.window = pygame.display.set_mode( (self.max_x, self.max_y) )
        #set background
        #self.window.fill( (30, 30, 255) )
        self.window.fill( (0,0,0) )
        
        midpnt = int(self.max_x*0.6)
        self.drawer_bounds = pygame.Rect(0, 0, midpnt, self.max_y)
        self.control_panel_bounds = pygame.Rect(midpnt, 0, self.max_x-midpnt, self.max_y)
        
        self.control_panel = ControlPanel(self.window, self.control_panel_bounds)
        self.drawer = Drawer(self.window)
        
        self.control_panel.draw()
        
    def check_events(self):
        """
        pygame window loop. check if ESCAPE key is pressed to close window and exit program
        """
        for event in pygame.event.get():
            self.control_panel.check_event(event)
            
            # press ESCAPE to exit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: 
                    sys.exit(0)
        pygame.display.flip()



class ControlPanel(object):
    """
    Keeps track of panel buttons and state.
    Redraws the whole panel whenever there is user interaction.
    """
    def __init__(self, window, bounds):
        self.window = window
        
        self.border_color = (255, 255, 0)
        self.bounds = bounds
        
        partition = 0.2
        #spindle_position_bounds = pygame.Rect(self.bounds[0], self.bounds[1], self.bounds[2], int(self.bounds[3]*partition))
        #tabbed_pane_bounds = pygame.Rect(self.bounds[0], self.bounds[1] + int(self.bounds[3]*partition), self.bounds[2], int(self.bounds[3]*(1-partition)))
        spindle_position_bounds = pygame.Rect(0, 0, self.bounds[2], int(self.bounds[3]*partition))
        tabbed_pane_bounds = pygame.Rect(0, int(self.bounds[3]*partition), self.bounds[2], int(self.bounds[3]*(1-partition)))

        self.tabbed_pane = TabbedPane(color=(255,255,255),
                                      window=self.window,
                                      bounds_relative_to_parent=tabbed_pane_bounds,
                                      parent_bounds=self.bounds)
        
        ###########################################################################
        board_tab = self.tabbed_pane.add_pane("Position Board") 
        
        # x_offset and y_offset are button position relative to the x,y of tabbed_pane_bounds
        buttons = [{'text': 'Left', 'x_offset': 60, 'y_offset': 65, 'command': LeftCommand('y')},
                   {'text': 'Toward', 'x_offset': 130, 'y_offset': 45, 'command': LeftCommand('y')},
                   {'text': 'Away', 'x_offset': 130, 'y_offset': 85, 'command': LeftCommand('y')},
                   {'text': 'Right', 'x_offset': 200, 'y_offset': 65, 'command': LeftCommand('y')},
                   
                   {'text': 'Up', 'x_offset': 320, 'y_offset': 65, 'command': LeftCommand('y')},
                   {'text': 'Down', 'x_offset': 375, 'y_offset': 65, 'command': LeftCommand('y')},
                   
                   {'text': 'Auto Jog To Zero', 'x_offset': 200, 'y_offset': 200, 'command': LeftCommand('y')},
                   
                   {'text': 'Reset Zero', 'x_offset': 200, 'y_offset': 300, 'command': LeftCommand('y')},
                  ]
        self.labels = []
        labels = [{'text': 'Jog Board', 'x_offset': 130, 'y_offset': 20},
                  {'text': 'Spindle Position', 'x_offset': 350, 'y_offset': 40},
                  ]
        for button in buttons:
            board_tab.buttons.append(create_item(self.window, button['text'], button['x_offset'], button['y_offset'], board_tab, command=button['command']))
            
        for label in labels:
            board_tab.labels.append(create_item(self.window, label['text'], label['x_offset'], label['y_offset'], board_tab))
        ###########################################################################
        
        ###########################################################################
        mill_tab = self.tabbed_pane.add_pane("Mill Board") 
        
        # x_offset and y_offset are button position relative to the x,y of tabbed_pane_bounds
        buttons = [{'text': 'Go', 'x_offset': 60, 'y_offset': 65, 'command': LeftCommand('y')},
                   {'text': 'Pause', 'x_offset': 130, 'y_offset': 45, 'command': LeftCommand('y')},
                   {'text': 'Reset', 'x_offset': 130, 'y_offset': 85, 'command': LeftCommand('y')},
                  ]
        self.labels = []
        labels = [{'text': 'Jog Board', 'x_offset': 130, 'y_offset': 20},
                  {'text': 'Spindle Position', 'x_offset': 350, 'y_offset': 40},
                  ]
        for button in buttons:
            mill_tab.buttons.append(create_item(self.window, button['text'], button['x_offset'], button['y_offset'], mill_tab, command=button['command']))
            
        for label in labels:
            mill_tab.labels.append(create_item(self.window, label['text'], label['x_offset'], label['y_offset'], mill_tab))
        ###########################################################################
        
        self.tabbed_pane.select_tab(board_tab)
        
    def draw(self):
        """ draw all general"""
        self.tabbed_pane.draw()
    
    def check_event(self, event):
        """
        Ask all GUI elements to check event
        """
        self.tabbed_pane.check_event(event)
        
def create_item(window, text, x, y, parent, color=(100,193,212), command=None, bevel=True):
    """
    Factory method. All buttons and labels should be constructed using this method.
    @param text: item text
    @param x: x bound of item relative to parent
    @param y: y bound of item relative to parent
    @param parent: parent container. This is important because the created item's absolute
        bounds are based on it's relative x,y position plus it's parent's absolute bounds.
    @param color: background color
    @param bevel: If True, will add drop shadows around item. Not bevel per se...
    """
    font = pygame.font.Font(None, 20)
    text_width, text_height = font.size(text)
    text_surface = font.render(text,True,(0,0,0))
    rect = pygame.Rect(x-int(text_width/2.0),
                       y-int(text_height/2.0),
                       text_width,
                       text_height)
    if command:
        return Button(text_surface=text_surface,
                      color=color,
                      bounds_relative_to_parent=rect,
                      parent_bounds=parent.bounds,
                      command=command,
                      window=window,
                      bevel=bevel)
    else:
        return Label(text_surface=text_surface,
                     color=color,
                     bounds_relative_to_parent=rect,
                     parent_bounds=parent.bounds,
                     window=window)

class TabbedPane:
    """ Like Button class below, without commands """
    
    def __init__(self, color, bounds_relative_to_parent, parent_bounds, window):
        self.bounds = bounds_relative_to_parent.move( (parent_bounds[0], parent_bounds[1]) )

        self.color = color
        self.window = window
        self.tabs = []
        
    def add_pane(self, name):
        """
        All panes should be constructed using this factory method
        @param name: Tab label
        @return: constructed Tab
        """
        tab = Tab(tab_rank=len(self.tabs),
                  parent=self,
                  color=self.color,
                  #bounds_relative_to_parent=self.bounds.inflate(0, -50).move(0, 20),
                  bounds_relative_to_parent=pygame.Rect(0,20,self.bounds.inflate(0, -50)[2], self.bounds.inflate(0, -50)[3]),
                  window=self.window, name=name)
        self.tabs.append(tab)
        return tab
    
    def select_tab(self, selected_tab):
        """
        Sets the tab selection
        @param selected_tab: Tab. Should be in self.tabs
        """
        for tab in self.tabs:
            if tab == selected_tab:
                tab.selected = True
            else:
                tab.selected = False
        
    def draw(self):
        pygame.draw.rect(self.window, self.color, self.bounds)
        for tab in self.tabs:
            tab.draw()
    
    def check_event(self, event):
        """
        Ask all GUI elements to check event
        """
        for tab in self.tabs:
            tab.check_event(event)

class Tab:
    """ A single tab. Contains buttons and labels"""
    
    def __init__(self, name, color, bounds_relative_to_parent, window, parent, tab_rank):
        self.parent=parent
        
        self.bounds = bounds_relative_to_parent.move( (self.parent.bounds[0], self.parent.bounds[1]) )

        self.color = color
        self.window = window
        self.selected = False
        self.buttons = []
        self.labels = []
        
        self.tab = create_item(self.window, name, tab_rank*150 + 100, 12, parent, command=SelectTab(parent, self), bevel=False, color=(255,255,255))
        
    def draw(self):
        if self.selected:
            self.tab.draw()
        
            pygame.draw.rect(self.window, self.color, self.bounds)
        
            for item in self.buttons + self.labels:
                item.draw()
        else:
            self.tab.draw(background_tab=True)

    def check_event(self, event):
        """
        Ask all GUI elements to check event.
        If this tab is selected, check child items for events.
        Otherwise, check tab item (top of tab)
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.selected:
                for item in self.buttons:
                    item.handleMouseDown(event.pos[0], event.pos[1])
            else:
                self.tab.handleMouseDown(event.pos[0], event.pos[1])

class Label:
    """ Like Button class below, without commands """
    
    def __init__(self, text_surface, color, parent_bounds, bounds_relative_to_parent, window):
        self.bounds = bounds_relative_to_parent.move( (parent_bounds[0], parent_bounds[1]) )

        self.text_surface = text_surface
        self.color = color
        self.window = window
        
    def draw(self):
        self.window.blit(self.text_surface, (self.bounds[0], self.bounds[1]))


class Button:
    """Button class based on the Command pattern."""
    
    def __init__(self, text_surface, color, parent_bounds, bounds_relative_to_parent, command, window, bevel=True):
        self.bounds = bounds_relative_to_parent.move( (parent_bounds[0], parent_bounds[1]) )

        self.button_bounds = self.bounds.inflate(20,10)

        self.text_surface = text_surface
        self.color = color
        self.command = command
        self.pushed = False
        self.bevel = bevel
        self.window = window

    def handleMouseDown(self, x, y):
        if self.bounds.collidepoint(x, y):
            if self.command != None:
                self.command.do()
    
    def handleKeyPressed(self, a):
        pass
                
    def draw(self, background_tab=False):
        color = background_tab and (150,150,150) or self.color

        pygame.draw.rect(self.window, color, self.button_bounds)
        
        if self.bevel:
            x = self.button_bounds[0]-1
            y = self.button_bounds[1]
            h = self.button_bounds[3]
            dx = 2 # depth in x
            dy = 2 # depth in y 
            pygame.draw.polygon(self.window, (100,100,100), [(x,y),(x,y+h),(x-dx,y+h+dy),(x-dx,y+dy)])
            x = self.button_bounds[0]
            y = self.button_bounds[1]
            w = self.button_bounds[2]
            pygame.draw.polygon(self.window, (200,200,200), [(x,y+h),(x+w,y+h),(x+w-dx,y+h+dy),(x-dx,y+h+dy)])

        self.window.blit(self.text_surface, (self.bounds[0], self.bounds[1]))
