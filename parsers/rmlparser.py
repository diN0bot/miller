
import sys
import os
import csv
from move import Move

class RMLParser(object):
    """
    Parses RML files into Moves and Virtual Machine Controller (VMC) files.
    VMC are python commands that correspond to executing Moves.
    """
    def __init__(self):
        self.rml = None
        
        self.zup = 0 # z axis up position
        self.zdown = 0 # z axis down position
        self.z_up = 0 # z axis up position in rmlunits
        self.z_down = 0 # z axis down position in rmlunits
        self.currentx = 0 # current x axis position
        self.currenty = 0 # current y axis position
        self.penposition = "down"
        
        self.tableindex = 0
        self.main_module_name = "miller"
        self.rmlunits = 0.001 #rml units in thousandths of an inch
        
        self.traversespeed = 8 # units are in/min
        self.retractspeed = 8 # units are in/min
        self.cuttingspeed = 1 # units are in/min
        self.plungespeed = 1
        
        self.moves = []
        self.vmc = None
        
    def _write_vmc(self, str):
    	"""
    	Writes a VMC file if one already exists. If no VMC file opened,
    	then nothing happens (no-op)
    	"""
        if self.vmc:
            self.vmc.write(str + os.linesep)
    
    def _make_move(self, x=None, y=None, z=None, rate=1):
    	"""
    	Appends a Move instance to the moves list.
    	Writes a move call to the VMC file, also (convenience call to self._write_vmc)
    	"""
        self.moves.append(Move(x=x, y=y, z=z, rate=rate))
        self._write_vmc("machinecontroller.add_moves(Move(%s, %s, %s, %s))" % (x, y, z, rate))
    
    def parse_rml(self, rml_filename, output_vmc=True):
        """
        Parses .CAD (the media lab program, not the file format) rml files into
        move objects
        
        @param rml_filename: name of rml file to parse
        @param output_vmc: True if should write Virtual Machine Controller script.
        	The VMC file will have the same name as the rml file but with a '.vmc' suffix
        @returns: list of Moves parsed from file
        """
        if ".rml" == rml_filename[-4:]:
        	vmcfile = rml_filename.replace('.rml', '.py')
        else:
        	vmcfile = rml_filename + '.py'
        
        # parse rmlfile as a semi-colon delimited file
        # rml contains the data we want to parse
        rmlfile = open(rml_filename, mode = 'r')
        csvparser = csv.reader(rmlfile, delimiter=';', quoting = csv.QUOTE_ALL)
        self.rml = csvparser.next()
        rmlfile.close()
        
        if output_vmc:
            self.vmc = open(vmcfile, 'w')

        self._write_vmc("from " + self.main_module_name + " import Controller, GUI, settings")
        self._write_vmc("from move import Move")
        self._write_vmc("")
        
        self._write_vmc("""
machinecontroller = Controller(settings.SERIAL_PORT)

gui = GUI(machinecontroller)
gui.drawer.init_pen('simmove', 400)

machinecontroller.set_gui(gui)

# set start position
machinecontroller.virtualmachine.position[0] = 1
machinecontroller.virtualmachine.position[1] = 1
#For some reason setting this also changes the local computer movetable!!! Why???
machinecontroller.virtualmachine.position[2] = 0.002
""")
        self._write_vmc("traversespeed = " + str(self.traversespeed))
        self._write_vmc("retractspeed = " + str(self.retractspeed))
        
        for h in xrange(len(self.rml)):
            commander = 0
            firstterm = 0
            secondterm = 0
            currententry = self.rml[h]
            entrylength = len(currententry)
            for i in xrange(entrylength):
                j = i+2
                
                if currententry[i:j]=="PA": #no idea what the hell this is
                    commander = "PA"
                    
                elif currententry[i:j] == "VS": #xy travel speed
                    commander = "VS"
                    firstterm = j
                    xyspeed = currententry[firstterm:entrylength]
                    xyspeed = float(xyspeed)
                    self.cuttingspeed = xyspeed
                    self._write_vmc("cuttingspeed = " + str(xyspeed))
                    
                elif currententry[i:j]== "VZ": #z travel speed
                    commander = "VZ"
                    firstterm = j
                    zspeed = float(currententry[firstterm:entrylength])
                    self.plungespeed = zspeed
                    
                    self._write_vmc("plungespeed = %s" % self.plungespeed)
                
                elif currententry[i:j] == "PZ":
                    commander = "PZ"
                    firstterm = j
                    
                elif currententry[i:j] == "PU":
                    commander = "PU"
                    firstterm = j
                    
                elif currententry[i:j] == "PD":
                    commander = "PD"
                    firstterm = j
                    
                elif currententry[i] == ",":
                    secondterm = i
                    
            if commander == "PZ": #Set Z pen positions in down, up format
                zdown = float(currententry[firstterm:secondterm])
                zup = float(currententry[secondterm+1:entrylength])

                self.z_down = zdown*self.rmlunits
                self.z_up = zup*self.rmlunits
                
                self._write_vmc("z_down = %s" % self.z_down)
                self._write_vmc("z_up = %s" % self.z_up)
                
        
            if commander == "PD": #Pen down RML command.
                
                if self.penposition == "down":
                
                    currentx = float(currententry[firstterm:secondterm])
                    currenty = float(currententry[secondterm+1:entrylength])
                    
                    self._make_move(currentx*self.rmlunits, currenty*self.rmlunits, self.z_down, self.cuttingspeed)

                elif self.penposition == "up":
                
                    self._make_move(z=self.z_down, rate=self.plungespeed)
                    
                    currentx = float(currententry[firstterm:secondterm])
                    currenty = float(currententry[secondterm+1:entrylength])
                    
                    self._make_move(currentx*self.rmlunits, currenty*self.rmlunits, self.z_down, self.cuttingspeed)
                    self.penposition = "down"    
        
            if commander == "PU": #Pen up RML command.
                
                if self.penposition == "up":
                    
                    currentx = float(currententry[firstterm:secondterm])
                    currenty = float(currententry[secondterm+1:entrylength])
                                    
                    self._make_move(currentx*self.rmlunits, currenty*self.rmlunits, self.z_up, self.traversespeed)
                                    
                elif self.penposition == "down":
                    
                    self._make_move(z=self.z_up, rate=self.retractspeed)
                    
                    currentx = float(currententry[firstterm:secondterm])
                    currenty = float(currententry[secondterm+1:entrylength])
                    
                    self._make_move(currentx*self.rmlunits, currenty*self.rmlunits, self.z_up, self.traversespeed)
                    self.penposition = "up"

        self._write_vmc("machinecontroller.mill_moves()")
        return self.moves 

if __name__ == "__main__":
    if len(sys.argv) > 0:
        RMLParser().parse_rml(sys.argv[1])
        sys.exit(0)
    else:
        print "Program takes 1 required argument: name of RML file"
        sys.exit(1)
