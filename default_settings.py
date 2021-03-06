#
# Override these settings by creating settings.py. Variables deinfed in settings.py
# will automatically override these default settings.
#
# settings.py should not be version controlled
#

# If True, will print more verbose messages to the console about what's going on.
LOG = True

# If True, will not attempt to communicate over the serial port
USE_SERIAL = False

# Serial port number 
SERIAL_PORT = 3

# Try to import local environment settings
try:
    from settings import *
except:
    pass
