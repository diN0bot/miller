'''
script and log of some dimension of hello.scan.01
1. scanned a cut board
2. measure critical dimensions on board with calipers
3. import scanned image into cad program
4. measure dimensions in autodesk
5. create a (few) scaling dimensions.
6. characterize liberally.
cnc mill
4/25/09
'''

# multiply autdoesk measured dimension by scale to get actual. 
scale1 = 1.281/7.408
scale2 = .970/5.430
#3% error!

thinTraceVert = scale1*.0317

thickTraceVert = scale1*.0681

thinTraceHor = scale1*.0414
thickTraceHor = scale1*.0637

print 'thin vert ' + str(thinTraceVert)
print 'thick vert ' + str(thickTraceVert)
print ' '
print 'thin hor ' + str(thinTraceHor)
print 'thick hor ' + str(thickTraceHor)
