#!/usr/bin/env python
#
# cad.py
#
# Neil Gershenfeld
#
# (c) Massachusetts Institute of Technology 2006
# Permission granted for experimental and personal use;
# license for commercial sale available from MIT.
#
# todo:
#
# STL export
# switch to numpy
# test .uni output
# image output
# clear .cad variables before executing
# anisotropic RML linewidths
# label positions for rectangular aspect ratio
# erase labels between draws
# auto/fixed scale, offsets
# check CutAbs Resonetics
# remove extra CR on .cad save
# cd .. path error
# clean up nesting of parens
# fix ps filling nested polygons
# ps filled polygons
# 3D DXF output
# 3D connector packages
# fix rot view refresh
# eps output
# bitmap laser output
# image drawing tools
# compare 4x CW<->CCW, inner<->outer orders
# xz, yz finish cut contours
# test camm, epi, ord to absolute units otuput
# sort toolpath starts for proximity
# include polygons
# overload operators
# 3D text primitives
#
DATE = "3/6/07"

from numarray import *
from numarray.convolve import *
from string import *
from Tkinter import *
from tkFileDialog import *
import Image, ImageTk, ImageDraw, ImageFont, ImageOps

class point:
   #
   # an xyz point
   #
   def __init__(self,x,y,z=0):
      self.x = x
      self.y = y
      self.z = z

class cad_variables:
   #
   # cad variables
   #
   def __init__(self):
      self.xmin = 0 # minimum x value to render
      self.xmax = 0 # maximum x value to render
      self.ymin = 0 # minimum y value to render
      self.ymax = 0 # maximum y value to render
      self.zmin = 0 # minimum z value to render
      self.zmax = 0 # maximum z value to render
      self.zlist = [] # z values to render
      self.nx = 0 # number of x points to render
      self.ny = 0 # number of y points to render
      self.nz = 1 # number of z points to render
      self.rz = 0 # perspective view z rotation (degrees)
      self.rx = 0 # perspective view x rotation (degrees)
      self.units = 'in' # file units
      self.function = '0' # cad function
      self.toolpaths = [] # toolpathst
      self.labels = [] # display labels
      self.image_r = array(0) # red array
      self.image_g = array(0) # green array
      self.image_b = array(0) # blue array
      self.image_min = 0 # image min value
      self.image_max = 0 # image max value
      self.stop = 0 # stop rendering
      self.nplot = 400 # plot window size
      self.inches_per_unit = 1.0 # file units
      self.views = 'xyzr'
   def view(self,arg):
      global canvas_xy,canvas_yz,canvas_xz,canvas_rot
      if (arg == 'xy'):
         view_frame3.grid_forget()
         view_frame2.grid(row=2,column=0)
         self.views = 'xy'
         self.nplot = 800
         canvas_xy = Canvas(view_frame2, width=self.nplot, height=self.nplot)
         imxy = Image.new("RGBX",(self.nplot,self.nplot),'black')
         image_xy = ImageTk.PhotoImage(imxy)
         canvas_xy.create_image(self.nplot/2,self.nplot/2,image=image_xy)
         canvas_xy.bind('<Motion>',msg_xy)
         canvas_xy.grid(row=1,column=1)
      elif (arg == 'xyzr'):
         view_frame2.grid_forget()
         view_frame3.grid(row=2,column=0)
         self.views = 'xyzr'
         self.nplot = 400
	 canvas_xy = Canvas(view_frame3, width=self.nplot, height=self.nplot)
	 canvas_yz = Canvas(view_frame3, width=self.nplot, height=self.nplot)
	 canvas_xz = Canvas(view_frame3, width=self.nplot, height=self.nplot)
	 canvas_rot = Canvas(view_frame3, width=self.nplot, height=cad.nplot)
	 imxy = Image.new("RGBX",(self.nplot,self.nplot),'black')
	 image_xy = ImageTk.PhotoImage(imxy)
	 canvas_xy.create_image(self.nplot/2,self.nplot/2,image=image_xy)
	 canvas_xy.bind('<Motion>',msg_xy)
	 canvas_xy.grid(row=1,column=1)
	 imyz = Image.new("RGBX",(self.nplot,self.nplot),'black')
	 image_yz = ImageTk.PhotoImage(imyz)
	 canvas_yz.create_image(self.nplot/2,self.nplot/2,image=image_yz)
	 canvas_yz.bind('<Motion>',msg_yz)
	 canvas_yz.grid(row=1,column=2)
	 imxz = Image.new("RGBX",(self.nplot,self.nplot),'black')
	 image_xz = ImageTk.PhotoImage(imxz)
	 canvas_xz.create_image(self.nplot/2,self.nplot/2,image=image_xz)
	 canvas_xz.bind('<Motion>',msg_xz)
	 canvas_xz.grid(row=2,column=1)
	 imrot = Image.new("RGBX",(self.nplot,self.nplot),'black')
	 image_rot = ImageTk.PhotoImage(imrot)
	 canvas_rot.create_image(self.nplot/2,self.nplot/2,image=image_rot)
	 canvas_rot.bind('<Motion>',msg_nomsg)
	 canvas_rot.grid(row=2,column=2)
      else:
         print "view not supported"          
   def nxplot(self):
      xwidth = self.xmax - self.xmin
      ywidth = self.ymax - self.ymin
      if (xwidth >= ywidth):
         n = self.nplot
      else:
         n = int(self.nplot*xwidth/float(ywidth))
      return n
   def nyplot(self):
      xwidth = self.xmax - self.xmin
      ywidth = self.ymax - self.ymin
      if (xwidth < ywidth):
         n = self.nplot
      else:
         n = int(self.nplot*ywidth/float(xwidth))
      return n
   def nzplot(self):
      xwidth = self.xmax - self.xmin
      zwidth = self.zmax - self.zmin
      n = int(self.nxplot()*zwidth/float(xwidth))
      return n

cad = cad_variables()

class cad_text:
   def __init__(self,x,y,z,text,size=10):
      self.x = x
      self.y = y
      self.z = z
      self.text = text
      self.size = size

class images_class:
   def __init__(self):
      self.xy = 0
      self.xz = 0
      self.yz = 0
      self.rot = 0

images = images_class()

class CA_states:
   #
   # CA state definition class
   #
   def __init__(self):
      self.empty = 0
      self.interior = 1
      self.edge = (1 << 1) # 2
      self.north = (1 << 2) # 4
      self.west = (2 << 2) # 8
      self.east = (3 << 2) # 12
      self.south = (4 << 2) # 16
      self.stop = (5 << 2) # 20
      self.corner = (6 << 2) # 24

class rule_table:
   #
   # CA rule table class
   #
   # 0 = empty
   # 1 = interior
   # 2 = edge
   # edge+direction = start
   #
   def __init__(self):
      self.table = zeros(2**(9*2))
      self.s = CA_states()
      #
      # 1 0:
      #
      # 011
      # 111
      # 111
      self.add_rule(0,1,1,1,1,1,1,1,1,self.s.north)
      # 101
      # 111
      # 111
      self.add_rule(1,0,1,1,1,1,1,1,1,self.s.east)
      #
      # 2 0's:
      #
      # 001
      # 111
      # 111
      self.add_rule(0,0,1,1,1,1,1,1,1,self.s.east)
      # 100
      # 111
      # 111
      self.add_rule(1,0,0,1,1,1,1,1,1,self.s.east)
      # 010
      # 111
      # 111
      self.add_rule(0,1,0,1,1,1,1,1,1,self.s.east)
      # 011
      # 110
      # 111
      self.add_rule(0,1,1,1,1,0,1,1,1,self.s.south)
      # 110
      # 011
      # 111
      self.add_rule(1,1,0,0,1,1,1,1,1,self.s.east)
      # 101
      # 011
      # 111
      self.add_rule(1,0,1,0,1,1,1,1,1,self.s.east)
      # 101
      # 110
      # 111
      self.add_rule(1,0,1,1,1,0,1,1,1,self.s.south)
      # 011
      # 111
      # 110
      self.add_rule(0,1,1,1,1,1,1,1,0,self.s.corner)
      # 011
      # 111
      # 101
      self.add_rule(0,1,1,1,1,1,1,0,1,self.s.north)
      # 110
      # 111
      # 101
      self.add_rule(1,1,0,1,1,1,1,0,1,self.s.west)
      # 101
      # 111
      # 110
      self.add_rule(1,0,1,1,1,1,1,1,0,self.s.south)
      # 101
      # 111
      # 011
      self.add_rule(1,0,1,1,1,1,0,1,1,self.s.east)
      #
      # 3 0's:
      #
      # 001
      # 011
      # 111
      self.add_rule(0,0,1,0,1,1,1,1,1,self.s.east)
      # 010
      # 011
      # 111
      self.add_rule(0,1,0,0,1,1,1,1,1,self.s.east)
      # 010
      # 110
      # 111
      self.add_rule(0,1,0,1,1,0,1,1,1,self.s.south)
      # 010
      # 111
      # 011
      self.add_rule(0,1,0,1,1,1,0,1,1,self.s.east)
      # 010
      # 111
      # 110
      self.add_rule(0,1,0,1,1,1,1,1,0,self.s.south)
      # 110
      # 011
      # 011
      self.add_rule(1,1,0,0,1,1,0,1,1,self.s.east)
      # 011
      # 110
      # 110
      self.add_rule(0,1,1,1,1,0,1,1,0,self.s.south)
      # 101
      # 011
      # 011
      self.add_rule(1,0,1,0,1,1,0,1,1,self.s.east)
      # 101
      # 110
      # 110
      self.add_rule(1,0,1,1,1,0,1,1,0,self.s.south)
      # 011
      # 011
      # 011
      self.add_rule(0,1,1,0,1,1,0,1,1,self.s.north)
      #
      # 4 0's:
      #
      # 001
      # 011
      # 011
      self.add_rule(0,0,1,0,1,1,0,1,1,self.s.east)
      # 100
      # 110
      # 110
      self.add_rule(1,0,0,1,1,0,1,1,0,self.s.south)
      # 010
      # 011
      # 011
      self.add_rule(0,1,0,0,1,1,0,1,1,self.s.east)
      # 010
      # 110
      # 110
      self.add_rule(0,1,0,1,1,0,1,1,0,self.s.south)
      # 001
      # 110
      # 110
      self.add_rule(0,0,1,1,1,0,1,1,0,self.s.south)
      # 100
      # 011
      # 011
      self.add_rule(1,0,0,0,1,1,0,1,1,self.s.east)
      #
      # 5 0's:
      #
      # 000 
      # 011
      # 011
      self.add_rule(0,0,0,0,1,1,0,1,1,self.s.east)
      #
      # edge states
      #
      # 200
      # 211
      # 211
      self.add_rule(2,0,0,2,1,1,2,1,1,self.s.east+self.s.edge)
      # 201
      # 211
      # 211
      self.add_rule(2,0,1,2,1,1,2,1,1,self.s.east+self.s.edge)
      # 210
      # 211
      # 211
      self.add_rule(2,1,0,2,1,1,2,1,1,self.s.east+self.s.edge)
      # 002
      # 112
      # 112
      self.add_rule(0,0,2,1,1,2,1,1,2,self.s.stop)
      # 102
      # 112
      # 112
      self.add_rule(1,0,2,1,1,2,1,1,2,self.s.stop)
      # 002
      # 112
      # 102
      self.add_rule(0,0,2,1,1,2,1,0,2,self.s.stop)
      # 012
      # 112
      # 112
      self.add_rule(0,1,2,1,1,2,1,1,2,self.s.stop)
      # 012
      # 112
      # 102
      self.add_rule(0,1,2,1,1,2,1,0,2,self.s.stop)

   def add_rule(self,nw,nn,ne,ww,cc,ee,sw,ss,se,rule):
      #
      # add a CA rule, with rotations
      #
      s = CA_states()
      #
      # add the rule
      #
      state = \
         (nw <<  0) + (nn <<  2) + (ne <<  4) + \
         (ww <<  6) + (cc <<  8) + (ee << 10) + \
         (sw << 12) + (ss << 14) + (se << 16)
      self.table[state] = rule
      #
      # rotate 90 degrees
      # 
      state = \
         (sw <<  0) + (ww <<  2) + (nw <<  4) + \
         (ss <<  6) + (cc <<  8) + (nn << 10) + \
         (se << 12) + (ee << 14) + (ne << 16)
      if (rule == s.east):
         self.table[state] = s.south
      elif (rule == s.south):
         self.table[state] = s.west
      elif (rule == s.west):
         self.table[state] = s.north
      elif (rule == s.north):
         self.table[state] = s.east
      elif (rule == (s.east+s.edge)):
         self.table[state] = s.south+s.edge
      elif (rule == (s.south+s.edge)):
         self.table[state] = s.west+s.edge
      elif (rule == (s.west+s.edge)):
         self.table[state] = s.north+s.edge
      elif (rule == (s.north+s.edge)):
         self.table[state] = s.east+s.edge
      elif (rule == s.corner):
         self.table[state] = s.corner
      elif (rule == s.stop):
         self.table[state] = s.stop
      #
      # rotate 180 degrees
      # 
      state = \
         (se <<  0) + (ss <<  2) + (sw <<  4) + \
         (ee <<  6) + (cc <<  8) + (ww << 10) + \
         (ne << 12) + (nn << 14) + (nw << 16)
      if (rule == s.east):
         self.table[state] = s.west
      elif (rule == s.south):
         self.table[state] = s.north
      elif (rule == s.west):
         self.table[state] = s.east
      elif (rule == s.north):
         self.table[state] = s.south
      elif (rule == (s.east+s.edge)):
         self.table[state] = s.west+s.edge
      elif (rule == (s.south+s.edge)):
         self.table[state] = s.north+s.edge
      elif (rule == (s.west+s.edge)):
         self.table[state] = s.east+s.edge
      elif (rule == (s.north+s.edge)):
         self.table[state] = s.south+s.edge
      elif (rule == s.corner):
         self.table[state] = s.corner
      elif (rule == s.stop):
         self.table[state] = s.stop
      #
      # rotate 270 degrees
      # 
      state = \
         (ne <<  0) + (ee <<  2) + (se <<  4) + \
         (nn <<  6) + (cc <<  8) + (ss << 10) + \
         (nw << 12) + (ww << 14) + (sw << 16)
      if (rule == s.east):
         self.table[state] = s.north
      elif (rule == s.south):
         self.table[state] = s.east
      elif (rule == s.west):
         self.table[state] = s.south
      elif (rule == s.north):
         self.table[state] = s.west
      elif (rule == (s.east+s.edge)):
         self.table[state] = s.north+s.edge
      elif (rule == (s.south+s.edge)):
         self.table[state] = s.east+s.edge
      elif (rule == (s.west+s.edge)):
         self.table[state] = s.south+s.edge
      elif (rule == (s.north+s.edge)):
         self.table[state] = s.west+s.edge
      elif (rule == s.corner):
         self.table[state] = s.corner
      elif (rule == s.stop):
         self.table[state] = s.stop

