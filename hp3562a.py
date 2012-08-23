#! /usr/bin/env python

# Reads data from the HP 3562A DSA



#=======================================IMPORTS
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
#==============================================================================




#=======================================INITIATE THE GPIB CONTROLLER
def gpib_init(addr) :
	#Set controller to command mode
	ser.write("++mode 1\r")
	time.sleep(0.1)
	ser.write("++ifc\r")
	time.sleep(0.1)
	#Turn off auto read mode after write
	ser.write("++auto 0\r")
	time.sleep(0.1)
	#Turn on EOI - necessary for this device so it knows when a command has been sent
	ser.write("++eoi 1\r")
	time.sleep(0.1)
	#Set the GPIB address. Currently at 30
	ser.write("++addr " + str(addr) + "\r")
	#Clear the device buffer
	gpib_clear_device()
#==============================================================================





#=======================================READ FROM THE DEVICE       
def gpib_read():
	#Tell the converter you want to read data
        ser.write("++read eoi\r")
        buffer = []
        readvalue = "data"
        #Read until there's nothing left to read
        while (readvalue != ""):
		readvalue = ser.readline()
		buffer.append(readvalue)
	
	#Get rid of the \r\n in the strings
	buffer = [lines.replace('\r\n', '') for lines in buffer]	
		
	if (len(buffer[:-1]) == 1):
		#If the buffer only has 1 element then just return that element instead of a list		
		return buffer[0]
	else:
		#Otherwise return all but the last (empty) element
		return buffer[:-1]
#==============================================================================




		
#=======================================WRITE TO THE DEVICE		
def gpib_write(gpibstr):
	#Doesn't really need its own function, but might become more elaborate later
        ser.write(gpibstr + "\r")
#==============================================================================






#=======================================CLEAR THE DEVICE      
def gpib_clear_device():
	#Clear the device buffer in case there are leftovers from previous operation
        ser.write("++read eoi\r")
	empty_buffer = "full"
	while (empty_buffer != ""):   
		empty_buffer = ser.readline()
#==============================================================================




#=======================================VERIFY COMMUNICATION
def verify_communication():
	gpib_write("ID?")
	device_id = gpib_read()
	if (device_id == "HP3562A"):
		print "HP3562A Functioning Properly"
	else:
		print "ID = " + device_id
		print "Bad Data Transfer - Exiting"
		sys.exit()
#==============================================================================		




#=======================================READ THE ACTIVE TRACE
def read_active_trace():
	gpib_write("DDAS")
	trace = gpib_read()
	print "Read data from Device"
	return trace
#==============================================================================		





#=======================================EXTRACT THE HEADER AND DATA FROM THE TRACE
def extract_header_data(trace, verbose):
	header = trace[0:67]
	data = trace[67:]
	if (verbose == True):
		print "Header:"
		for k, lines in enumerate(header):
			print k, lines
			
		print "Data:"
		print data
	
	return [header,data]
#==============================================================================		





#=======================================SAVE THE RAWFILE
def save_rawfile(trace, rawfilename):
	rawfile = open(rawfilename,"w")
	for datapoint in trace:
		rawfile.write(str(datapoint)+"\n")
	rawfile.close()
#==============================================================================		




#=======================================LOAD THE RAWFILE
def load_rawfile(rawfilename):
	rawfile = open(rawfilename,"r")
	trace = rawfile.readlines()
	rawfile.close()
	trace = [lines.replace('\n', '') for lines in trace]
	print "Successfully read data from: " + rawfilename
	return trace
#==============================================================================	








