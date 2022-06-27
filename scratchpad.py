import random 
from matplotlib import pyplot

l1 = []
l2 = []
l3 = []

for n in range(1000):
    l1.append(random.randint(1,100))
    l2.append(random.randint(1,100))
    l3.append(random.randint(1,100))


pyplot.plot(l1)
pyplot.plot(l2)
pyplot.plot(l3)