def evaluate_state(array):
   #
   # assemble the state bit strings
   #
   (ny, nx) = shape(array)
   s = CA_states()
   nn = concatenate(([s.edge+zeros(nx)],array[:(ny-1)]))
   ss = concatenate((array[1:],[s.edge+zeros(nx)]))
   ww = concatenate((reshape(s.edge+zeros(ny),(ny,1)),array[:,:(nx-1)]),1)
   ee = concatenate((array[:,1:],reshape(s.edge+zeros(ny),(ny,1))),1)
   cc = array
   nw = concatenate(([s.edge+zeros(nx)],ww[:(ny-1)]))
   ne = concatenate(([s.edge+zeros(nx)],ee[:(ny-1)]))
   sw = concatenate((ww[1:],[s.edge+zeros(nx)]))
   se = concatenate((ee[1:],[s.edge+zeros(nx)]))
   state = (nw <<  0) + (nn <<  2) + (ne <<  4) + \
            (ww <<  6) + (cc <<  8) + (ee << 10) + \
            (sw << 12) + (ss << 14) + (se << 16)
   return state

def vectorize_toolpaths(array):
   #
   # convert lattice toolpath directions to vectors
   #
   s = CA_states()
   toolpaths = []
   max_dist = float(string_vector_error.get())
   start_sites = (array == (s.north+s.edge)) | (array == (s.south+s.edge)) | \
      (array == (s.east+s.edge)) | (array == (s.west+s.edge))
   num_start_sites = sum(sum(1.0*start_sites))
   path_sites = (array == s.north) | (array == s.south) | (array == s.east) | \
      (array == s.west)
   num_path_sites = sum(sum(1.0*path_sites))
   remaining_sites = num_start_sites + num_path_sites
   while (remaining_sites != 0):
      if (num_start_sites > 0):
         #
         # begin segment on a start state
         #
	 if (argmax(start_sites[0,:]) != 0):
	    x = argmax(start_sites[0,:])
	    y = 0
	 elif (argmax(start_sites[:,0]) != 0):
	    x = 0
	    y = argmax(start_sites[:,0])
	 elif (argmax(start_sites[-1,:]) != 0):
	    x = argmax(start_sites[-1,:])
	    y = cad.ny-1
	 elif (argmax(start_sites[:,-1]) != 0):
	    x = cad.nx-1
	    y = argmax(start_sites[:,-1])
	 else:
	    print "error: internal start"
	    sys.exit()
	 #print "start from ",x,y
      else:
         #
	 # no start states; begin segment on upper-left boundary point
	 #
         maxcols = argmax(path_sites)
         y = argmax(argmax(path_sites))
         x = maxcols[y]
	 array[y][x] += s.edge
	 #print "segment from ",x,y
      segment = [point(x,y)]
      vector = [point(x,y)]
      while 1:
         #
	 # follow path
	 #
	 """
	 x = 278
	 y = 5
	 window = 5
	 for i in range (y-window,y+window+1):
	    for j in range (x-window,x+window+1):
	       sys.stdout.write("%2d "%array[i][j])
	    sys.stdout.write("\n")
	 """
	 y = vector[-1].y
	 x = vector[-1].x
	 state = array[y][x]
	 #
	 # if start state, set stop
	 #
	 if (state == (s.north + s.edge)):
	    state = s.north
	    array[y][x] = s.stop
	 elif (state == (s.south + s.edge)):
	    state = s.south
	    array[y][x] = s.stop
	 elif (state == (s.east + s.edge)):
	    state = s.east
	    array[y][x] = s.stop
	 elif (state == (s.west + s.edge)):
	    state = s.west
	    array[y][x] = s.stop
	 #print "x,y,state,array: ",x,y,state,array[y][x]
	 #
	 # move if a valid direction
	 #
         if (state == s.north):
	    direction = "north"
	    #print "north"
	    ynew = y - 1
	    xnew = x
         elif (state == s.south):
	    direction = "south"
	    #print "south"
            ynew = y + 1
	    xnew = x
         elif (state == s.east):
	    direction = "east"
	    #print "east"
	    ynew = y
            xnew = x + 1
         elif (state == s.west):
	    direction = "west"
	    #print "west"
	    ynew = y
            xnew = x - 1
         elif (state == s.corner):
	    #print "corner"
	    if (direction == "east"):
	       #print "south"
	       xnew = x
	       ynew = y + 1
	    elif (direction == "west"):
	       #print "north"
	       xnew = x
	       ynew = y - 1
	    elif (direction == "north"):
	       #print "east"
	       ynew = y
	       xnew = x + 1
	    elif (direction == "south"):
	       #print "west"
	       ynew = y
	       xnew = x - 1
	 else:
	    #
	    # not a valid direction, terminate segment on previous point
	    #
            print "unexpected path termination at",x,y
	    #sys.exit()
	    segment.append(point(x,y))
	    toolpaths.append(segment)
            array[y][x] = s.interior
	    break
	 #print "xnew,ynew,snew",xnew,ynew,array[ynew][xnew]
	 #
	 # check if stop reached
	 #
         if (array[ynew][xnew] == s.stop):
	    #print "stop at ",xnew,ynew
	    segment.append(point(xnew,ynew))
	    toolpaths.extend([segment])
            if (state != s.corner):
	       array[y][x] = s.interior
            array[ynew][xnew] = s.interior
	    break
	 #
	 # find max transverse distance from vector to new point
	 #
	 dmax = 0
	 dx = xnew - vector[0].x
	 dy = ynew - vector[0].y
	 norm = sqrt(dx**2 + dy**2)
	 nx = dy / norm
	 ny = -dx / norm
	 for i in range(len(vector)):
	    dx = vector[i].x - vector[0].x
	    dy = vector[i].y - vector[0].y
	    d = abs(nx*dx + ny*dy)
	    if (d > dmax):
	       dmax = d
	 #
         # start new vector if transverse distance > max_dist
         #
	 if (dmax >= max_dist):
	    #print "max at ",x,y
	    segment.append(point(x,y))
	    vector = [point(x,y)]
	 #
         # otherwise add point to vector
         #
	 else:
	    #print "add ",xnew,ynew
	    vector.append(point(xnew,ynew))
            if ((array[y][x] != s.corner) & (array[y][x] != s.stop)):
               array[y][x] = s.interior
      start_sites = (array == (s.north+s.edge)) | (array == (s.south+s.edge)) | \
         (array == (s.east+s.edge)) | (array == (s.west+s.edge))
      num_start_sites = sum(sum(1.0*start_sites))
      path_sites = (array == s.north) | (array == s.south) | (array == s.east) | \
         (array == s.west)
      num_path_sites = sum(sum(1.0*path_sites))
      remaining_sites = num_start_sites + num_path_sites
   #
   # reverse segment order, to start from inside to out
   #
   newpaths = []
   for segment in range(len(toolpaths)):
      newpaths.append(toolpaths[-1-segment])
   root.update()
   return newpaths

def evaluate():
   #
   # evaluate .cad program/image
   #
   if (len(widget_cad_text.get("1.0",END)) > 1):
      #
      # .cad
      #
      cad_text_string = widget_cad_text.get("1.0",END)
      exec cad_text_string in globals()
      widget_function_text.config(state=NORMAL)
      widget_function_text.delete("1.0",END)
      widget_function_text.insert("1.0",cad.function)
      widget_function_text.config(state=DISABLED)
   if (cad.image_r.size() > 1):
      #
      # image 
      #
      cad.xmin = float(string_image_xmin.get())
      xwidth = float(string_image_xwidth.get())
      cad.xmax = cad.xmin + xwidth
      cad.ymin = float(string_image_ymin.get())
      yheight = float(string_image_yheight.get())
      cad.ymax = cad.ymin + yheight
      cad.image_min = float(string_image_min.get())
      cad.image_max = float(string_image_max.get())
      cad.zmin = float(string_image_zmin.get())
      cad.zmax = float(string_image_zmax.get())
      cad.nz = int(string_image_nz.get())
      cad.inches_per_unit = float(string_image_units.get())

