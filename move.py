"""
Simple data structure for storing move information.
This is the interface between the parsers and the machine controller code.
Because both modules depend on this class, it lives here outside of import loops.

NOTE: If, in a later iteration, it makes sense to have a different kind of move,
and thus a different kind of machinecontroller.execute_move, then the execute_move
abstraction should be attached to each move object. Since only the machinecontroller
actually knows how to execute moves, that means the Move abstraction should be 
owned by machinecontroller.

That is, a machine controller instance should be able to store different kinds of moves
that get executed differently.
"""

class Move(object):
    """
    Simple data structure for holding rml move information
    """
    def __init__(self, x = None, y = None, z = None, rate = 1):
        self.x = x
        self.y = y
        self.z = z
        self.rate = rate
    
    def __unicode__(self):
        return "x=%s, y=%s, z=%s at %s" % (self.x, self.y, self.z, self.rate)
