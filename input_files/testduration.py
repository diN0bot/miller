from miller import Controller, GUI, settings
from move import Move


machinecontroller = Controller(settings.SERIAL_PORT)

gui = GUI(machinecontroller)
gui.drawer.init_pen('simmove', 400)

machinecontroller.set_gui(gui)

# set start position
machinecontroller.virtualmachine.position[0] = 1
machinecontroller.virtualmachine.position[1] = 1
#For some reason setting this also changes the local computer movetable!!! Why???
machinecontroller.virtualmachine.position[2] = 0.002

traversespeed = 8
retractspeed = 8
cuttingspeed = 4.0
plungespeed = 4.0
z_down = -0.005
z_up = 0.05
machinecontroller.add_moves(Move(None, None, 0.05, 8))
machinecontroller.add_moves(Move(0.877, 1.055, 0.05, 8))
machinecontroller.add_moves(Move(None, None, -0.005, 4.0))
machinecontroller.add_moves(Move(0.899, 1.055, -0.005, 4.0))
machinecontroller.add_moves(Move(0.899, 2.055, -0.005, 4.0))
machinecontroller.add_moves(Move(1.899, 2.055, -0.005, 4.0))
machinecontroller.add_moves(Move(1.899, 1.055, -0.005, 4.0))
machinecontroller.add_moves(Move(0.899, 1.055, -0.005, 4.0))
machinecontroller.mill_moves()
