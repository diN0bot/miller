
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
import commands
import csv
import numpy
#import numarray
import time
import math
import serial
import pygame

from GUI import GUI
from parsers import RMLParser

import default_settings as settings

#-----------OBJECTS------------------------------------------------------------

def GCD(a, b):
    while b != 0:
        (a, b) = (b, a%b)
    return a

class MotorController(object):
    """
    """
    def __init__(self, clockspeed=0, prescalar=0, counterrate=0, stepsize=0,
                 direction=0, rate=0, softwarecountersize=0, hardwarecountersize=0,
                 duration=0, softwarecounter=0, hardwarecounter=0):
        """
        @param clockspeed: clock speed in Hz
        @param prescalar: internal prescalar
        @param counterrate: counter rate
        @param stepsize: travel per step in inches
        @param direction: 0 = off, 1 = forward, 2 = reverse 
        @param rate: next move time between steps in prescaled clock steps 
        @param duration: next move total duration in prescaled clock steps
        @param softwarecounter: 
        @param hardwarecounter: 
        """
        # The following line assigns all parameters to instance fields.
        # It is equivalent to self.clockspeed=clockspeed; self.rate=rate; ...
        self.__dict__.update(dict((name, value) for (name, value) in vars().items()))

class Guide(object):
    """
    """
    
    def __init__(self):
        """
        self.vector establishes vector of motion
        """
        vector = [0, 0, 0]
        
    def move(self, s):
        """
        """
        return numpy.array(self.vector)*s

class Machine(object):
    """
    
    """
    
    def __init__(self):
        """
        Initializes machine instance state.
        """
        self.numberofaxes = 3
        
        self.dynamicrangeresolution = 6000   #this sets the minimum slope ratio resolution
        self.maxcountersize = self.dynamicrangeresolution**2    #this is the max counter capacity needed based on calculations in notebook from 1/26/09
        self.softwarecounternumber = math.ceil(math.log(self.maxcountersize, 2)/8)     #max number of bytes needed
        
        self.guides = []
        self.motorcontrollers = []
        
        for i in range(self.numberofaxes):
            self.guides.append(Guide())
            mc = MotorController()
            mc.softwarecounter = numpy.zeros(self.softwarecounternumber)
            self.motorcontrollers.append(mc)
            
        self.position = numpy.zeros(self.numberofaxes) #current machine position (inches).
            
        self.guides[0].vector = [1, 0, 0]
        self.guides[1].vector = [0, 1, 0]
        self.guides[2].vector = [0, 0, 1]
        
        for i in range(self.numberofaxes):
            self.motorcontrollers[i].clockspeed = 20000000
            self.motorcontrollers[i].prescalar = 1024
            self.motorcontrollers[i].stepsize = 0.001
            self.motorcontrollers[i].softwarecountersize = 2**16-1
            self.motorcontrollers[i].hardwarecountersize = 2**8-1

    def move(self, commandmove):
        """
        Defines how the virtual machine moves based on its configuration and
        additional sensor inputs.
        
        Its goal is to create a model of the machine which can be used in a virtual 
        feedback loop by the controller.
        @param commandmove: 
        @return: 
        """
        returnmove = numpy.zeros(self.numberofaxes)
        for i in range(self.numberofaxes):
            returnmove=returnmove + self.guides[i].move(commandmove[i])
        return returnmove
            

