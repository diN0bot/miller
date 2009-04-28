from main import run_app
from miller import Move

moves = []
traversespeed = 8
retractspeed = 8
cuttingspeed = 4.0
plungespeed = 4.0
z_down = -0.005
z_up = 0.05
moves.append(Move(None, None, 0.05, 8))
moves.append(Move(0.877, 1.055, 0.05, 8))
moves.append(Move(None, None, -0.005, 4.0))
moves.append(Move(0.899, 1.055, -0.005, 4.0))
moves.append(Move(0.899, 2.055, -0.005, 4.0))
moves.append(Move(1.899, 2.055, -0.005, 4.0))
moves.append(Move(1.899, 1.055, -0.005, 4.0))
moves.append(Move(0.899, 1.055, -0.005, 4.0))
run_app(moves)
