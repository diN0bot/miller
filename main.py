
"""
Information Flow:

    1. Parse .rml file into Moves: [dx, dy, dz] + feedspeed in inches/min
    
    2. Execute moves:
        a. move -> controller.stepgen -> None (modifies machine state, eg duration)
        b. None -> controller.xmit (reads machine state) -> packet sent to controller
        c. packet -> controller.simmove -> estimated [dx, dy, dz] + rate + movetime 

"""

#------------IMPORTS-----------------------------------------------------------

import sys, os
import threading
import commands
import csv
import numpy
#import numarray
import time
import math
import serial
import pygame

from GUI import GUI
from miller import Controller
from parsers import RMLParser

import default_settings as settings

def run_app(moves):
    """
    @param moves: iterable of Move objects
    """
    try:
        controller = Controller(settings.SERIAL_PORT)
        controller.set_board(moves)
        
        gui = GUI(controller)
        gui.drawer.init_pen('simmove', 400)
        
        controller.set_gui(gui)
    
        # set start position
        controller.virtualmachine.position[0] = 1
        controller.virtualmachine.position[1] = 1
        #For some reason setting this also changes the local computer movetable!!! Why???
        controller.virtualmachine.position[2] = 0.002
        
        # mill board!
        controller.mill_board()
    
        # gui should continue running until user presses escape key
        while True:
            gui.check_events()
            time.sleep(0.2)
    except Exception, error:
        print " ERROR "
        print Exception, error
        self.controller.exit()
        sys.exit(0)

if __name__ == "__main__":
    """ This is the main loop that gets executed when running this file
        from the command line """
    
    if len(sys.argv) > 0:
        rmlfile = sys.argv[1]
    else:
        print "Program takes 1 required argument: name of RML file"
        sys.exit(1)
        
    moves = RMLParser().parse_rml(rmlfile)
    
    run_app(moves)
