import os
import termios
import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import sys
from PyQt4 import QtGui, QtCore


fig=plt.figure()

a=[1,2,3,4]
b=[4,3,2,1]

axes=fig.add_subplot(211)
axes2=fig.add_subplot(212)

poo1 = axes.plot(a)
poo2 = axes2.plot(b)

axes.legend("asdf")
axes.grid(True,"both")
axes2.grid(True,"both")
plt.show()
