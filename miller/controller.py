
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

import default_settings as settings
from miller.eventqueue import EventQueue

#-----------OBJECTS------------------------------------------------------------

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

class Move(object):
    """
    Simple data structure for storing move information.
    
    This is the interface between the parsers and the machine controller code.
    Because both modules depend on this class, it lives here outside of import loops.
    
    NOTE: Controller assumes Move objects depict global positions and rate, not
    changes in positions or rate.
    
    NOTE: If, in a later iteration, it makes sense to have a different kind of move,
    and thus a different kind of machinecontroller.execute_move, then the execute_move
    abstraction should be attached to each move object. Since only the machinecontroller
    actually knows how to execute moves, that means the Move abstraction should be 
    owned by machinecontroller.
    
    That is, a machine controller instance should be able to store different kinds of moves
    that get executed differently.
    """

    def __init__(self, x = None, y = None, z = None, rate = 1):
        self.x = x
        self.y = y
        self.z = z
        self.rate = rate
    
    def __unicode__(self):
        return "x=%s, y=%s, z=%s at %s" % (self.x, self.y, self.z, self.rate)

class Controller(object):
    """
    this space intentionally left blank
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
        
        self.virtualmachine = Machine()
        self.gui = None
        
        self.board = EventQueue(self._finished_milling_board_callback)
        self.one_offs = EventQueue()
        
        self.board.pause()
        self.one_offs.go()
        
        self.board.setName("Board Queue Thread")
        self.one_offs.setName("One Offs Thread")
        
        # jogging move parameters
        self.PEN_STATES = {'up':'up', 'down':'down', 'cut':'cut'}
        self.pen_state = self.PEN_STATES['up']
        self.pen_up_z = 0.05
        self.pen_down_z = -0.005
        self.pen_cut_z = -0.010 # ??
        self.move_amount = 0.1
        self.traverse_speed = 8.0
        self.retract_speed = 8.0
        self.cutting_speed = 4.0
        self.plunge_speed = 4.0
        
        # start event queues
        self.board.start()
        self.one_offs.start()
    
    def _finished_milling_board_callback(self):
        self.board.pause()
        self.one_offs.go()

    def is_pen_up(self): return self.pen_state == self.PEN_STATES['up']
    def is_pen_down(self): return self.pen_state == self.PEN_STATES['down']
    def is_pen_cutting(self): return self.pen_state == self.PEN_STATES['cut']
    
    def set_gui(self, gui):
        """
        Set self's gui field. This should be part of the constructor, but because GUI's constructor
        also takes a Controller, we need a set_gui method to resolve the catch-22.
        
        If set_gui is never called, that's ok. There will simply be no gui.
        If set_gui is called twice, self.gui is overwritten
        
        @param gui: a GUI instance 
        """
        self.gui = gui
    
    def _movegen(self, moveto):
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

    def _GCD(self, a, b):
        while b != 0:
            (a, b) = (b, a%b)
        return a

    def _stepgen(self, traverse, rate):
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
                gcd = self._GCD(absmovingsteps[0], absmovingsteps[1])
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
            for i in range(self.virtualmachine.numberofaxes):
                    self.virtualmachine.motorcontrollers[i].hardwarecounter = 0
                    self.virtualmachine.motorcontrollers[i].softwarecounter = 0
                    self.virtualmachine.motorcontrollers[i].duration = 0
                    self.virtualmachine.motorcontrollers[i].direction = 0
            return nomove

    def _xmit(self):
        """
        Constructs and sends packet over serial port.
        
        Packet contains instructions for different speeds for each of the 
        three motors, as well as a single instruction duration.
        
        Blocking on receiving acknowledge. @TODO implement time_out with x retries
        before raising an exception.
        
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

    def _simmove(self, outgoing):
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
    
    def set_board(self, moves):
        """
        Sets board's move queue to the specified moves. Will overwrite any
        moves currently in queue. Use mill_board() to start milling..
        """
        self.board.reset()
        for move in moves:
            self.board.add(self.move, move.x, move.y, move.z, move.rate)
    
    def reset_board(self):
        """
        Returns spindle and move queue to initial state.
        """
        self.board.reset()
    
    def mill_board(self):
        """
        Continue milling moves in move queue.
        """
        self.one_offs.pause()
        self.board.go()
    
    def pause_board(self):
        """
        Stop milling moves in move queue. Resume with mill_board()
        """
        self.one_offs.reset()
        self.one_offs.go()
        self.board.pause()
        
    def exit(self):
        """
        Exit EventQueue threads
        """
        self.board.exit()
        self.one_offs.exit()
    
    def jog_left(self):
        rate = self.is_pen_up() and self.traverse_speed or self.cutting_speed
        x = self.virtualmachine.position[0] - self.move_amount
        self.one_offs.add(self.move, x=x, rate=rate)
        
    def jog_right(self):
        rate = self.is_pen_up() and self.traverse_speed or self.cutting_speed
        x = self.virtualmachine.position[0] + self.move_amount
        self.one_offs.add(self.move, x=x, rate=rate)
    
    def jog_away(self):
        rate = self.is_pen_up() and self.traverse_speed or self.cutting_speed
        y = self.virtualmachine.position[1] - self.move_amount
        self.one_offs.add(self.move, y=y, rate=rate)
    
    def jog_toward(self):
        rate = self.is_pen_up() and self.traverse_speed or self.cutting_speed
        y = self.virtualmachine.position[1] + self.move_amount
        self.one_offs.add(self.move, y=y, rate=rate)
    
    def pen_up(self):
        if not self.is_pen_up():
            self.one_offs.add(self.move, z = self.pen_up_z, rate=self.retract_speed)
    
    def pen_down(self):
        if not self.is_pen_down():
            self.one_offs.add(self.move, z = self.pen_down_z, rate=self.plunge_speed)
    
    def pen_cut(self):
        if not self.is_pen_cutting():
            self.one_offs.add(self.move, z = self.pen_cut_z, rate=self.plunge_speed)
    
    def move(self, x = None, y = None, z = None, rate = 1):
        """
        @invariant: z should match one of self.pen_FOO_z
        @invariant: rate should match one of self.FOO_speed
        """
        if z == self.pen_up_z: self.pen_state = self.PEN_STATES['up']
        if z == self.pen_down_z: self.pen_state = self.PEN_STATES['down']
        if z == self.pen_cut_z: self.pen_state = self.PEN_STATES['cut']
        
        if x == None: x = self.virtualmachine.position[0]
        if y == None: y = self.virtualmachine.position[1]
        if z == None: z = self.virtualmachine.position[2]

        moveto = [x, y, z]
        feedspeed = rate
        
        if settings.LOG: print "commandedposition: ", moveto
        delta = self._movegen(moveto)
        if self.gui:
            if moveto[2] > 0:
                self.gui.drawer.pen_down('simmove')
            else:
                self.gui.drawer.pen_up('simmove')
        nomove = self._stepgen(delta, feedspeed)
        # how much to pause for loop when not in USE_SERIAL
        sleep_amt = 0
        if nomove != 1:
            outgoing = self._xmit()
            [delta, rate, movetime] = self._simmove(outgoing)
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
        
        if not settings.USE_SERIAL and self.gui:
            # pause to mimic line drawing
            time.sleep(sleep_amt)
            # wait for space bar
            #gui.drawer.pause_for_space()
