import virtualmachine9 as vm

traversespeed = 8
retractspeed = 8
cuttingspeed = 4.0
plungespeed = 4.0
z_down = -0.005
z_up = 0.05
vm.move(None, None, 0.05, 8)
vm.move(0.877, 1.055, 0.05, 8)
vm.move(None, None, -0.005, 4.0)
vm.move(0.899, 1.055, -0.005, 4.0)
vm.move(0.899, 2.055, -0.005, 4.0)
vm.move(1.899, 2.055, -0.005, 4.0)
vm.move(1.899, 1.055, -0.005, 4.0)
vm.move(0.899, 1.055, -0.005, 4.0)