def render(view='xyzr'):
   render_stop_flag = 0
   cad.stop = 0
   #
   # if .cad doesn't call render, delete windows and add stop button
   #
   if (find(widget_cad_text.get("1.0",END),"render(") == -1):
      widget_stop.pack()
      delete_windows()
   #
   # initialize variables
   #
   cad.toolpaths = []
   cad.zlist = []
   rx = pi*cad.rx/180.
   rz = pi*cad.rz/180.
   r = rule_table()
   s = CA_states()
   #
   # evaluate coordinate arrays
   #
   Xarray = outerproduct(ones((cad.ny,1)),cad.xmin+(cad.xmax-cad.xmin)*arange(cad.nx)/(cad.nx-1.0))
   Yarray = outerproduct(cad.ymin+(cad.ymax-cad.ymin)*arange(cad.ny-1,-1,-1)/(cad.ny-1.0),ones((1,cad.nx)))
   if (cad.zlist == []):
      if ((cad.nz == 1) & (cad.image_r.size() != 1)):
         cad.zlist = [(cad.zmax+cad.zmin)/2.0]
         cad.view('xy')
      elif (cad.nz == 1):
         cad.zlist = [cad.zmin]
         cad.view('xy')
      else:
         cad.zlist = cad.zmin + (cad.zmax-cad.zmin)*arange(cad.nz)/(cad.nz-1.0)
         cad.view('xyzr')
   else:
      cad.nz = len(cad.zlist)
   #
   # draw orthogonal views
   #
   X = Xarray
   Y = Yarray
   accum_r = zeros((cad.ny,cad.nx))
   accum_g = zeros((cad.ny,cad.nx))
   accum_b = zeros((cad.ny,cad.nx))
   intensity_yz = zeros((cad.ny,cad.nz))
   intensity_xz = zeros((cad.nz,cad.nx))
   for layer in range(cad.nz):
      #
      # check render stop button
      #
      if (cad.stop == 1):
         break
      #
      # xy view
      #
      Z = cad.zlist[layer]
      string_msg.set("render z = %.3f"%Z)
      root.update()
      if (cad.image_r.size() == 1):
         array_r = eval(cad.function)
	 array_g = array_r
	 array_b = array_r
         if ((cad.zmax == cad.zmin) | (cad.nz == 1)):
            zi = 255
         else:
            zi = int(255.0*layer/(cad.nz-1.0))
         accum_r = where(((zi*array_r) > accum_r),(zi*array_r),accum_r)
         accum_g = where(((zi*array_g) > accum_g),(zi*array_g),accum_g)
         accum_b = where(((zi*array_b) > accum_b),(zi*array_b),accum_b)
         intensity = (1 << 16)*accum_b + (1 << 8)*accum_g + (1 << 0)*accum_r
      else:
         array_r = (cad.image_r >= (cad.image_min + (cad.image_max-cad.image_min)*(Z-cad.zmin)/float(cad.zmax-cad.zmin)))
         array_g = (cad.image_g >= (cad.image_min + (cad.image_max-cad.image_min)*(Z-cad.zmin)/float(cad.zmax-cad.zmin)))
         array_b = (cad.image_b >= (cad.image_min + (cad.image_max-cad.image_min)*(Z-cad.zmin)/float(cad.zmax-cad.zmin)))
         image_z = int(cad.image_min + (cad.image_max-cad.image_min)*(Z-cad.zmin)/float(cad.zmax-cad.zmin))
         intensity_r = where((cad.image_r <= image_z),cad.image_r,image_z)
         intensity_g = where((cad.image_g <= image_z),cad.image_g,image_z)
         intensity_b = where((cad.image_b <= image_z),cad.image_b,image_z)
         intensity = (1 << 16)*intensity_b + (1 << 8)*intensity_g + (1 << 0)*intensity_r
      im_xy = Image.frombuffer("RGBX",(cad.nx,cad.ny),intensity)
      im_xy = im_xy.transpose(Image.FLIP_TOP_BOTTOM)
      im_xy_draw = ImageDraw.Draw(im_xy)
      #im_xy = im_xy.resize((cad.nplot,cad.nplot),Image.ANTIALIAS)
      im_xy = im_xy.resize((cad.nxplot(),cad.nyplot()))
      images.xy = ImageTk.PhotoImage(im_xy)
      canvas_xy.create_image(cad.nplot/2,cad.nplot/2,image=images.xy)
      root.update()
      #
      # find toolpaths if needed
      #
      ncontours = int(string_num_contours.get())
      if (ncontours == -1):
         ncontours = 2**20 # a big number
      cad.toolpaths.append([])
      for contour in range(ncontours):
         #
         # check render stop button
         #
         if (cad.stop == 1):
            break
         #
	 # convolve tool for contour
	 #
         string_msg.set(" convolve tool ... ")
	 root.update()
	 tool_rad = float(string_tool_dia.get())/2.0
	 tool_dia = float(string_tool_dia.get())
	 tool_overlap = float(string_tool_overlap.get())
	 kernel_rad = tool_rad + contour*tool_overlap*tool_dia
	 ikernel_rad = 1 + int(cad.nx*kernel_rad/(cad.xmax-cad.xmin))
	 if (ikernel_rad > (((cad.nx/2),(cad.ny/2))[(cad.ny/2) > (cad.nx/2)])):
	    break
	 k = ones((2*ikernel_rad,2*ikernel_rad)).astype(Bool)
	 kx = 1+outerproduct(ones((2*ikernel_rad,1)),arange(2*ikernel_rad))
	 ky = 1+outerproduct(arange(2*ikernel_rad),ones((1,2*ikernel_rad)))
	 k = ((kx-ikernel_rad)**2 + (ky-ikernel_rad)**2) < ikernel_rad**2
	 interior = (array_r == s.interior)
	 conv = convolve2d(interior,k,fft=1)
	 conv = (.5+conv).astype(UInt32)
	 conv = s.interior * conv.astype(Bool)
	 conv_array = conv + (conv != s.interior)*array_r
         #
	 # use CA rule table to find edge directions
	 #
         string_msg.set("  follow edges ... ")
	 root.update()
         state = evaluate_state(conv_array)
	 toolpath = r.table[state]
	 tool_array = toolpath + (toolpath == s.empty)*conv_array
         tool_intensity = \
              ((0 << 16) +   (0 << 8) +   (0 << 0))*(tool_array == s.empty) +\
            ((255 << 16) + (255 << 8) + (255 << 0))*(tool_array == s.interior) +\
            ((  0 << 16) + (  0 << 8) + (255 << 0))*(tool_array == s.north) +\
            ((  0 << 16) + (255 << 8) + (  0 << 0))*(tool_array == s.south) +\
            ((255 << 16) + (  0 << 8) + (  0 << 0))*(tool_array == s.east) +\
            ((  0 << 16) + (255 << 8) + (255 << 0))*(tool_array == s.west) +\
            ((128 << 16) + (  0 << 8) + (128 << 0))*(tool_array == s.stop)
	 """
	 #
	 # show CA
	 #
         im_xy = Image.frombuffer("RGBX",(cad.nx,cad.ny),tool_intensity)
         im_xy = im_xy.transpose(Image.FLIP_TOP_BOTTOM)
         im_xy = im_xy.resize((cad.nplot,cad.nplot))
         im_xy = im_xy.resize((cad.nplot,cad.nplot))
         images.xy = ImageTk.PhotoImage(im_xy)
         canvas_xy.create_image(cad.nplot/2,cad.nplot/2,image=images.xy)
	 """
	 #
	 # vectorize contour
	 #
         string_msg.set("    vectorize ...    ")
	 root.update()
         new_paths = vectorize_toolpaths(tool_array)
	 if (len(new_paths) == 0):
	    break
	 cad.toolpaths[layer].extend(new_paths)
         #
	 # draw toolpath
	 #
         im_xy_draw = ImageDraw.Draw(im_xy)
         for segment in range(len(cad.toolpaths[layer])):
            x = cad.nxplot()*(cad.toolpaths[layer][segment][0].x+0.5)/float(cad.nx)
            y = cad.nyplot()*(cad.toolpaths[layer][segment][0].y+0.5)/float(cad.ny)
            for vertex in range(1,len(cad.toolpaths[layer][segment])):
               xnew = cad.nxplot()*(cad.toolpaths[layer][segment][vertex].x+0.5)/float(cad.nx)
               ynew = cad.nyplot()*(cad.toolpaths[layer][segment][vertex].y+0.5)/float(cad.ny)
               im_xy_draw.line([x,y,xnew,ynew],fill="#ffa0a0",width=1)
               x = xnew
               y = ynew
         #
         # show xy toolpath view
         #
         images.xy = ImageTk.PhotoImage(im_xy)
         canvas_xy.create_image(cad.nplot/2,cad.nplot/2,image=images.xy)
	 #
	 # add send_to button
	 #
	 send_to_frame.pack()
	 root.update()
      #
      # draw labels
      #
      for label in range(len(cad.labels)):
	 x = cad.nplot/2. + cad.nxplot()*(cad.labels[label].x-(cad.xmax+cad.xmin)/2.0)/(cad.xmax-cad.xmin)
	 y = cad.nplot/2. - cad.nyplot()*(cad.labels[label].y-(cad.ymax+cad.ymin)/2.0)/(cad.ymax-cad.ymin)
	 string = cad.labels[label].text
	 size = cad.labels[label].size
         canvas_xy.create_text(x,y,text=string,font=('arial',size,'bold'),fill='#ff0000',anchor=CENTER,justify=CENTER)
      #
      # draw origin
      #
      x0 = cad.nplot/2. + cad.nxplot()*(0-(cad.xmax+cad.xmin)/2.)/(cad.xmax-cad.xmin)
      y0 = cad.nplot/2. - cad.nyplot()*(0-(cad.ymax+cad.ymin)/2.)/(cad.ymax-cad.ymin)
      dxy = .025*cad.nplot
      canvas_xy.create_line([x0-dxy,y0,x0+dxy,y0],fill="green")
      canvas_xy.create_line([x0,y0-dxy,x0,y0+dxy],fill="green")
      #
      # yz view
      #
      if (cad.views == 'xyzr'):
         accum_yz_r = zeros(cad.ny)
         accum_yz_g = zeros(cad.ny)
         accum_yz_b = zeros(cad.ny)
         for vertex in range(cad.nx):
            xi = 55 + int(200.0*vertex/(cad.nx-1.0))
            slice_r = array_r[:,vertex]
            slice_g = array_g[:,vertex]
            slice_b = array_b[:,vertex]
            accum_yz_r = where(((xi*slice_r) >= accum_yz_r),(xi*slice_r),accum_yz_r)
            accum_yz_g = where(((xi*slice_g) >= accum_yz_g),(xi*slice_g),accum_yz_g)
            accum_yz_b = where(((xi*slice_b) >= accum_yz_b),(xi*slice_b),accum_yz_b)
         intensity_yz[:,layer] = (1 << 16)*accum_yz_b + (1 << 8)*accum_yz_g + (1 << 0)*accum_yz_r
         im_yz = Image.frombuffer("RGBX",(cad.nz,cad.ny),intensity_yz)
         im_yz = im_yz.transpose(Image.FLIP_TOP_BOTTOM)
         im_yz = im_yz.transpose(Image.FLIP_LEFT_RIGHT)
         im_yz = im_yz.resize((cad.nzplot(),cad.nyplot()))
         images.yz = ImageTk.PhotoImage(im_yz)
         canvas_yz.create_image(cad.nplot/2,cad.nplot/2,image=images.yz)
         #
         # draw origin
         #
         z0 = cad.nplot/2. - cad.nzplot()*(0-(cad.zmax+cad.zmin)/2.)/(cad.zmax-cad.zmin)
         y0 = cad.nplot/2. - cad.nyplot()*(0-(cad.ymax+cad.ymin)/2.)/(cad.ymax-cad.ymin)
         canvas_yz.create_line([z0-dxy,y0,z0+dxy,y0],fill="green")
         canvas_yz.create_line([z0,y0-dxy,z0,y0+dxy],fill="green")
      #
      # xz view
      #
      if (cad.views == 'xyzr'):
         accum_xz_r = zeros(cad.nx)
         accum_xz_g = zeros(cad.nx)
         accum_xz_b = zeros(cad.nx)
         for vertex in range(cad.ny):
#            yi = 55 + int(200.0*vertex/(cad.ny-1.0))
            yi = int(255.0*vertex/(cad.ny-1.0))
	    slice_r = array_r[vertex,:]
	    slice_g = array_g[vertex,:]
	    slice_b = array_b[vertex,:]
            accum_xz_r = where(((yi*slice_r) >= accum_xz_r),(yi*slice_r),accum_xz_r)
            accum_xz_g = where(((yi*slice_g) >= accum_xz_g),(yi*slice_g),accum_xz_g)
            accum_xz_b = where(((yi*slice_b) >= accum_xz_b),(yi*slice_b),accum_xz_b)
         intensity_xz[(cad.nz-1-layer),:] = (1 << 16)*accum_xz_b + (1 << 8)*accum_xz_g + (1 << 0)*accum_xz_r
         im_xz = Image.frombuffer("RGBX",(cad.nx,cad.nz),intensity_xz)
         im_xz = im_xz.transpose(Image.FLIP_TOP_BOTTOM)
         im_xz = im_xz.resize((cad.nxplot(),cad.nzplot()))
         images.xz = ImageTk.PhotoImage(im_xz)
         canvas_xz.create_image(cad.nplot/2,cad.nplot/2,image=images.xz)
         #n
         # draw origin
         #
         x0 = cad.nplot/2. + cad.nxplot()*(0-(cad.xmax+cad.xmin)/2.)/(cad.xmax-cad.xmin)
         z0 = cad.nplot/2. - cad.nzplot()*(0-(cad.zmax+cad.zmin)/2.)/(cad.zmax-cad.zmin)
         canvas_xz.create_line([x0-dxy,z0,x0+dxy,z0],fill="green")
         canvas_xz.create_line([x0,z0-dxy,x0,z0+dxy],fill="green")
      #
      # draw it
      #
      root.update()
   #
   # rotated view
   #
   if (cad.views == 'xyzr'):
      accum = zeros((cad.ny,cad.nx))
      for Z in cad.zlist:
         #
         # check render stop button
         #
         if (cad.stop == 1):
            break
         string_msg.set("render z = %.3f"%Z)
         dY = cos(rx)*(Yarray-(cad.ymax+cad.ymin)/2.0) - sin(rx)*(Z-(cad.zmax+cad.zmin)/2.0)
         Z = (cad.zmax+cad.zmin)/2.0 + sin(rx)*(Yarray-(cad.ymax+cad.ymin)/2.0) + cos(rx)*(Z-(cad.zmax+cad.zmin)/2.0)
         X = (cad.xmax+cad.xmin)/2.0 + cos(rz)*(Xarray-(cad.xmax+cad.xmin)/2.0) - sin(rz)*dY
         Y = (cad.ymax+cad.ymin)/2.0 + sin(rz)*(Xarray-(cad.xmax+cad.xmin)/2.0) + cos(rz)*dY
         array = eval(cad.function)
         if (cad.zmax == cad.zmin):
            zi = 255
         else:
            zi = 55 + 245.0*(Z-cad.zmin)/(cad.zmax-cad.zmin)
            zi = zi.astype(UInt8)
         accum = where(((zi*array) > accum),(zi*array),accum)
         intensity = ((1 << 16) + (1 << 8) + (1 << 0)) * accum
         im_rot = Image.frombuffer("RGBX",(cad.nx,cad.ny),intensity)
         im_rot = im_rot.transpose(Image.FLIP_TOP_BOTTOM)
         #im_rot = im_rot.resize((cad.nplot,cad.nplot),Image.ANTIALIAS)
         im_rot = im_rot.resize((cad.nxplot(),cad.nyplot()))
         images.rot = ImageTk.PhotoImage(im_rot)
         canvas_rot.create_image(cad.nplot/2,cad.nplot/2,image=images.rot)
         root.update()
   #
   # return
   #
   widget_stop.pack_forget()
   string_msg.set("done")
   root.update()
   return

def draw_toolpath():
   im_xy = Image.new("RGBX",(cad.nxplot(),cad.nyplot()),'white')
   im_xy_draw = ImageDraw.Draw(im_xy)
   for layer in range(len(cad.toolpaths)):
      for segment in range(len(cad.toolpaths[layer])):
         x = cad.nxplot()*(cad.toolpaths[layer][segment][0].x+0.5)/float(cad.nx)
         y = cad.nyplot()*(cad.toolpaths[layer][segment][0].y+0.5)/float(cad.ny)
         for vertex in range(1,len(cad.toolpaths[layer][segment])):
            xnew = cad.nxplot()*(cad.toolpaths[layer][segment][vertex].x+0.5)/float(cad.nx)
            ynew = cad.nyplot()*(cad.toolpaths[layer][segment][vertex].y+0.5)/float(cad.ny)
            im_xy_draw.line([x,y,xnew,ynew],fill="black")
            x = xnew
            y = ynew
   images.xy = ImageTk.PhotoImage(im_xy)
   canvas_xy.create_image(cad.nplot/2,cad.nplot/2,image=images.xy)

def delete_windows():
   im_xy = Image.new("RGBX",(cad.nplot,cad.nplot),'black')
   images.xy = ImageTk.PhotoImage(im_xy)
   canvas_xy.create_image(cad.nplot/2,cad.nplot/2,image=images.xy)
   im_yz = Image.new("RGBX",(cad.nplot,cad.nplot),'black')
   images.yz = ImageTk.PhotoImage(im_yz)
   canvas_yz.create_image(cad.nplot/2,cad.nplot/2,image=images.yz)
   im_xz = Image.new("RGBX",(cad.nplot,cad.nplot),'black')
   images.xz = ImageTk.PhotoImage(im_xz)
   canvas_xz.create_image(cad.nplot/2,cad.nplot/2,image=images.xz)
   im_rot = Image.new("RGBX",(cad.nplot,cad.nplot),'black')
   images.rot = ImageTk.PhotoImage(im_rot)
   canvas_rot.create_image(cad.nplot/2,cad.nplot/2,image=images.rot)
   root.update()

