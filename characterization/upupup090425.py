'''
up up up down down down test
commanded move: 20 thou
'''

import matplotlib.pyplot as plt

# data is reported data in thousandths using Triton dial indicator
data = [0.0, 15.0, 34.0, 52.0, 38.0, 19.5, -1.0, 16.0, 34.5, 52.0, 38.0, 19.5, -1.0, 16.0, 35.0, 52.0, 38.0, 19.5, -1.0, 16.0, 35.0, 52.0, 38.0, 19.5, -1]
move = [20.0, 20.0, 20.0, -20.0, -20.0, -20.0, 20.0, 20.0, 20.0, -20.0, -20.0, -20.0, 20.0, 20.0, 20.0, -20.0, -20.0, -20.0, 20.0, 20.0, 20.0, -20.0, -20.0, -20.0]
poop1 = [0, 21]
poop2 = [13, 22]
count = []
delta = []
for i in range(1,len(data)):
    delta.append(abs(data[i]-data[i-1]))
    count.append(i-1)
plt.plot(count,delta)
plt.plot(poop1, poop2, '*')
plt.show()
    