#=======================================CREATE THE MATPLOTLIB PLOT
class plot_window(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    #def __init__(self, parent=None, width=5, height=4, dpi=100):
    def __init__(self, main_widget, xdata, ydata, log):
    	self.xdata = xdata
	self.ydata = ydata
    	#Setup the matplotlib figure
        #fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig = Figure()
        
        #add subplot
        self.axes = self.fig.add_subplot(111)
        
        #Want the axes cleared every time plot() is called
        self.axes.hold(False)

	self.axes.plot(self.xdata,self.ydata)
	self.axes.set_xscale(log)
	self.axes.set_xlim(min(self.xdata),max(self.xdata))
	self.axes.grid(True, 'both')
        #self.fig.savefig('figuresave_test.pdf',format='pdf')

	
		
		        
        FigureCanvas.__init__(self, self.fig)
        #self.setParent(parent)
#==============================================================================		








#=======================================CREATE THE GUI
class GUI_window(QtGui.QMainWindow):
	#First input = QtGui.QMainWindow ?
        
	def __init__(self,xdata, ydata, log):
   		
   		#Create the Main Widget
   		self.main_widget = QtGui.QWidget()
		self.main_widget.resize(800, 600)
		self.main_widget.move(300, 300)
		self.main_widget.setWindowTitle('HP3562A GUI')     
		
		#Assign all the data values
		self.xdata = xdata
		self.ydata = ydata
		self.log = log	
		
		#Make the figure
		self.fig = Figure()
        
		#add subplot
		self.axes = self.fig.add_subplot(111)
		
		#Want the axes cleared every time plot() is called
		self.axes.hold(False)
	
		#Take care of all the plotting
		self.plt = self.axes.plot(self.xdata,self.ydata)
		self.axes.set_xscale(log)
		self.axes.set_xlim(min(self.xdata),max(self.xdata))
		self.axes.grid(True, 'both')
		self.canvas = FigureCanvas(self.fig)
	
		#Define the toolbar	
		self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_widget)
			
		#Want the plots to be in a nice vertical line
		vertical_widgets = QtGui.QVBoxLayout(self.main_widget)
		
		vertical_widgets.addWidget(self.canvas)
		vertical_widgets.addWidget(self.mpl_toolbar)

		#Add Buttons
		self.display_buttons()

		#Show the GUI
		self.main_widget.show()


	def display_buttons(self):
	
		#Quit Button
		qbtn_quit = QtGui.QPushButton('Quit', self.main_widget)
		#qbtn_quit.clicked.connect(QtCore.QCoreApplication.instance().quit)
		qbtn_quit.connect(qbtn_quit, QtCore.SIGNAL("clicked()"), app, QtCore.SLOT("quit()"))
		qbtn_quit.resize(qbtn_quit.sizeHint())
		qbtn_quit.move(700, 50)  
		
		
		#Save plot button
		#qbtn_save = QtGui.QPushButton('Save Plot', self.widget)
		#qbtn_save.clicked.connect()
		#qbtn_save.resize(qbtn_save.sizeHint())
		#qbtn_save.move(700, 100)  		
#==============================================================================		
        
        
        
        

#=======================================MAIN PROGRAM		
if __name__ == "__main__":

	if len(sys.argv) == 1:
		#Baudrate and other stuff doesn't matter
		ser = serial.Serial('/dev/tty.usbserial-PXG7UUUG',rtscts=0,timeout=1)
		
		#Found from the DSA front panel
		addr=30
		
		#Initiate the GPIB converter
		gpib_init(addr)
		
		#Verify that the computer, converter and device are communicating correctly
		verify_communication()
	
	
	
		gpib_write("++ver")
		version = gpib_read()
		
		gpib_write("ID?")
		device_id = gpib_read()
		
		gpib_write("RDY?")
		ready_status = gpib_read()
	
		#Print out diagnostic data
# 		print "Size = " + str(len(data))
# 		print "ID = " + device_id
# 		print "Ready? " + ready_status
# 		print "Version = " + version
	
	
		trace = read_active_trace()
		#Return control to the DSA
		gpib_write("++mode 0")
	else:
		trace = load_rawfile(sys.argv[1])
	
		
		
	[header,data] = extract_header_data(trace, False)
	
	rawfilename = "gpibtest-raw.txt"
	save_rawfile(trace, rawfilename)
	rawfilename = "gpibtest-justdata.txt"	
	save_rawfile(data, rawfilename)
	
		
	
	#print data
	real = map(float,data[::2])
	imaginary = map(float,data[1::2])


	#start_freq = 65
	#delta x = 56
	#log/linear data = 41
	#complex/real = 37
	#x-axis units = 11
	#y-axis units (amplitude) = 10
	#Volts peak/rms = 9


	#Extract relevant header information
	num_data_points = int(float(header[2]))
	start_freq = float(header[65])
	delta_freq = float(header[56])

	#For X-axis log = 1, linear = 0
	log = int(float(header[41]))

	#Create frequency array
	if (log == 1):
		freq = start_freq * np.power(10,delta_freq * np.arange(num_data_points))
	else:
		freq = start_freq + delta_freq * np.arange(num_data_points)


	#Convert to magnitude
	complex_values = []
	magnitude = []
	for k in range(len(real)):
		#print k
		complex_values.append(complex(real[k],imaginary[k]))
		magnitude.append(abs(complex(real[k],imaginary[k])))
	

	app = QtGui.QApplication(sys.argv)
    	w = GUI_window(freq,magnitude,'log')
    	#w.plot_data(freq,magnitude,'log')
    	#w.setWindowTitle("Current Trace")
 	#w.show()
	sys.exit(app.exec_())
	