def select_cad():
   image_x_frame.pack_forget()
   image_y_frame.pack_forget()
   image_z_frame.pack_forget()
   image_intensity_frame.pack_forget()
   image_units_frame.pack_forget()
   image_invert_frame.pack_forget()
   widget_cad_text.delete("1.0",END)
   widget_cad_text.insert("1.0",cad_template)
   editor_frame.pack()
   cad.image = array(0)
   cad.toolpaths = []
   string_num_contours.set('0')
   widget_cad_save.pack(side='left')
   delete_windows()

def select_image():
   editor_frame.pack_forget()
   cad_input_frame.pack_forget()
   image_x_frame.pack()
   image_y_frame.pack()
   image_z_frame.pack()
   image_intensity_frame.pack()
   image_units_frame.pack()
   image_invert_frame.pack()
   cad_input_frame.pack()
   cad.toolpaths = []
   string_num_contours.set('0')
   widget_cad_save.pack_forget()
   delete_windows()

def input_open():
   filename = askopenfilename()
   string_input_file.set(filename)
   if (find(filename,'.cad') != -1):
      cad_load(0)
   elif ((find(filename,'.jpg') != -1) | (find(filename,'.JPG') != -1) |
      (find(filename,'.png') != -1) | (find(filename,'.PNG') != -1)):
      widget_cad_text.delete("1.0",END)
      image_load(0)
   else:
      string_msg.set("unsupported input file format")
      root.update()
      
def cad_load(event):
   cam_pack_forget()
   select_cad()
   input_file_name = string_input_file.get()
   input_file = open(input_file_name,'rb')
   cad_text_string = input_file.read()
   widget_cad_text.delete("1.0",END)
   widget_cad_text.insert("1.0",cad_text_string)
   input_file.close()
   cad.toolpaths = []
   cad.image = array(0)
   cad.nz = 1
   string_num_contours.set('0')
   evaluate()
   if (find(widget_cad_text.get("1.0",END),"render(") == -1):
      render()

def image_load(event):
   cam_pack_forget()
   select_image()
   function_string_frame.pack_forget()
   input_file_name = string_input_file.get()
   input_file = open(input_file_name,'rb')
   input_file.close()
   cad.toolpaths = []
   string_num_contours.set('0')
   image = Image.open(input_file_name)
   (cad.nx,cad.ny) = image.size
   info = image.info
   if ('dpi' in info):
      (xdpi,ydpi) = info['dpi']
   else:
      xdpi = cad.nx
      ydpi = xdpi
   string_image_nx.set(" nx = "+str(cad.nx))
   string_image_ny.set(" ny = "+str(cad.ny))
   cad.nz = 1
   string_image_nz.set(str(cad.nz))
   cad.xmin = 0
   string_image_xmin.set('0')
   cad.xmax = cad.nx/float(xdpi)
   string_image_xwidth.set(str(cad.xmax-cad.xmin))
   cad.ymin = 0
   string_image_ymin.set('0')
   cad.ymax = cad.ny/float(ydpi)
   string_image_yheight.set(str(cad.ymax-cad.ymin))
   cad.zmin = -1
   string_image_zmin.set('-1')
   cad.zmax = 0
   string_image_zmax.set('0')
   cad.inches_per_unit = 1.0
   string_image_units.set('1.0')
   data = array(image.getdata())
   if (len(shape(data)) == 1): # check or grayscale
      data = [data,data,data]
      data = transpose(data)
   cad.image_r = array(data[:,0],shape=(cad.ny,cad.nx))
   cad.image_g = array(data[:,1],shape=(cad.ny,cad.nx))
   cad.image_b = array(data[:,2],shape=(cad.ny,cad.nx))
   cad.image_min = 0
   string_image_min.set(str(cad.image_min))
   cad.image_max = 255
   string_image_max.set(str(cad.image_max))
   evaluate()
   render()

def invert_image(event):
   cad.image_r = 255 - cad.image_r
   cad.image_g = 255 - cad.image_g
   cad.image_b = 255 - cad.image_b
   evaluate()
   render()

def cad_save(event):
   input_file_name = string_input_file.get()
   input_file = open(input_file_name,'wb')
   cad_text_string = widget_cad_text.get("1.0",END)
   input_file.write(cad_text_string)
   input_file.close()
   string_msg.set(input_file_name+" saved")
   root.update()

def render_button(event):
   cam_pack_forget()
   if (cad.image_r.size() == 1):
      function_string_frame.pack()
   cad.toolpaths = []
   string_num_contours.set('0')
   evaluate()
   if (find(widget_cad_text.get("1.0",END),"render(") == -1):
      render()

def render_stop(event):
   cad.stop = 1
   widget_stop.pack_forget()
      
def cam(event):
   function_string_frame.pack_forget()
   cam_file_frame.pack()
   string_num_contours.set('1')
   root.update()

def contour(event):
   evaluate()
   if (find(widget_cad_text.get("1.0",END),"render(") == -1):
      render()

def triangulate(event):
   evaluate()
   voxel_size = int(string_STL_voxel.get())
   im_xy = Image.new("RGBX",(cad.nxplot(),cad.nyplot()),'white')
   im_xy_draw = ImageDraw.Draw(im_xy)
   im_xz = Image.new("RGBX",(cad.nxplot(),cad.nzplot()),'white')
   im_xz_draw = ImageDraw.Draw(im_xz)
   im_yz = Image.new("RGBX",(cad.nzplot(),cad.nyplot()),'white')
   im_yz_draw = ImageDraw.Draw(im_yz)
   index = arange(voxel_size+1,shape=(1,voxel_size+1))
   index_max = voxel_size*ones((1,voxel_size+1))
   index_min = zeros((1,voxel_size+1))
   edges_x = concatenate(( \
      index,index_max,index,index_min,index_max,index_max, \
      index_min,index_min,index,index_max,index,index_min))
   edges_y = concatenate(( \
      index_max,index,index_min,index,index_max,index_min, \
      index_min,index_max,index_max,index,index_min,index))
   edges_z = concatenate(( \
      index_max,index_max,index_max,index_max,index,index, \
      index,index,index_min,index_min,index_min,index_min))
   for k in range(0,cad.nz,voxel_size):
      Z = cad.zmin + (cad.zmax-cad.zmin)*(k+edges_z)/(cad.nz-1.0)
      string_msg.set("triangulate layer %d/%d"%(k,cad.nz))
      root.update()
      for j in range(0,cad.ny,voxel_size):
	 Y = cad.ymin + (cad.ymax-cad.ymin)*(j+edges_y)/(cad.ny-1.0)
         for i in range(0,cad.nx,voxel_size):
	    X = cad.xmin + (cad.xmax-cad.xmin)*(i+edges_x)/(cad.nx-1.0)
            edge_array = eval(cad.function)
	    edge_left = edge_array[:,:-1]
	    edge_right = edge_array[:,1:]
	    edges = (edge_left != edge_right)

	    xs = cad.nxplot()*(i+edges_x[edges]+0.5)/float(cad.nx)
	    ys = cad.nyplot()*(j+edges_y[edges]+0.5)/float(cad.ny)
	    zs = cad.nzplot() - cad.nzplot()*(k+edges_z[edges]+0.5)/float(cad.nz)

	    """

	    if (len(xs) >= 3):

	       d1 = (xs[0]-xs[-1])**2 + (ys[0]-ys[-1])**2 + (zs[0]-zs[-1])**2

 	       dx0 = xs[0] - sum(xs)/len(xs)
	       dy0 = ys[0] - sum(ys)/len(ys)
	       dz0 = zs[0] - sum(zs)/len(zs)

	       dx1 = xs[0]-xs[-1]
	       dy1 = ys[0]-ys[-1]
	       dz1 = zs[0]-zs[-1]

	       cross_x = dy1*dz0 - dz1*dy0
	       cross_y = dz1*dx0 - dx1*dz0
	       cross_z = dx1*dy0 - dy1*dz0

	       trans_x = cross_y*dz0 - cross_z*dy0
	       trans_y = cross_z*dx0 - cross_x*dz0
	       trans_z = cross_x*dy0 - cross_y*dz0

	       if ((trans_x**2 + trans_y**2 + trans_z**2) == 0):
	          print '0',xs,ys,zs

	       print 't',trans_x,trans_y,trans_z

	       dots = []
	       for v in range(1,len(xs)):
	          d = sqrt((xs[v]-xs[0])**2 + (ys[v]-ys[0])**2 + (zs[v]-zs[0])**2)
	          dx = (xs[0]-xs[v])/d
	          dy = (ys[0]-ys[v])/d
	          dz = (zs[0]-zs[v])/d
	          dot = trans_x*dx + trans_y*dy + trans_z*dz
	          dots.append(dot)
               print dots

	    """

	    for v1 in range(0,len(xs)):
	       for v2 in range(1,len(xs)):
                  im_xy_draw.line([xs[v1],ys[v1],xs[v2],ys[v2]],fill="black")
                  im_xz_draw.line([xs[v1],zs[v1],xs[v2],zs[v2]],fill="black")
                  im_yz_draw.line([zs[v1],ys[v1],zs[v2],ys[v2]],fill="black")
      images.xy = ImageTk.PhotoImage(im_xy)
      images.xz = ImageTk.PhotoImage(im_xz)
      images.yz = ImageTk.PhotoImage(im_yz)
      canvas_xy.create_image(cad.nplot/2,cad.nplot/2,image=images.xy)
      canvas_xz.create_image(cad.nplot/2,cad.nplot/2,image=images.xz)
      canvas_yz.create_image(cad.nplot/2,cad.nplot/2,image=images.yz)
      im_rot = Image.new("RGBX",(cad.nplot,cad.nplot),'white')
      images.rot = ImageTk.PhotoImage(im_rot)
      canvas_rot.create_image(cad.nplot/2,cad.nplot/2,image=images.rot)
      root.update()
   string_msg.set("done")
   root.update()

def select_epi():
   input_file_name = string_input_file.get()
   string_cam_file.set(input_file_name[0:-4]+'.epi')
   cam_pack_forget()
   cam_file_frame.pack()
   cam_vector_frame.pack()
   cam_dia_frame.pack()
   cam_contour_frame.pack()
   laser_frame1.pack()
   laser_frame2.pack()
   string_laser_rate.set("2500")
   string_laser_power.set("50")
   string_laser_speed.set("50")
   string_tool_dia.set("0.01")
   root.update()

def select_camm():
   input_file_name = string_input_file.get()
   string_cam_file.set(input_file_name[0:-4]+'.camm')
   cam_pack_forget()
   cam_file_frame.pack()
   cam_vector_frame.pack()
   cam_dia_frame.pack()
   cam_contour_frame.pack()
   cut_frame.pack()
   string_cut_force.set("45")
   string_cut_velocity.set("2")
   string_tool_dia.set("0.01")
   root.update()

def select_ps():
   input_file_name = string_input_file.get()
   string_cam_file.set(input_file_name[0:-4]+'.ps')
   cam_pack_forget()
   cam_file_frame.pack()
   cam_vector_frame.pack()
   cam_dia_frame.pack()
   cam_contour_frame.pack()
   fill_frame.pack()
   string_tool_dia.set("0.0")
   root.update()

def select_ord():
   input_file_name = string_input_file.get()
   string_cam_file.set(input_file_name[0:-4]+'.ord')
   cam_pack_forget()
   cam_file_frame.pack()
   cam_vector_frame.pack()
   cam_dia_frame.pack()
   cam_contour_frame.pack()
   string_tool_dia.set("0.01")
   waterjet_frame.pack()
   string_lead_in.set("0.05")
   string_quality.set("-3")
   root.update()

def select_rml():
   input_file_name = string_input_file.get()
   string_cam_file.set(input_file_name[0:-4]+'.rml')
   cam_pack_forget()
   cam_file_frame.pack()
   cam_vector_frame.pack()
   cam_dia_frame.pack()
   cam_contour_frame.pack()
   speed_frame.pack()
   string_tool_dia.set("0.0156")
   string_xy_speed.set("4")
   string_z_speed.set("4")
   root.update()

def select_oms():
   input_file_name = string_input_file.get()
   string_cam_file.set(input_file_name[0:-4]+'.oms')
   cam_pack_forget()
   cam_file_frame.pack()
   cam_vector_frame.pack()
   cam_dia_frame.pack()
   cam_contour_frame.pack()
   excimer_frame.pack()
   string_pulse_period.set("10000")
   string_tool_dia.set("0.001")
   string_cut_vel.set("0.1")
   string_cut_accel.set("5.0")
   root.update()

def select_dxf():
   input_file_name = string_input_file.get()
   string_cam_file.set(input_file_name[0:-4]+'.dxf')
   cam_pack_forget()
   cam_file_frame.pack()
   cam_vector_frame.pack()
   cam_dia_frame.pack()
   cam_contour_frame.pack()
   string_tool_dia.set("0.0")
   root.update()

def select_uni():
   input_file_name = string_input_file.get()
   string_cam_file.set(input_file_name[0:-4]+'.uni')
   cam_pack_forget()
   cam_file_frame.pack()
   cam_vector_frame.pack()
   cam_dia_frame.pack()
   cam_contour_frame.pack()
   laser_frame1.pack()
   string_laser_rate.set("500")
   string_laser_power.set("10")
   string_laser_speed.set("10")
   string_tool_dia.set("0.01")
   root.update()

