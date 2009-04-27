
import math
import pygame

class Drawer(object):
    """
    Draw circuitboard in window. Currently for debug, but eventually for shock and awe.
    Requires pygame.
    """
    
    def __init__(self, window, pen_zoom_pairs={}):
        """
        Initializes window and drawing parameters, including displaying a pygame window.
        """
        self.max_x = 840
        self.max_y = 680
        
        self.zooms = {}
        for pen, zoom in pen_zoom_pairs:
            self.zooms[pen] = zoom
            
        # line color when pen up unless more sophisticated coloring is occuring
        self.up = (255, 255, 255)
        # line color when pen down unless more sophisticated coloring is occuring
        self.down = (255, 0, 0)
        # True if pen is up, False if pen is down
        self.is_ups = {}
        # current pen location along x axis
        self.xs = {}
        # current pen location along y axis
        self.ys = {}
        
        self.window = window
        
    def init_pen(self, pen, zoom):
        self.xs[pen] = int(self.max_x / 4.0) 
        self.ys[pen] = int(self.max_y / 4.0)
        self.is_ups[pen] = True
        if not pen in self.zooms:
            self.zooms[pen] = zoom
        
    def pen_up(self, pen):
        self.is_ups[pen] = True
        
    def pen_down(self, pen):
        self.is_ups[pen] = False
    
    def goto(self, x, y, pen, relative=True, zoom=None, rate=None, movetime=None):
        """
        Draws a line (x, y) from the current pen position. x and y are assumed to be 
        relative to current position.
        
        @param x: int
        @param y: int
        @param rate: 
        @param movetime: 
        """
        if not pen in self.xs:
            self.init_pen(pen, zoom)
    
        if rate and movetime:
            diffx = abs(self.xs[pen] - x)
            diffy = abs(self.ys[pen] - y)
            h = math.sqrt(diffx*diffx + diffy*diffy)

            nrate = round(rate)
           #print "ABC", self.is_ups[pen], nrate, "   ", h, "      ", rate
            hr = rate / 9.0 * 255
            #hr = h/rate
            #hr = (h*rate / 2500) * 255
            #hr = movetime/rate * 200
            
            if hr > 255:
                hr = 255
            if hr < 0:
                hr = 0
            hg = hb = self.is_ups[pen] and hr or 0
            color = (hr, hg, hb)
            ret = hr
        else:
            color = self.is_ups[pen] and self.up or self.down
            ret = 0
        #pygame.draw.line(self.window, (255,255,255), (self.x, self.y), (self.x+self.zoom*x, self.y+self.zoom*y), 4)
        if relative:
            pygame.draw.line(self.window, color, (self.xs[pen], self.ys[pen]), (self.xs[pen]+self.zooms[pen]*x, self.ys[pen]+self.zooms[pen]*y), 1)
            self.xs[pen] += self.zooms[pen]*x
            self.ys[pen] += self.zooms[pen]*y
        else:
            pygame.draw.line(self.window, color, (self.xs[pen], self.ys[pen]), (self.zooms[pen]*x, self.zooms[pen]*y), 1)
    
        # update window
        pygame.display.flip()
        
        return ret / 1000.0 

    def pause_for_space(self):
        """
        sleeps until SPACEBAR is pressed
        """
        while True:
            for event in pygame.event.get(): 
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return True
            time.sleep(.2)

    def check_event(self, event):
        """
        none currently.
        """
        pass
    