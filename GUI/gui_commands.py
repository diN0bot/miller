"""
All button and tab command objects.

Each object has a 'do' method that takes no parameters. Any necessary parameter
should be passed in upon initialization.
"""

import pygame

"""========================================================================="""
"""  Machine Commands """
"""========================================================================="""
class LeftCommand(object):
    """ job board left """
    
    def __init__(self, machine):
        self.machine = machine
        
    def do(self):
        self.machine.jog_left()

class RightCommand(object):
    """ job board right """
    
    def __init__(self, machine):
        self.machine = machine
        
    def do(self):
        self.machine.jog_right()

"""========================================================================="""
"""  GUI Commands """
"""========================================================================="""
    
class SelectTab(object):
    """ job board right """
    
    def __init__(self, tabbed_pane, tab):
        self.tabbed_pane = tabbed_pane
        self.tab = tab
        
    def do(self):
        self.tabbed_pane.select_tab(self.tab)
        self.tabbed_pane.draw()
        pygame.display.flip()
    