def select_gif():
   input_file_name = string_input_file.get()
   string_cam_file.set(input_file_name[0:-4]+'.gif')
   cam_pack_forget()
   cam_file_frame.pack()
   root.update()

def select_stl():
   input_file_name = string_input_file.get()
   string_cam_file.set(input_file_name[0:-4]+'.stl')
   cam_pack_forget()
   cam_file_frame.pack()
   string_STL_voxel.set("10")
   STL_frame.pack()
   root.update()

def cam_pack_forget():
   cam_file_frame.pack_forget()
   cam_vector_frame.pack_forget()
   cam_dia_frame.pack_forget()
   cam_contour_frame.pack_forget()
   laser_frame1.pack_forget()
   laser_frame2.pack_forget()
   cut_frame.pack_forget()
   speed_frame.pack_forget()
   waterjet_frame.pack_forget()
   excimer_frame.pack_forget()
   STL_frame.pack_forget()
   fill_frame.pack_forget()
   send_to_frame.pack_forget()

def save_cam(event):
   #
   # write toolpath
   #
   text = string_cam_file.get()
   if (find(text,".epi") != -1):
      write_epi()
   elif (find(text,".camm") != -1):
      write_camm()
   elif (find(text,".ps") != -1):
      write_ps()
   elif (find(text,".ord") != -1):
      write_ord()
   elif (find(text,".rml") != -1):
      write_rml()
   elif (find(text,".oms") != -1):
      write_oms()
   elif (find(text,".dxf") != -1):
      write_dxf()
   elif (find(text,".uni") != -1):
      write_uni()
   elif (find(text,".gif") != -1):
      write_gif()
   elif (find(text,".stl") != -1):
      write_stl()
   else:
      string_msg.set("unsupported output file format")
      root.update()

def write_epi():
   #
   # Epilog lasercutter output
   # todo: try 1200 DPI
   #
   units = 600*cad.inches_per_unit
   filename = string_cam_file.get()
   file = open(filename, 'wb')
   if (integer_laser_autofocus.get() == 0):
      #
      # init with autofocus off
      #
      file.write("%-12345X@PJL JOB NAME="+string_cam_file.get()+"\r\nE@PJL ENTER LANGUAGE=PCL\r\n&y0A&l0U&l0Z&u600D*p0X*p0Y*t600R*r0F&y50P&z50S*r6600T*r5100S*r1A*rC%1BIN;XR"+string_laser_rate.get()+";YP"+string_laser_power.get()+";ZS"+string_laser_speed.get()+";")
   else:
      #
      # init with autofocus on
      #
      file.write("%-12345X@PJL JOB NAME="+string_cam_file.get()+"\r\nE@PJL ENTER LANGUAGE=PCL\r\n&y1A&l0U&l0Z&u600D*p0X*p0Y*t600R*r0F&y50P&z50S*r6600T*r5100S*r1A*rC%1BIN;XR"+string_laser_rate.get()+";YP"+string_laser_power.get()+";ZS"+string_laser_speed.get()+";")
   for layer in range(len(cad.toolpaths)):
      for segment in range(len(cad.toolpaths[layer])):
         x = int(units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][0].x+0.5)/float(cad.nx)))
         y = int(units*(-cad.ymin - ((cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][0].y)+0.5)/float(cad.ny))))
         file.write("PU"+str(x)+","+str(y)+";")
         for vertex in range(1,len(cad.toolpaths[layer][segment])):
            x = int(units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][vertex].x+0.5)/float(cad.nx)))
            y = int(units*(-cad.ymin - ((cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][vertex].y)+0.5)/float(cad.ny))))
            file.write("PD"+str(x)+","+str(y)+";")
      file.write("%0B%1BPUE%-12345X@PJL EOJ \r\n")
   file.close()
   draw_toolpath()
   string_msg.set("wrote %s"%filename)
   root.update()

def write_camm():
   filename = string_cam_file.get()
   file = open(filename, 'wb')
   units = 1000*cad.inches_per_unit
   file.write("PA;PA;!ST1;!FS"+string_cut_force.get()+";VS"+string_cut_velocity.get()+";")
   for layer in range(len(cad.toolpaths)):
      for segment in range(len(cad.toolpaths[layer])):
         x = int(units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][0].x+0.5)/float(cad.nx)))
         y = int(units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][0].y)+0.5)/float(cad.ny)))
         file.write("PU"+str(x)+","+str(y)+";")
         for vertex in range(1,len(cad.toolpaths[layer][segment])):
            x = int(units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][vertex].x+0.5)/float(cad.nx)))
            y = int(units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][vertex].y)+0.5)/float(cad.ny)))
            file.write("PD"+str(x)+","+str(y)+";")
   file.write("PU0,0;")
   file.close()
   draw_toolpath()
   string_msg.set("wrote %s"%filename)
   root.update()

def write_ps():
   #
   # Postscript output
   #
   units = cad.inches_per_unit
   filename = string_cam_file.get()
   file = open(filename, 'wb')
   file.write("%! cad.py output\n")
   file.write("%%%%BoundingBox: 0 0 %.3f %.3f\n"%
      (72.0*(cad.xmax-cad.xmin),72.0*(cad.ymax-cad.ymin)))
   file.write("/m {moveto} def\n")
   file.write("/l {lineto} def\n")
   file.write("72 72 scale\n")
   file.write(".005 setlinewidth\n")
   file.write("%f %f translate\n"%(0.5,0.5))
   for layer in range(len(cad.toolpaths)):
      for segment in range(len(cad.toolpaths[layer])):
         x = units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][0].x+0.5)/float(cad.nx))
         y = units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][0].y)+0.5)/float(cad.ny))
         file.write("%f %f m\n"%(x,y))
         for vertex in range(1,len(cad.toolpaths[layer][segment])):
            x = units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][vertex].x+0.5)/float(cad.nx))
            y = units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][vertex].y)+0.5)/float(cad.ny))
            file.write("%f %f l\n"%(x,y))
	 if (integer_fill.get() == 0):
            file.write("stroke\n")
	 else:
            file.write("fill\n")
   file.write("showpage\n")
   file.close()
   draw_toolpath()
   string_msg.set("wrote %s"%filename)
   root.update()

def write_ord():
   #
   # OMAX waterjet output
   #
   units = cad.inches_per_unit
   lead_in = float(string_lead_in.get())
   quality = int(string_quality.get())
   filename = string_cam_file.get()
   file = open(filename, 'wb')
   xlead = []
   ylead = []
   for layer in range(len(cad.toolpaths)):
      for segment in range(len(cad.toolpaths[layer])):
         #
         # calculate and write lead-in
         #
         x0 = units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][0].x+0.5)/float(cad.nx))
         y0 = units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][0].y)+0.5)/float(cad.ny))
         x1 = units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][1].x+0.5)/float(cad.nx))
         y1 = units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][1].y)+0.5)/float(cad.ny))
         dx = x1 - x0
         dy = y1 - y0
         norm_x = -dy
         norm_y = dx
         norm = sqrt(norm_x**2 + norm_y**2)
         norm_x = norm_x/norm
         norm_y = norm_y/norm
         xlead.append(x0 + norm_x*lead_in)
         ylead.append(y0 + norm_y*lead_in)
         file.write("%f, %f, 0, %d\n"%(xlead[segment],ylead[segment],quality))
         #
         # loop over segment
         #
         for vertex in range(len(cad.toolpaths[layer][segment])):
            x = units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][vertex].x+0.5)/float(cad.nx))
            y = units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][vertex].y)+0.5)/float(cad.ny))
            file.write("%f, %f, 0, %d\n"%(x,y,quality))
         #
         # write lead-out
         #
         file.write("%f, %f, 0, 0\n"%(x0,y0))
         file.write("%f, %f, 0, 0\n"%(xlead[segment],ylead[segment]))
   file.close()
   #
   # draw toolpath with lead-in/out
   #
   im_xy = Image.new("RGBX",(cad.nxplot(),cad.nyplot()),'white')
   im_xy_draw = ImageDraw.Draw(im_xy)
   for layer in range(len(cad.toolpaths)):
      for segment in range(len(cad.toolpaths[layer])):
         x = cad.nxplot()*(cad.toolpaths[layer][segment][0].x+0.5)/float(cad.nx)
         y = cad.nyplot()*(cad.toolpaths[layer][segment][0].y+0.5)/float(cad.ny)
         xl = cad.nxplot()*(xlead[segment]-cad.xmin)/(cad.xmax-cad.xmin)
         yl = cad.nyplot()-cad.nyplot()*(ylead[segment]-cad.ymin)/(cad.ymax-cad.ymin)
         im_xy_draw.line([xl,yl,x,y],fill="black")
         for vertex in range(1,len(cad.toolpaths[layer][segment])):
            xnew = cad.nxplot()*(cad.toolpaths[layer][segment][vertex].x+0.5)/float(cad.nx)
            ynew = cad.nyplot()*(cad.toolpaths[layer][segment][vertex].y+0.5)/float(cad.ny)
            im_xy_draw.line([x,y,xnew,ynew],fill="black")
            x = xnew
            y = ynew
   images.xy = ImageTk.PhotoImage(im_xy)
   canvas_xy.create_image(cad.nplot/2,cad.nplot/2,image=images.xy)
   string_msg.set("wrote %s"%filename)
   root.update()

def write_rml():
   #
   # Roland Modela output
   #
   units = 1000*cad.inches_per_unit
   filename = string_cam_file.get()
   file = open(filename, 'wb')
   file.write("PA;PA;VS"+string_xy_speed.get()+";!VZ"+string_z_speed.get()+";!MC1;")
   #file.write("PA;PA;VS"+string_xy_speed.get()+";!VZ"+string_z_speed.get()+";!MC0;")
   zup = cad.zmax
   izup = int(units*zup)
   for layer in range(len(cad.zlist)-1,-1,-1):
      zdown = cad.zlist[layer]
      izdown = int(units*zdown)
      file.write("!PZ"+str(izdown)+","+str(izup)+";")
      #
      # follow toolpaths CCW, for CW tool motion
      #
      for segment in range(len(cad.toolpaths[layer])):      
         x = int(units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][0].x+0.5)/float(cad.nx)))
         y = int(units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][0].y)+0.5)/float(cad.ny)))
         file.write("PU"+str(x)+","+str(y)+";")
         for vertex in range(1,len(cad.toolpaths[layer][segment])):
            x = int(units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][vertex].x+0.5)/float(cad.nx)))
            y = int(units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][vertex].y)+0.5)/float(cad.ny)))
            file.write("PD"+str(x)+","+str(y)+";")
   file.write("PU"+str(x)+","+str(y)+";!MC0;")
   #
   # file padding hack for end-of-file buffering problems
   #
   for i in range(750):
      file.write("!MC0;")
   file.close()
   draw_toolpath()
   string_msg.set("wrote %s"%filename)
   root.update()

def write_oms():
   #
   # Resonetics excimer micromachining center output
   #
   units = 25.4*cad.inches_per_unit
   pulseperiod = float(string_pulse_period.get())
   cutvel = float(string_cut_vel.get())
   cutaccel = float(string_cut_accel.get())
   slewvel = 1
   slewaccel = 5
   settle = 100
   filename = string_cam_file.get()
   file = open(filename, 'wb')
   file.write("AA LP0,0,0,0,0\n") # set origin
   file.write("PP%d\n"%pulseperiod) # set pulse period
   for layer in range(len(cad.toolpaths)):
      for segment in range(len(cad.toolpaths[layer])):      
         x = units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][0].x+0.5)/float(cad.nx))
         y = units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][0].y)+0.5)/float(cad.ny))
	 file.write("VL%.1f,%.1f\n"%(slewvel,slewvel))
	 file.write("AC%.1f,%.1f\n"%(slewaccel,slewaccel))
         file.write("MA%f,%f\n"%(x,y))
	 file.write("VL%.1f,%.1f\n"%(cutvel,cutvel))
	 file.write("AC%.1f,%.1f\n"%(cutaccel,cutaccel))
	 file.write("WT%d\n"%settle) # wait to settle
         for vertex in range(1,len(cad.toolpaths[layer][segment])):
            x = units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][vertex].x+0.5)/float(cad.nx))
            y = units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][vertex].y)+0.5)/float(cad.ny))
            file.write("CutAbs %f,%f\n"%(x,y))
   file.write("END\n")
   file.close()
   draw_toolpath()
   string_msg.set("wrote %s"%filename)
   root.update()

