"""
All button and tab command objects.

Each object has a 'do' method that takes no parameters. Any necessary parameter
should be passed in upon initialization.
"""

import pygame

#-----------Machine Commands---------------------------------------------------

class LeftCommand(object):
    """ job board left """
    
    def __init__(self, controller):
        self.controller = controller
        
    def do(self):
        self.controller.jog_left()

class RightCommand(object):
    """ job board right """
    
    def __init__(self, controller):
        self.controller = controller
        
    def do(self):
        self.controller.jog_right()
        
class TowardCommand(object):
    """ job board toward """
    
    def __init__(self, controller):
        self.controller = controller
        
    def do(self):
        self.controller.jog_toward()
        
class AwayCommand(object):
    """ job board away """
    
    def __init__(self, controller):
        self.controller = controller
        
    def do(self):
        self.controller.jog_away()
        
class UpCommand(object):
    """ set pen up """
    
    def __init__(self, controller):
        self.controller = controller
        
    def do(self):
        self.controller.pen_up()

class DownCommand(object):
    """ set pen down """
    
    def __init__(self, controller):
        self.controller = controller
        
    def do(self):
        self.controller.jog_down()

class CutCommand(object):
    """ set pen cut """
    
    def __init__(self, controller):
        self.controller = controller
        
    def do(self):
        self.controller.pen_cut()


#-----------GUI Commands-------------------------------------------------------
    
class SelectTab(object):
    """ job board right """
    
    def __init__(self, tabbed_pane, tab):
        self.tabbed_pane = tabbed_pane
        self.tab = tab
        
    def do(self):
        self.tabbed_pane.select_tab(self.tab)
        self.tabbed_pane.draw()
        pygame.display.flip()
    