class Controller(object):
    """
    """
    
    def __init__(self, portnumber):
        """
        @param portnumber: serial port number. check your os-specific serial.py file for details 
        """
        #error tolerance for positioning axes (inches)
        self.movtol = 0.0001
        self.portnumber = portnumber
        self.baudrate = 19200
        #in seconds
        self.sertimeout = None
        
        self.moves = []
        # index matches move that will be executed next
        self.moves_index = 0
        
        self.virtualmachine = Machine()
        
        self.gui = None
    
    def set_gui(self, gui):
        """
        
        """
        self.gui = gui
    
    def movegen(self, moveto):
        """
        @param moveto: 
        @return: delta
        """
        #ensures that error always starts out larger than the tolerance
        error = self.movtol*2*numpy.ones(len(moveto))
        #copies machine position to hypothetical position
        position = self.virtualmachine.position
        delta = numpy.zeros(len(moveto))
        
        while max(error) > self.movtol:
            error = moveto - position
            travel = self.virtualmachine.move(error)
            position=position + travel
            delta = delta + error
                
        return delta

    def stepgen(self, traverse, rate):
        """
        @param traverse: 
        @param rate: in in/min
        
        @TODO Currently only works propertly with 1 and 2 axis movement. Simultaneous
        movement in 3 axes is buggy. "This implies that error mapping won't work yet."
        """
        # convert to inches per second
        rate = rate / 60.
        # this flag gets set if a no-move condition is triggered
        nomove = 0
        distancesquaredsum = 0
        clockspeeds = numpy.zeros(self.virtualmachine.numberofaxes)
        prescalars = numpy.zeros(self.virtualmachine.numberofaxes)
        stepsizes = numpy.zeros(self.virtualmachine.numberofaxes)
        softwarecountersize = numpy.zeros(self.virtualmachine.numberofaxes)
        hardwarecountersize = numpy.zeros(self.virtualmachine.numberofaxes)
        
        for i in range(self.virtualmachine.numberofaxes):
            distancesquaredsum = distancesquaredsum + (traverse[i]*traverse[i])
            clockspeeds[i] = self.virtualmachine.motorcontrollers[i].clockspeed
            prescalars[i] = self.virtualmachine.motorcontrollers[i].prescalar
            stepsizes[i] = self.virtualmachine.motorcontrollers[i].stepsize
            softwarecountersize[i] = self.virtualmachine.motorcontrollers[i].softwarecountersize
            hardwarecountersize[i] = self.virtualmachine.motorcontrollers[i].hardwarecountersize

        distance = math.sqrt(distancesquaredsum)    #Euclidean distance of move
        movetime = distance / rate                  #Duration of move in seconds
        if settings.LOG: print "MOVETIME", movetime

        scaledclock = clockspeeds / prescalars      #Motor controller clock speeds (ticks / second)
        
        steps   = traverse / stepsizes              #number of steps needed
        steps   = numpy.round(steps)                #convert steps into integers
        absteps = numpy.abs(steps)                  #absolute step values
        
        movingaxes        = numpy.nonzero(steps)[0] #isolates only the moving axes
        movingsteps       = numpy.take(steps, movingaxes)
        absmovingsteps    = numpy.take(absteps, movingaxes)
        counter_durations = numpy.zeros(len(steps))

        directions = movingsteps/absmovingsteps     #-1 = reverse, 1 = forward

        if len(movingsteps)>2:
            if settings.LOG: print "3+ AXIS SIMULTANEOUS MOVES NOT SUPPORTED BY THIS STEP GENERATOR"

        if len(movingsteps) !=0:        
            nomove = 0
            
            if len(movingsteps) == 2:
                gcd = GCD(absmovingsteps[0], absmovingsteps[1])
                gcd_movingsteps = absmovingsteps / gcd
                
                # flip gcd_movingsteps
                moving_durations = gcd_movingsteps[::-1] 
                overall_duration = absmovingsteps[0]*moving_durations[0]
                
            else: # len == 1
                moving_durations = [1]
                overall_duration = absmovingsteps[0]
                
            maxsteps = max(absmovingsteps)
            stepinterval = overall_duration / absmovingsteps
    
            softwarecounterrange = (softwarecountersize / maxsteps).astype(int)
            hardwarecounterrange = numpy.ones(self.virtualmachine.numberofaxes)*min(hardwarecountersize)
    
            # movetime / number of sw counter ticks = time per click
            neededtimeperpulse = movetime / overall_duration
    
            prehwcounterpulsetime = prescalars / clockspeeds
    
            hardwarecounterstemp = numpy.ceil(neededtimeperpulse / prehwcounterpulsetime)
            hardwarecountersovfl = numpy.ceil(hardwarecounterstemp / hardwarecounterrange)
    
        
            softwarecounters = numpy.min([softwarecounterrange, hardwarecountersovfl], axis = 0)
            hardwarecounters = numpy.ceil(neededtimeperpulse/(prehwcounterpulsetime*softwarecounters))
    
            
            durations = numpy.zeros(self.virtualmachine.numberofaxes)
            numpy.put(durations, movingaxes, stepinterval)
            
            numpy.put(counter_durations, movingaxes, moving_durations)
    
            counter_durations = counter_durations * softwarecounters
            overall_duration = overall_duration * softwarecounters[0]   #this is a hack for now
        
            directions2 = numpy.zeros(self.virtualmachine.numberofaxes)
            numpy.put(directions2, movingaxes, directions)
    
            for i in range(self.virtualmachine.numberofaxes):
                self.virtualmachine.motorcontrollers[i].hardwarecounter = hardwarecounters[i]
                self.virtualmachine.motorcontrollers[i].softwarecounter = counter_durations[i]
                self.virtualmachine.motorcontrollers[i].duration = overall_duration
                if directions2[i] == -1:
                    directions2[i] = 2
                self.virtualmachine.motorcontrollers[i].direction = directions2[i]
        else:
            nomove = 1
            for i in range(virtualmachine.numberofaxes):
                    self.virtualmachine.motorcontrollers[i].hardwarecounter = 0
                    self.virtualmachine.motorcontrollers[i].softwarecounter = 0
                    self.virtualmachine.motorcontrollers[i].duration = 0
                    self.virtualmachine.motorcontrollers[i].direction = 0
            return nomove
        

    def xmit(self):
        """
        Constructs and sends packet over serial port
        
        packet format:
            byte0 - Start Byte
            byte1 - hwcounter
            byte2 - AXIS 1 Rate 0
            byte3 - AXIS 1 Rate 1
            byte4 - AXIS 2 Rate 0
            byte5 - AXIS 2 Rate 1
            byte6 - AXIS 3 Rate 0
            byte7 - AXIS 3 Rate 1
            byte8 - move duration 0
            byte9 - move duration 1
            byte10 - move duration 2
            byte11 - move duration 3
            byte12 - sync / motor direction (00ZrZfYrYfXrXf) where r is reverse and f is forward
        
        @TODO add byte13 - checksum
        
        @return: outgoing packet
        @raise serial.SerialException: If cannot open serial port and in use-serial mode (USE_SERIAL is True)
        """
        packetlength = 13
        xmitteraxes = self.virtualmachine.numberofaxes
        outgoing = numpy.zeros(packetlength)
        outgoing[0] = 255
        outgoing[1] = self.virtualmachine.motorcontrollers[0].hardwarecounter
        for i in range(xmitteraxes):
            outgoing[i*2+2] = int(self.virtualmachine.motorcontrollers[i].softwarecounter % 256)
            outgoing[i*2+3] = int(self.virtualmachine.motorcontrollers[i].softwarecounter / 256)
            outgoing[12] = outgoing[12] + self.virtualmachine.motorcontrollers[i].direction*(4**i)
            
        duration = self.virtualmachine.motorcontrollers[0].duration

        outgoingindex = 11
        remainder = duration
        for i in range(4):
            outgoing[11-i] = int(remainder / 256**(3-i))
            remainder = remainder % 256**(3-i)
        

        try:
            # open serial port
            serport = serial.Serial(self.portnumber, self.baudrate, timeout=self.sertimeout)

            # send command
            for i in range(len(outgoing)):
                serport.write(chr(outgoing[i]))
                a = serport.read()
    
            start = time.time()
            serport.read()
            if settings.LOG: print "XINT TIME", time.time() - start
            
        except serial.SerialException, details:
            if not settings.USE_SERIAL:
                pass
            else:
                print "\nEXCEPTION RAISED:", details
                sys.exit(0)
            
        return outgoing


    def simmove(self, outgoing):
        """
        @param outgoing: packet sent over serial port
        @return: [delta, rate, movetime]
        """
        xmitteraxes     = self.virtualmachine.numberofaxes
        hardwarecounter = numpy.ones(xmitteraxes)*outgoing[1]
        softwarecounter = numpy.ones(xmitteraxes)
        stepsize        = numpy.zeros(xmitteraxes)
        clockspeeds     = numpy.zeros(xmitteraxes)
        prescalars      = numpy.zeros(xmitteraxes)
        directions      = numpy.zeros(xmitteraxes)
        steps           = numpy.zeros(xmitteraxes)
        
        for i in range(3):
            softwarecounter[i] = outgoing[i*2+2]+outgoing[i*2+3]*256
            stepsize[i]        = self.virtualmachine.motorcontrollers[i].stepsize
            clockspeeds[i]     = self.virtualmachine.motorcontrollers[i].clockspeed
            prescalars[i]      = self.virtualmachine.motorcontrollers[i].prescalar

        duration = outgoing[8]+outgoing[9]*256+outgoing[10]*256**2+outgoing[11]*256**3

        remainder = outgoing[12]
        for i in range(3):
            directions[2-i] = int(remainder / 4**(2-i))
            remainder = remainder % 4**(2-i)
            if directions[2-i] == 2:
                directions[2-i] = -1

        movingaxes = numpy.nonzero(directions)[0]   #isolates only the moving axes
        movingcounters = numpy.take(softwarecounter, movingaxes)

        movingsteps = numpy.floor(duration / movingcounters)
        numpy.put(steps, movingaxes, movingsteps)
        delta = steps * stepsize*directions

        deltasquared = delta**2
        distancesquared = numpy.sum(deltasquared)
        distance = math.sqrt(distancesquared)
        minclockspeed = min(clockspeeds)
        maxprescalar = max(prescalars)
        maxhardwarecounter = max(hardwarecounter)
        
        movetime =   maxprescalar * maxhardwarecounter * duration / minclockspeed

        minutes = movetime / 60 #time in minutes

        rate = distance / minutes

        return [delta, rate, movetime]
    
    def add_moves(self, moves):
        """
        @param moves: single Move instance or list, tuple of Move objects 
        """
        if isinstance(moves, (list, tuple)):
            self.moves += moves
        else:
            self.moves.append(moves)
    
    def mill_moves(self):
        for move in self.moves:
            self.mill_move(move.x, move.y, move.z, move.rate)
            self.moves_index += 1
    
    def mill_move(self, x = None, y = None, z = None, rate = 1):
        """
        """
        
        if x == None: x = self.virtualmachine.position[0]
        if y == None: y = self.virtualmachine.position[1]
        if z == None: z = self.virtualmachine.position[2]

        moveto = [x, y, z]
        feedspeed = rate
        
        if settings.LOG: print "commandedposition: ", moveto
        delta = self.movegen(moveto)
        if self.gui:
            if moveto[2] > 0:
                self.gui.drawer.pen_down('simmove')
            else:
                self.gui.drawer.pen_up('simmove')
        nomove = self.stepgen(delta, feedspeed)
        # how much to pause for loop when not in USE_SERIAL
        sleep_amt = 0
        if nomove != 1:
            outgoing = self.xmit()
            [delta, rate, movetime] = self.simmove(outgoing)
            if settings.LOG: print "SIMMOVE MOVETIME", movetime
            if self.gui:
                sleep_amt = self.gui.drawer.goto(delta[0], delta[1], 'simmove', rate=rate, movetime=movetime)
            if settings.LOG: print "MOVE COMPLETE", delta
        else:
            delta = numpy.zeros(self.virtualmachine.numberofaxes)
            if settings.LOG: print "NO MOVE HERE!"
    
        self.virtualmachine.position = self.virtualmachine.position + delta
    
        if settings.LOG: print "machine position: " , self.virtualmachine.position
        if settings.LOG: print ""
        
        if self.gui:
            self.gui.check_events()
                    
        if not settings.USE_SERIAL and self.gui:
            # pause to mimic line drawing
            time.sleep(sleep_amt)
            # wait for space bar
            #gui.drawer.pause_for_space()

def run_app(moves):
    
    machinecontroller = Controller(settings.SERIAL_PORT)
    machinecontroller.add_moves(moves)
    
    gui = GUI(machinecontroller)
    gui.drawer.init_pen('simmove', 400)
    
    machinecontroller.set_gui(gui)

    # set start position
    machinecontroller.virtualmachine.position[0] = 1
    machinecontroller.virtualmachine.position[1] = 1
    #For some reason setting this also changes the local computer movetable!!! Why???
    machinecontroller.virtualmachine.position[2] = 0.002
    
    # mill board!
    machinecontroller.mill_moves()
    
    print "\nFINISHED BOARD!"

    # don't end program until press ESCAPE key
    while True: 
        gui.check_events()
        time.sleep(0.2)


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