def write_dxf():
   #
   # DXF output
   #
   units = cad.inches_per_unit
   filename = string_cam_file.get()
   file = open(filename, 'wb')
   file.write("999\nDXF written by cad.py\n")
   file.write("0\nSECTION\n")
   file.write("2\nHEADER\n")
   file.write("9\n$EXTMIN\n")
   file.write("10\n%f\n"%cad.xmin)
   file.write("20\n%f\n"%cad.ymin)
   file.write("9\n$EXTMAX\n")
   file.write("10\n%f\n"%cad.xmax)
   file.write("20\n%f\n"%cad.ymax)
   file.write("0\nENDSEC\n")
   file.write("0\nSECTION\n")
   file.write("2\nTABLES\n")
   file.write("0\nTABLE\n")
   file.write("2\nLTYPE\n70\n1\n")
   file.write("0\nLTYPE\n")
   file.write("2\nCONTINUOUS\n")
   file.write("70\n64\n3\n")
   file.write("Solid line\n")
   file.write("72\n65\n73\n0\n40\n0.000000\n")
   file.write("0\nENDTAB\n")
   file.write("0\nTABLE\n2\nLAYER\n70\n1\n")
   file.write("0\nLAYER\n2\ndefault\n70\n64\n62\n7\n6\n")
   file.write("CONTINUOUS\n0\nENDTAB\n")
   file.write("0\nENDSEC\n")
   file.write("0\nSECTION\n")
   file.write("2\nBLOCKS\n")
   file.write("0\nENDSEC\n")
   file.write("0\nSECTION\n")
   file.write("2\nENTITIES\n")
   for layer in range(len(cad.toolpaths)):
      for segment in range(len(cad.toolpaths[layer])):
         for vertex in range(1,len(cad.toolpaths[layer][segment])):
            x0 = units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][vertex-1].x+0.5)/float(cad.nx))
            y0 = units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][vertex-1].y)+0.5)/float(cad.ny))
            x1 = units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][vertex].x+0.5)/float(cad.nx))
            y1 = units*(cad.ymin + (cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][vertex].y)+0.5)/float(cad.ny))
	    file.write("0\nLINE\n")
	    file.write("10\n%f\n"%x0)
	    file.write("20\n%f\n"%y0)
	    file.write("11\n%f\n"%x1)
	    file.write("21\n%f\n"%y1)
   file.write("0\nENDSEC\n")
   file.write("0\nEOF\n")
   file.close()
   draw_toolpath()
   string_msg.set("wrote %s"%filename)
   root.update()

def write_uni():
   #
   # Universal lasercutter output
   #
   units = 1000*cad.inches_per_unit
   filename = string_cam_file.get()
   file = open(filename, 'wb')
   file.write("Z") # initialize
   file.write("t%s~;"%filename) # title
   file.write("IN;DF;PS0;DT~") # initialize
   ppibyte = int(float(string_laser_rate.get())/10)
   file.write("s%c"%ppibyte) # PPI
   speed_hibyte = int(648*float(string_laser_speed.get()))/256
   speed_lobyte = int(648*float(string_laser_speed.get()))%256
   file.write("v%c%c"%(speed_hibyte,speed_lobyte)) # speed
   power_hibyte = (320*int(string_laser_power.get()))/256
   power_lobyte = (320*int(string_laser_power.get()))%256
   file.write("p%c%c"%(power_hibyte,power_lobyte)) # power
   file.write("a%c"%2) # air assist on high
   for layer in range(len(cad.toolpaths)):
      for segment in range(len(cad.toolpaths[layer])):
         x = int(units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][0].x+0.5)/float(cad.nx)))
         y = int(units*(19 + cad.ymin + ((cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][0].y)+0.5)/float(cad.ny))))
         file.write("PU;PA"+str(x)+","+str(y)+";PD;")
         for vertex in range(1,len(cad.toolpaths[layer][segment])):
            x = int(units*(cad.xmin + (cad.xmax-cad.xmin)*(cad.toolpaths[layer][segment][vertex].x+0.5)/float(cad.nx)))
            y = int(units*(19 + cad.ymin + ((cad.ymax-cad.ymin)*((cad.ny-cad.toolpaths[layer][segment][vertex].y)+0.5)/float(cad.ny))))
            file.write("PA"+str(x)+","+str(y)+";")
   file.write("e") # end of file
   file.close()
   draw_toolpath()
   string_msg.set("wrote %s"%filename)
   root.update()

def write_gif():
   #
   # GIF image output
   #
   string_num_contours.set('0')
   evaluate()
   if (find(widget_cad_text.get("1.0",END),"render(") == -1):
      render()
   filename = string_cam_file.get()
   intensity = (1 << 16)*cad.image_b + (1 << 8)*cad.image_g + (1 << 0)*cad.image_r
   im = Image.frombuffer("RGBX",(cad.nx,cad.ny),intensity)
   im = im.transpose(Image.FLIP_TOP_BOTTOM)
   im.save(filename)

def write_stl():
   #
   # STL output
   #
   print "not implemented"


def msg_xy(event):
   x = (cad.xmin+cad.xmax)/2. + (cad.xmax-cad.xmin)*(1+event.x-cad.nplot/2.)/float(cad.nxplot())
   y = (cad.ymin+cad.ymax)/2. + (cad.ymin-cad.ymax)*(1+event.y-cad.nplot/2.)/float(cad.nyplot())
   string_msg.set("x = %.2f  y = %.2f"%(x,y))

def msg_yz(event):
   if (cad.nz > 1):
      y = (cad.ymin+cad.ymax)/2. + (cad.ymin-cad.ymax)*(1+event.y-cad.nplot/2.)/float(cad.nyplot())
      z = (cad.zmin+cad.zmax)/2. + (cad.zmin-cad.zmax)*(1+event.x-cad.nplot/2.)/float(cad.nzplot())
      string_msg.set("y = %.2f  z = %.2f"%(y,z))
   else:
      string_msg.set("")

def msg_xz(event):
   if (cad.nz > 1):
      x = (cad.xmin+cad.xmax)/2. + (cad.xmax-cad.xmin)*(1+event.x-cad.nplot/2.)/float(cad.nxplot())
      z = (cad.zmin+cad.zmax)/2. + (cad.zmin-cad.zmax)*(1+event.y-cad.nplot/2.)/float(cad.nzplot())
      string_msg.set("x = %.2f  z = %.2f"%(x,z))
   else:
      string_msg.set("")

def msg_nomsg(event):
   string_msg.set("")

def image_min_x(event):
   cad.xmin = float(string_image_xmin.get())
   xwidth = float(string_image_xwidth.get())
   cad.xmax = cad.xmin + xwidth
   root.update()

def image_min_y(event):
   cad.ymin = float(string_image_ymin.get())
   yheight = float(string_image_yheight.get())
   cad.ymax = cad.ymin + yheight
   root.update()

def image_scale_x(event):
   yheight = float(string_image_yheight.get())
   xwidth = yheight*cad.nx/float(cad.ny)
   cad.xmax = cad.xmin + xwidth
   string_image_xwidth.set(str(xwidth))
   root.update()

def image_scale_y(event):
   xwidth = float(string_image_xwidth.get())
   yheight = xwidth*cad.ny/float(cad.nx)
   cad.ymax = cad.ymin + yheight
   string_image_yheight.set(str(yheight))
   root.update()

def send_to(event):
   cad_path = os.path.dirname(sys.argv[0])
   if (sys.argv[0] == "cad.py"):
      cfg_path = "cad.cfg"
   else:
      cfg_path = os.path.dirname(sys.argv[0])+"/cad.cfg"
   try:
      config_file = open(cfg_path, 'r')
   except:
      string_msg.set(cfg_path+" not found")
      root.update()
      return()
   save_cam(0)
   cam_file_name = string_cam_file.get()
   dot = find(cam_file_name,".")
   while 1:
      new_dot = find(cam_file_name,".",dot+1)
      if (new_dot == -1):
         break
      else:
	 dot = new_dot
   suffix = cam_file_name[dot+1:]
   while 1:
      line = config_file.readline()
      if (find(line,suffix) == 0):
         string_msg.set("sending "+cam_file_name+" ...")
         root.update()
	 quote1 = find(line,'"')
	 quote2 = find(line,'"',quote1+1)
	 cmd = line[(quote1+1):quote2]
	 cmd = replace(cmd,'file',cam_file_name)
	 os.system(cmd)
         string_msg.set(cam_file_name+" sent")
         root.update()
         config_file.close()
         root.update()
	 return()
      elif (line == ""):
         string_msg.set(suffix+" driver not defined in "+cfg_path)
         config_file.close()
         root.update()
	 return()
#
# set up GUI
#
root = Tk()
root.title('cad.py')
#
# message frame
#
msg_frame = Frame(root)
string_msg = StringVar()
widget_msg = Label(msg_frame, textvariable = string_msg)
widget_msg.pack(side='left')
Label(msg_frame, text=" ").pack(side='left')
widget_stop = Button(msg_frame, text='stop', borderwidth=2)
widget_stop.bind('<Button-1>',render_stop)
msg_frame.grid(row=1)
#
# view frame
#
view_frame2 = Frame(root)
view_frame3 = Frame(root)
cad.view('xyzr')
#
# I/O frame
#
io_frame = Frame(root)
io_frame.grid(row=2,column=1,sticky=N)
#cad_frame.bind('<Motion>',msg_nomsg)
   #
   # input frame
   #
input_frame = Frame(io_frame)
input_frame.pack()
      #
      # .cad editor
      #
editor_frame = Frame(input_frame)
widget_text_yscrollbar = Scrollbar(editor_frame)
widget_cad_text = Text(editor_frame, bg='white', bd=5, width=45, height=40, yscrollcommand=widget_text_yscrollbar.set)
widget_cad_text.grid(row=1,column=1)
widget_text_yscrollbar.grid(row=1,column=2,sticky=N+S)
widget_text_yscrollbar.config(command=widget_cad_text.yview)
widget_cad_text.bind('<Motion>',msg_nomsg)
editor_frame.pack()
      #
      # input file
      #
cad_input_frame = Frame(input_frame)
widget_input_file = Button(cad_input_frame, text="input file:",command=input_open)
widget_input_file.pack(side='left')
string_input_file = StringVar()
string_input_file.set('out.cad')
Label(cad_input_frame, text=" ").pack(side='left')
widget_cad = Entry(cad_input_frame, width=12, bg='white', textvariable=string_input_file)
widget_cad.pack(side='left')
Label(cad_input_frame, text=" ").pack(side='left')
widget_cad_save = Button(cad_input_frame, text="save .cad")
widget_cad_save.bind('<Button-1>',cad_save)
widget_cad_save.pack(side='left')
cad_input_frame.pack()
      #
      # image x
      #
image_x_frame = Frame(input_frame)
Label(image_x_frame, text="x min: ").pack(side='left')
string_image_xmin = StringVar()
widget_image_xmin = Entry(image_x_frame, width=6, bg='white', textvariable=string_image_xmin)
widget_image_xmin.bind('<Return>',image_min_x)
widget_image_xmin.pack(side='left')
Label(image_x_frame, text="   x width: ").pack(side='left')
string_image_xwidth = StringVar()
widget_image_xwidth = Entry(image_x_frame, width=6, bg='white', textvariable=string_image_xwidth)
widget_image_xwidth.bind('<Return>',image_scale_y)
widget_image_xwidth.pack(side='left')
string_image_nx = StringVar()
Label(image_x_frame, textvariable = string_image_nx).pack(side='left')
      #
      # image y
      #
image_y_frame = Frame(input_frame)
Label(image_y_frame, text="y min: ").pack(side='left')
string_image_ymin = StringVar()
widget_image_ymin = Entry(image_y_frame, width=6, bg='white', textvariable=string_image_ymin)
widget_image_ymin.bind('<Return>',image_min_y)
widget_image_ymin.pack(side='left')
Label(image_y_frame, text="  y height: ").pack(side='left')
string_image_yheight = StringVar()
widget_image_yheight = Entry(image_y_frame, width=6, bg='white', textvariable=string_image_yheight)
widget_image_yheight.bind('<Return>',image_scale_x)
widget_image_yheight.pack(side='left')
string_image_ny = StringVar()
Label(image_y_frame, textvariable = string_image_ny).pack(side='left')
      #
      # image z
      #
image_z_frame = Frame(input_frame)
Label(image_z_frame, text="zmin: ").pack(side='left')
string_image_zmin = StringVar()
widget_image_zmin = Entry(image_z_frame, width=6, bg='white', textvariable=string_image_zmin)
widget_image_zmin.pack(side='left')
Label(image_z_frame, text="   zmax: ").pack(side='left')
string_image_zmax = StringVar()
widget_image_zmax = Entry(image_z_frame, width=6, bg='white', textvariable=string_image_zmax)
widget_image_zmax.pack(side='left')
Label(image_z_frame, text="   nz: ").pack(side='left')
string_image_nz = StringVar()
widget_image_nz = Entry(image_z_frame, width=6, bg='white', textvariable=string_image_nz)
widget_image_nz.pack(side='left')
      #
      # image intensity
      #
image_intensity_frame = Frame(input_frame)
Label(image_intensity_frame, text="intensity min: ").pack(side='left')
string_image_min = StringVar()
widget_image_min = Entry(image_intensity_frame, width=6, bg='white', textvariable=string_image_min)
widget_image_min.pack(side='left')
Label(image_intensity_frame, text="   intensity max: ").pack(side='left')
string_image_max = StringVar()
widget_image_max = Entry(image_intensity_frame, width=6, bg='white', textvariable=string_image_max)
widget_image_max.pack(side='left')
   #
   # image units
   #   
image_units_frame = Frame(input_frame)
Label(image_units_frame, text="inches per unit: ").pack(side='left')
string_image_units = StringVar()
widget_image_units = Entry(image_units_frame, width=6, bg='white', textvariable=string_image_units)
widget_image_units.pack(side='left')
      #
      # image invert
      #
image_invert_frame = Frame(input_frame)
Label(image_invert_frame, text=" ").pack(side='left')
widget_image_invert = Button(image_invert_frame, text="invert image")
widget_image_invert.pack(side='left')
widget_image_invert.bind('<Button-1>',invert_image)
   #
   # output frame
   #
output_frame = Frame(io_frame)
output_frame.pack()
      #
      # controls
      #
control_frame = Frame(output_frame)
widget_render = Button(control_frame, text="render")
widget_render.bind('<Button-1>',render_button)
widget_render.pack(side='left')
Label(control_frame, text=" ").pack(side='left')
canvas_logo = Canvas(control_frame, width=26, height=26, background="white")
canvas_logo.create_oval(2,2,8,8,fill="red",outline="")
canvas_logo.create_rectangle(11,2,17,8,fill="blue",outline="")
canvas_logo.create_rectangle(20,2,26,8,fill="blue",outline="")
canvas_logo.create_rectangle(2,11,8,17,fill="blue",outline="")
canvas_logo.create_oval(10,10,16,16,fill="red",outline="")
canvas_logo.create_rectangle(20,11,26,17,fill="blue",outline="")
canvas_logo.create_rectangle(2,20,8,26,fill="blue",outline="")
canvas_logo.create_rectangle(11,20,17,26,fill="blue",outline="")
canvas_logo.create_rectangle(20,20,26,26,fill="blue",outline="")
canvas_logo.pack(side='left')
control_text = " cad.py (%s) "%DATE
Label(control_frame, text=control_text).pack(side='left')
widget_cam = Button(control_frame, text="cam")
widget_cam.bind('<Button-1>',cam)
widget_cam.pack(side='left')
Label(control_frame, text=" ").pack(side='left')
widget_quit = Button(control_frame, text="quit", command='exit')
widget_quit.pack(side='left')
control_frame.pack()
      #
      # function string
      #
function_string_frame = Frame(output_frame)
Label(function_string_frame, text="function:").grid(row=1,column=1)
widget_function_yscrollbar = Scrollbar(function_string_frame)
widget_function_text = Text(function_string_frame, bg='white', bd=5, width=45, height=12, yscrollcommand=widget_function_yscrollbar.set, state=DISABLED)
widget_function_text.grid(row=2,column=1)
widget_function_yscrollbar.grid(row=2,column=2,sticky=N+S)
widget_function_yscrollbar.config(command=widget_function_text.yview)
function_string_frame.pack()
      #
      # CAM file
      #
cam_file_frame = Frame(output_frame)
widget_cam_menu_button = Menubutton(cam_file_frame,text="output format", relief=RAISED)
widget_cam_menu_button.pack(side='left')
widget_cam_menu = Menu(widget_cam_menu_button)
widget_cam_menu.add_command(label='.epi (Epilog)',command=select_epi)
widget_cam_menu.add_command(label='.camm (CAMM)',command=select_camm)
widget_cam_menu.add_command(label='.rml (Modela)',command=select_rml)
widget_cam_menu.add_command(label='.ps (Postscript)',command=select_ps)
widget_cam_menu.add_command(label='.ord (OMAX)',command=select_ord)
widget_cam_menu.add_command(label='.oms (Resonetics)',command=select_oms)
widget_cam_menu.add_command(label='.dxf (DXF)',command=select_dxf)
#widget_cam_menu.add_command(label='.gif (GIF)',command=select_gif)
widget_cam_menu.add_command(label='.stl (STL)',command=select_stl)
#widget_cam_menu.add_command(label='.uni (Universal)',command=select_uni)
widget_cam_menu.add_command(label='.uni (Universal)',state=DISABLED)
widget_cam_menu.add_command(label='.g (G codes)',state=DISABLED)
widget_cam_menu_button['menu'] = widget_cam_menu
Label(cam_file_frame, text=" output file: ").pack(side='left')
string_cam_file = StringVar()
widget_cam_file = Entry(cam_file_frame, width=12, bg='white', textvariable=string_cam_file)
widget_cam_file.pack(side='left')
Label(cam_file_frame, text=" ").pack(side='left')
widget_cam_save = Button(cam_file_frame, text="save")
widget_cam_save.bind('<Button-1>',save_cam)
widget_cam_save.pack(side='left')
      #
      # vectorization
      #
cam_vector_frame = Frame(output_frame)
Label(cam_vector_frame, text="maximum vector fit error (lattice units): ").pack(side='left')
string_vector_error = StringVar()
string_vector_error.set('.75')
widget_vector_error = Entry(cam_vector_frame, width=6, bg='white', textvariable=string_vector_error)
widget_vector_error.pack(side='left')
      #
      # tool
      #
cam_dia_frame = Frame(output_frame)
Label(cam_dia_frame, text="tool diameter: ").pack(side='left')
string_tool_dia = StringVar()
string_tool_dia.set('0')
widget_tool_dia = Entry(cam_dia_frame, width=6, bg='white', textvariable=string_tool_dia)
widget_tool_dia.pack(side='left')
Label(cam_dia_frame, text=" tool overlap: ").pack(side='left')
string_tool_overlap = StringVar()
string_tool_overlap.set('0.5')
widget_tool_overlap = Entry(cam_dia_frame, width=6, bg='white', textvariable=string_tool_overlap)
widget_tool_overlap.pack(side='left')
      #
      # contour
      #
cam_contour_frame = Frame(output_frame)
Label(cam_contour_frame, text=" # contours (-1 for max): ").pack(side='left')
string_num_contours = StringVar()
string_num_contours.set('0')
widget_num_contours = Entry(cam_contour_frame, width=6, bg='white', textvariable=string_num_contours)
widget_num_contours.pack(side='left')
Label(cam_contour_frame, text=" ").pack(side='left')
widget_cam_contour = Button(cam_contour_frame, text="contour")
widget_cam_contour.pack(side='left')
widget_cam_contour.bind('<Button-1>',contour)
      #
      # laser power
      #
laser_frame1 = Frame(output_frame)
Label(laser_frame1, text=" power:").pack(side='left')
string_laser_power = StringVar()
Entry(laser_frame1, width=6, bg='white', textvariable=string_laser_power).pack(side='left')
Label(laser_frame1, text=" speed:").pack(side='left')
string_laser_speed = StringVar()
Entry(laser_frame1, width=6, bg='white', textvariable=string_laser_speed).pack(side='left')
Label(laser_frame1, text=" rate: ").pack(side='left')
string_laser_rate = StringVar()
Entry(laser_frame1, width=6, bg='white', textvariable=string_laser_rate).pack(side='left')
      #
      # autofocus
      #
laser_frame2 = Frame(output_frame)
integer_laser_autofocus = IntVar()
widget_autofocus = Checkbutton(laser_frame2, text="Auto Focus", variable=integer_laser_autofocus).pack(side='left')
      #
      # cutting
      #
cut_frame = Frame(output_frame)
Label(cut_frame, text="force: ").pack(side='left')
string_cut_force = StringVar()
Entry(cut_frame, width=6, bg='white', textvariable=string_cut_force).pack(side='left')
Label(cut_frame, text=" velocity:").pack(side='left')
string_cut_velocity = StringVar()
Entry(cut_frame, width=6, bg='white', textvariable=string_cut_velocity).pack(side='left')
      #
      # speed
      #
speed_frame = Frame(output_frame)
Label(speed_frame, text="xy speed:").pack(side='left')
string_xy_speed = StringVar()
Entry(speed_frame, width=6, bg='white', textvariable=string_xy_speed).pack(side='left')
Label(speed_frame, text=" z speed:").pack(side='left')
string_z_speed = StringVar()
Entry(speed_frame, width=6, bg='white', textvariable=string_z_speed).pack(side='left')
      #
      # waterjet
      #
waterjet_frame = Frame(output_frame)
Label(waterjet_frame,text="lead-in/out: ").pack(side='left')
string_lead_in = StringVar()
widget_lead_in = Entry(waterjet_frame, width=4, bg='white', textvariable=string_lead_in)
widget_lead_in.pack(side='left')
Label(waterjet_frame,text="quality: ").pack(side='left')
string_quality = StringVar()
widget_quality = Entry(waterjet_frame, width=4, bg='white', textvariable=string_quality)
widget_quality.pack(side='left')
      #
      # excimer
      #
excimer_frame = Frame(output_frame)
Label(excimer_frame,text="period (usec): ").pack(side='left')
string_pulse_period = StringVar()
widget_pulse_period = Entry(excimer_frame, width=5, bg='white', textvariable=string_pulse_period)
widget_pulse_period.pack(side='left')
Label(excimer_frame,text="velocity: ").pack(side='left')
string_cut_vel = StringVar()
widget_cut_vel = Entry(excimer_frame, width=4, bg='white', textvariable=string_cut_vel)
widget_cut_vel.pack(side='left')
Label(excimer_frame,text="acceleration: ").pack(side='left')
string_cut_accel = StringVar()
widget_cut_accel = Entry(excimer_frame, width=4, bg='white', textvariable=string_cut_accel)
widget_cut_accel.pack(side='left')
      #
      # STL
      #
STL_frame = Frame(output_frame)
Label(STL_frame,text="facet voxel size (lattice units): ").pack(side='left')
string_STL_voxel = StringVar()
widget_STL_voxel = Entry(STL_frame, width=5, bg='white', textvariable=string_STL_voxel)
widget_STL_voxel.pack(side='left')
Label(STL_frame,text=" ").pack(side='left')
widget_STL_triangulate = Button(STL_frame, text="triangulate")
widget_STL_triangulate.pack(side='left')
widget_STL_triangulate.bind('<Button-1>',triangulate)
      #
      # filling
      #
fill_frame = Frame(output_frame)
integer_fill = IntVar()
widget_fill = Checkbutton(fill_frame, text="fill polygons", variable=integer_fill).pack(side='left')
      #
      # send to
      #
send_to_frame = Frame(output_frame)
widget_send_to = Button(send_to_frame, text="send to machine")
widget_send_to.bind('<Button-1>',send_to)
widget_send_to.pack(side='left')

#
# define .cad template
#
cad_template = """#
# .cad template
#

#
# define shapes and transformation
#
# circle(x0, y0, r)
# cylinder(x0, y0, z0, z1, r)
# cone(x0, y0, z0, z1, r0)
# sphere(x0, y0, z0, r)
# torus(x0, y0, z0, r0, r1)
# rectangle(x0, x1, y0, y1)
# cube(x0, x1, y0, y1, z0, z1)
# triangle(x0, y0, x1, y1, x2, y2) (points in clockwise order)
# pyramid(x0, x1, y0, y1, z0, z1)
# function(Z_of_XY)
# functions(upper_Z_of_XY,lower_Z_of_XY)
# add(part1, part2)
# subtract(part1, part2)
# intersect(part1, part2)
# move(part,dx,dy)
# translate(part,dx,dy,dz)
# rotate(part, angle)
# rotate_x(part, angle)
# rotate_y(part, angle)
# rotate_z(part, angle)
# rotate_90(part)
# rotate_180(part)
# rotate_270(part)
# reflect_x(part)
# reflect_y(part)
# reflect_z(part)
# reflect_xy(part)
# reflect_xz(part)
# reflect_yz(part)
# scale_x(part, x0, sx)
# scale_y(part, y0, sy)
# scale_z(part, z0, sz)
# scale_xy(part, x0, y0, sxy)
# scale_xyz(part, x0, y0, z0, sxyz)
# coscale_x_y(part, x0, y0, y1, angle0, angle1, amplitude, offset)
# coscale_x_z(part, x0, z0, z1, angle0, angle1, amplitude, offset)
# coscale_xy_z(part, x0, y0, z0, z1, angle0, angle1, amplitude, offset)
# taper_x_y(part, x0, y0, y1, s0, s1)
# taper_x_z(part, x0, z0, z1, s0, s1)
# taper_xy_z(part, x0, y0, z0, z1, s0, s1)
# shear_x_y(part, y0, y1, dx0, dx1)
# shear_x_z(part, z0, z1, dx0, dx1)
# (more to come)

def circle(x0, y0, r):
   part = "(((X-x0)**2 + (Y-y0)**2) <= r**2)"
   part = replace(part,'x0',str(x0))
   part = replace(part,'y0',str(y0))
   part = replace(part,'r',str(r))
   return part

def cylinder(x0, y0, z0, z1, r):
   part = "(((X-x0)**2 + (Y-y0)**2 <= r**2) & (Z >= z0) & (Z <= z1))"
   part = replace(part,'x0',str(x0))
   part = replace(part,'y0',str(y0))
   part = replace(part,'z0',str(z0))
   part = replace(part,'z1',str(z1))
   part = replace(part,'r',str(r))
   return part

def cone(x0, y0, z0, z1, r0):
   part = cylinder(x0, y0, z0, z1, r0)
   part = taper_xy_z(part, x0, y0, z0, z1, 1.0, 0.0)
   return part

def sphere(x0, y0, z0, r):
   part = "(((X-x0)**2 + (Y-y0)**2 + (Z-z0)**2) <= r**2)"
   part = replace(part,'x0',str(x0))
   part = replace(part,'y0',str(y0))
   part = replace(part,'z0',str(z0))
   part = replace(part,'r',str(r))
   return part

def torus(x0, y0, z0, r0, r1):
   part = "(((r0 - sqrt((X-x0)**2 + (Y-y0)**2))**2 + (Z-z0)**2) <= r1**2)"
   part = replace(part,'x0',str(x0))
   part = replace(part,'y0',str(y0))
   part = replace(part,'z0',str(z0))
   part = replace(part,'r0',str(r0))
   part = replace(part,'r1',str(r1))
   return part

def rectangle(x0, x1, y0, y1):
   part = "((X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1))"
   part = replace(part,'x0',str(x0))
   part = replace(part,'x1',str(x1))
   part = replace(part,'y0',str(y0))
   part = replace(part,'y1',str(y1))
   return part

def cube(x0, x1, y0, y1, z0, z1):
   part = "((X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1) & (Z >= z0) & (Z <= z1))"
   part = replace(part,'x0',str(x0))
   part = replace(part,'x1',str(x1))
   part = replace(part,'y0',str(y0))
   part = replace(part,'y1',str(y1))
   part = replace(part,'z0',str(z0))
   part = replace(part,'z1',str(z1))
   return part

def triangle(x0, y0, x1, y1, x2, y2): # points in clockwise order
   part = "((((y1-y0)*(X-x0)-(x1-x0)*(Y-y0)) >= 0) & (((y2-y1)*(X-x1)-(x2-x1)*(Y-y1)) >= 0) & (((y0-y2)*(X-x2)-(x0-x2)*(Y-y2)) >= 0))"
   part = replace(part,'x0',str(x0))
   part = replace(part,'y0',str(y0))
   part = replace(part,'x1',str(x1))
   part = replace(part,'y1',str(y1))
   part = replace(part,'x2',str(x2))
   part = replace(part,'y2',str(y2))
   return part

def pyramid(x0, x1, y0, y1, z0, z1):
   part = cube(x0, x1, y0, y1, z0, z1)
   part = taper_xy_z(part, (x0+x1)/2., (y0+y1)/2., z0, z1, 1.0, 0.0)
   return part

def function(Z_of_XY):
   part = '(Z <= '+Z_of_XY+')'
   return part

def functions(upper_Z_of_XY,lower_Z_of_XY):
   part = '(Z <= '+upper_Z_of_XY+') & (Z >= '+lower_Z_of_XY+')'
   return part

def add(part1, part2):
   part = "part1 | part2"
   part = replace(part,'part1',part1)
   part = replace(part,'part2',part2)
   return part

def subtract(part1, part2):
   part = "(part1) & ~(part2)"
   part = replace(part,'part1',part1)
   part = replace(part,'part2',part2)
   return part

def intersect(part1, part2):
   part = "(part1) & (part2)"
   part = replace(part,'part1',part1)
   part = replace(part,'part2',part2)
   return part

def move(part,dx,dy):
   part = replace(part,'X','(X-'+str(dx)+')')
   part = replace(part,'Y','(Y-'+str(dy)+')')
   return part   

def translate(part,dx,dy,dz):
   part = replace(part,'X','(X-'+str(dx)+')')
   part = replace(part,'Y','(Y-'+str(dy)+')')
   part = replace(part,'Z','(Z-'+str(dz)+')')
   return part   

def rotate(part, angle):
   angle = angle*pi/180
   part = replace(part,'X','(cos(angle)*X+sin(angle)*y)')
   part = replace(part,'Y','(-sin(angle)*X+cos(angle)*y)')
   part = replace(part,'y','Y')
   part = replace(part,'angle',str(angle))
   return part

def rotate_x(part, angle):
   angle = angle*pi/180
   part = replace(part,'Y','(cos(angle)*Y+sin(angle)*z)')
   part = replace(part,'Z','(-sin(angle)*Y+cos(angle)*z)')
   part = replace(part,'z','Z')
   part = replace(part,'angle',str(angle))
   return part

def rotate_y(part, angle):
   angle = angle*pi/180
   part = replace(part,'X','(cos(angle)*X+sin(angle)*z)')
   part = replace(part,'Z','(-sin(angle)*X+cos(angle)*z)')
   part = replace(part,'z','Z')
   part = replace(part,'angle',str(angle))
   return part

def rotate_z(part, angle):
   angle = angle*pi/180
   part = replace(part,'X','(cos(angle)*X+sin(angle)*y)')
   part = replace(part,'Y','(-sin(angle)*X+cos(angle)*y)')
   part = replace(part,'y','Y')
   part = replace(part,'angle',str(angle))
   return part

def rotate_90(part):
   part = reflect_xy(part)
   part = reflect_y(part)
   return part

def rotate_180(part):
   part = reflect_xy(part)
   part = reflect_y(part)
   part = reflect_xy(part)
   part = reflect_y(part)
   return part

def rotate_270(part):
   part = reflect_xy(part)
   part = reflect_y(part)
   part = reflect_xy(part)
   part = reflect_y(part)
   part = reflect_xy(part)
   part = reflect_y(part)
   return part

def reflect_x(part):
   part = replace(part,'X','-X')
   return part

def reflect_y(part):
   part = replace(part,'Y','-Y')
   return part

def reflect_z(part):
   part = replace(part,'Z','-Z')
   return part

def reflect_xy(part):
   part = replace(part,'X','temp')
   part = replace(part,'Y','X')
   part = replace(part,'temp','Y')
   return part

def reflect_xz(part):
   part = replace(part,'X','temp')
   part = replace(part,'Z','X')
   part = replace(part,'temp','Z')
   return part

def reflect_yz(part):
   part = replace(part,'Y','temp')
   part = replace(part,'Z','Y')
   part = replace(part,'temp','Z')
   return part

def scale_x(part, x0, sx):
   part = replace(part,'X','(x0 + (X-x0)/sx)')
   part = replace(part,'x0',str(x0))
   part = replace(part,'sx',str(sx))
   return part

def scale_y(part, y0, sy):
   part = replace(part,'Y','(y0 + (Y-y0)/sy)')
   part = replace(part,'y0',str(y0))
   part = replace(part,'sy',str(sy))
   return part

def scale_z(part, z0, sz):
   part = replace(part,'Z','(z0 + (Z-z0)/sz)')
   part = replace(part,'z0',str(z0))
   part = replace(part,'sz',str(sz))
   return part

def scale_xy(part, x0, y0, sxy):
   part = replace(part,'X','(x0 + (X-x0)/sxy)')
   part = replace(part,'Y','(y0 + (Y-y0)/sxy)')
   part = replace(part,'x0',str(x0))
   part = replace(part,'y0',str(y0))
   part = replace(part,'sxy',str(sxy))
   return part

def scale_xyz(part, x0, y0, z0, sxyz):
   part = replace(part,'X','(x0 + (X-x0)/sxyz)')
   part = replace(part,'Y','(y0 + (Y-y0)/sxyz)')
   part = replace(part,'Z','(z0 + (Z-z0)/sxyz)')
   part = replace(part,'x0',str(x0))
   part = replace(part,'y0',str(y0))
   part = replace(part,'z0',str(z0))
   part = replace(part,'sxyz',str(sxyz))
   return part

def coscale_x_y(part, x0, y0, y1, angle0, angle1, amplitude, offset):
   phase0 = pi*angle0/180.
   phase1 = pi*angle1/180.
   part = replace(part,'X','(x0 + (X-x0)/(offset + amplitude*cos(phase0 + (phase1-phase0)*(Y-y0)/(y1-y0))))')
   part = replace(part,'x0',str(x0))
   part = replace(part,'y0',str(y0))
   part = replace(part,'y1',str(y1))
   part = replace(part,'phase0',str(phase0))
   part = replace(part,'phase1',str(phase1))
   part = replace(part,'amplitude',str(amplitude))
   part = replace(part,'offset',str(offset))
   return part

def coscale_x_z(part, x0, z0, z1, angle0, angle1, amplitude, offset):
   phase0 = pi*angle0/180.
   phase1 = pi*angle1/180.
   part = replace(part,'X','(x0 + (X-x0)/(offset + amplitude*cos(phase0 + (phase1-phase0)*(Z-z0)/(z1-z0))))')
   part = replace(part,'x0',str(x0))
   part = replace(part,'z0',str(z0))
   part = replace(part,'z1',str(z1))
   part = replace(part,'phase0',str(phase0))
   part = replace(part,'phase1',str(phase1))
   part = replace(part,'amplitude',str(amplitude))
   part = replace(part,'offset',str(offset))
   return part

def coscale_xy_z(part, x0, y0, z0, z1, angle0, angle1, amplitude, offset):
   phase0 = pi*angle0/180.
   phase1 = pi*angle1/180.
   part = replace(part,'X','(x0 + (X-x0)/(offset + amplitude*cos(phase0 + (phase1-phase0)*(Z-z0)/(z1-z0))))')
   part = replace(part,'Y','(y0 + (Y-y0)/(offset + amplitude*cos(phase0 + (phase1-phase0)*(Z-z0)/(z1-z0))))')
   part = replace(part,'x0',str(x0))
   part = replace(part,'y0',str(y0))
   part = replace(part,'z0',str(z0))
   part = replace(part,'z1',str(z1))
   part = replace(part,'phase0',str(phase0))
   part = replace(part,'phase1',str(phase1))
   part = replace(part,'amplitude',str(amplitude))
   part = replace(part,'offset',str(offset))
   return part

def taper_x_y(part, x0, y0, y1, s0, s1):
   part = replace(part,'X','(x0 + (X-x0)*(y1-y0)/(s1*(Y-y0) + s0*(y1-Y)))')
   part = replace(part,'x0',str(x0))
   part = replace(part,'y0',str(y0))
   part = replace(part,'y1',str(y1))
   part = replace(part,'s0',str(s0))
   part = replace(part,'s1',str(s1))
   return part

def taper_x_z(part, x0, z0, z1, s0, s1):
   part = replace(part,'X','(x0 + (X-x0)*(z1-z0)/(s1*(Z-z0) + s0*(z1-Z)))')
   part = replace(part,'x0',str(x0))
   part = replace(part,'z0',str(z0))
   part = replace(part,'z1',str(z1))
   part = replace(part,'s0',str(s0))
   part = replace(part,'s1',str(s1))
   return part

def taper_xy_z(part, x0, y0, z0, z1, s0, s1):
   part = replace(part,'X','(x0 + (X-x0)*(z1-z0)/(s1*(Z-z0) + s0*(z1-Z)))')
   part = replace(part,'Y','(y0 + (Y-y0)*(z1-z0)/(s1*(Z-z0) + s0*(z1-Z)))')
   part = replace(part,'x0',str(x0))
   part = replace(part,'y0',str(y0))
   part = replace(part,'z0',str(z0))
   part = replace(part,'z1',str(z1))
   part = replace(part,'s0',str(s0))
   part = replace(part,'s1',str(s1))
   return part

def shear_x_y(part, y0, y1, dx0, dx1):
   part = replace(part,'X','(X - dx0 - (dx1-dx0)*(Y-y0)/(y1-y0))')
   part = replace(part,'y0',str(y0))
   part = replace(part,'y1',str(y1))
   part = replace(part,'dx0',str(dx0))
   part = replace(part,'dx1',str(dx1))
   return part

def shear_x_z(part, z0, z1, dx0, dx1):
   part = replace(part,'X','(X - dx0 - (dx1-dx0)*(Z-z0)/(z1-z0))')
   part = replace(part,'z0',str(z0))
   part = replace(part,'z1',str(z1))
   part = replace(part,'dx0',str(dx0))
   part = replace(part,'dx1',str(dx1))
   return part

def coshear_x_z(part, z0, z1, angle0, angle1, amplitude, offset):
   phase0 = pi*angle0/180.
   phase1 = pi*angle1/180.
   part = replace(part,'X','(X - offset - amplitude*cos(phase0 + (phase1-phase0)*(Z-z0)/(z1-z0)))')
   part = replace(part,'z0',str(z0))
   part = replace(part,'z1',str(z1))
   part = replace(part,'phase0',str(phase0))
   part = replace(part,'phase1',str(phase1))
   part = replace(part,'amplitude',str(amplitude))
   part = replace(part,'offset',str(offset))
   return part

#
# define part
#

d = .5
teapot = cylinder(0,0,-d,d,d)
teapot = coscale_xy_z(teapot,0,0,-d,d,-90,90,.5,.75)

handle = torus(0,0,0,3.5*d/5.,d/10.)
handle = reflect_xz(handle)
handle = reflect_xy(handle)
handle = scale_x(handle,0,.75)
handle = scale_y(handle,0,3)
handle = translate(handle,-6*d/5.,0,0)
teapot = add(teapot,handle)

spout = torus(2.1*d,-.2*d,0,1.1*d,.2*d)
spout = reflect_yz(spout)
spout = intersect(spout,cube(-3*d,1.8*d,-3*d,3*d,0,3*d))
teapot = add(teapot,spout)

interior = cylinder(0,0,.1-d,.1+d,d-.1)
interior = coscale_xy_z(interior,0,0,-d,d,-90,90,.5,.75)
teapot = subtract(teapot,interior)

spout_interior = torus(2.1*d,-.2*d,0,1.1*d,.15*d)
spout_interior = reflect_yz(spout_interior)
spout_interior = intersect(spout_interior,cube(-3*d,1.8*d,-3*d,3*d,0,3*d))
teapot = subtract(teapot,spout_interior)

part = teapot

part = subtract(part,cube(0,3*d,-3*d,0,-3*d,3*d))

#
# define limits and parameters
#

width = 2.5
x0 = 0
y0 = 0
z0 = 0
cad.xmin = x0-width/2. # min x to render
cad.xmax = x0+width/2. # max x to render
cad.ymin = y0-width/2. # min y to render
cad.ymax = y0+width/2. # max y to render
cad.zmin = z0-width/4. # min z to render
cad.zmax = z0+width/4. # max x to render
cad.rx = 30 # x view rotation (degrees)
cad.rz = 20 # z view rotation (degrees)
dpi = 100 # horizontal resolution
nxy = int(dpi*(cad.xmax-cad.xmin))
cad.nx = nxy # x points to render
cad.ny = nxy # y points to render
dz = 0.025
cad.nz = int((cad.zmax-cad.zmin)/dz)
cad.inches_per_unit = 1.0 # use inch units

#
# assign part to cad.function
#

cad.function = part

"""

#
# read input file if on command line, otherwise use template
#
if len(sys.argv) == 2:
   filename = sys.argv[1]
   string_input_file.set(filename)
   if (find(filename,'.cad') != -1):
      cad_load(0)
   elif ((find(filename,'.jpg') != -1) | (find(filename,'.JPG') != -1) |
      (find(filename,'.png') != -1) | (find(filename,'.PNG') != -1)):
      widget_cad_text.delete("1.0",END)
      image_load(0)
   else:
      string_msg.set("unsupported input file format")
      root.update()
else:
   widget_cad_text.insert("1.0",cad_template)

#
# start GUI
#

root.mainloop()
