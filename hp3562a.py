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





#==============================================================================		
#=======================================DATA CLASS
#==============================================================================		
class data():


	#=======================================INITIALIZE
	def __init__(self, filename):
		
		#Obtain the data. Either read it from the GPIB or from a file
		if (filename==""):
			self.transfer = self.read_active_trace()
		else:
			self.transfer = self.load_rawfile(filename)
		
		#Extract the header and the actual trace	
		self.extract_header_data(False)
		
		#Create the frequency array
		self.create_frequency_array()
		
		#Convert the data
		self.convert_data()
		
	#==============================================================================		



				

	#=======================================READ THE ACTIVE TRACE
	def read_active_trace(self):
		gpib_write("DDAS")
		trace = gpib_read()
		print "Read data from Device"
		return trace
	#==============================================================================		





	#=======================================LOAD THE RAWFILE
	def load_rawfile(self,rawfilename):
		rawfile = open(rawfilename,"r")
		trace = rawfile.readlines()
		rawfile.close()
		trace = [lines.replace('\n', '') for lines in trace]
		print "Successfully read data from: " + rawfilename
		return trace
	#==============================================================================	





	#=======================================EXTRACT THE HEADER AND DATA FROM THE TRACE
	def extract_header_data(self,verbose):
		#start_freq = 65
		#delta x = 56
		#log/linear data = 41
		#complex/real = 37
		#x-axis units = 11
		#y-axis units (amplitude) = 10
		#Volts peak/rms = 9
		
		
		
		self.header = self.transfer[0:67]
		self.data = self.transfer[67:]
		if (verbose == True):
			print "Header:"
			for k, lines in enumerate(self.header):
				print k, lines
				
			print "Data:"
			print self.data
			
		#Extract relevant header information
		self.num_data_points = int(float(self.header[2]))
		self.start_freq = float(self.header[65])
		self.delta_freq = float(self.header[56])
	
		#For X-axis log = 1, linear = 0
		log = int(float(self.header[41]))
		if (log==1):
			self.log = "log"
		else:
			self.log = "linear"
		
	#==============================================================================		





	#=======================================CREATE FREQUENCY ARRAY
	def create_frequency_array(self):
		#Create frequency array
		if (self.log == 1):
			xdata = self.start_freq * np.power(10,self.delta_freq * np.arange(self.num_data_points))
		else:
			xdata = self.start_freq + self.delta_freq * np.arange(self.num_data_points)
			
		self.xdata = np.array(xdata)
	#==============================================================================		






	#=======================================CONVERT DATA
	def convert_data(self):
		#Separate the real and imaginary components
		self.real = map(float,self.data[::2])
		self.imaginary = map(float,self.data[1::2])
		
		#Convert to magnitude
		self.complex_values = []
		ydata = []
		for k in range(len(self.real)):
			#print k
			self.complex_values.append(complex(self.real[k],self.imaginary[k]))
			ydata.append(abs(complex(self.real[k],self.imaginary[k])))
			
		self.ydata = np.array(ydata)
	#==============================================================================		





	#=======================================SAVE THE RAWFILE
	def save_rawfile(self, rawfilename):
		rawfile = open(rawfilename,"w")
		for datapoint in trace:
			rawfile.write(str(datapoint)+"\n")
		rawfile.close()
	#==============================================================================		





#==============================================================================		
#==============================================================================		
#==============================================================================		









#==============================================================================		
#=======================================GUI WINDOW CLASS
#==============================================================================		
class GUI_window(QtGui.QMainWindow):
	#First input = QtGui.QMainWindow ?
        
        
        
        #=======================================INITIALIZE MAIN GUI WIDGET
	def __init__(self,active_trace,parent=None):
   		super(GUI_window, self).__init__(parent)
   		#Create the Main Widget
   		self.main_widget = QtGui.QWidget()
		self.main_widget.resize(800, 600)
		self.main_widget.move(300, 300)
		self.main_widget.setWindowTitle('HP3562A GUI')     
		
		#Make the figure
		self.fig = Figure()
        
		#add subplot
		self.axes = self.fig.add_subplot(111)
		
		#Want the axes cleared every time plot() is called
		#self.axes.hold(False)
	
		#Take care of all the plotting
		self.plt = self.axes.plot(active_trace.xdata,active_trace.ydata)
		self.axes.set_xscale(active_trace.log)
		self.axes.set_xlim(min(active_trace.xdata),max(active_trace.xdata))
		self.axes.grid(True, 'both')
		self.canvas = FigureCanvas(self.fig)
		self.canvas.setParent(self.main_widget)
		
		#Define the toolbar	
		self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_widget)
			
		#Want the plots to be in a nice vertical line
		self.vertical_widgets = QtGui.QVBoxLayout(self.main_widget)
		
		self.vertical_widgets.addWidget(self.canvas)
		self.vertical_widgets.addWidget(self.mpl_toolbar)

		
		#Add Buttons
		self.display_buttons()
		#self.setCentralWidget(self.main_widget)
		#Show the GUI
		self.main_widget.show()
	#==============================================================================		




	#=======================================DISPLAY BUTTONS
	def display_buttons(self):
	
		#Quit Button
		qbtn_quit = QtGui.QPushButton('Quit', self.main_widget)
		#qbtn_quit.clicked.connect(QtCore.QCoreApplication.instance().quit)
		qbtn_quit.connect(qbtn_quit, QtCore.SIGNAL("clicked()"), app, QtCore.SLOT("quit()"))
		qbtn_quit.resize(qbtn_quit.sizeHint())
		qbtn_quit.move(700, 50)  
		
		
		#Save plot button
		qbtn_addplot = QtGui.QPushButton('Over Plot', self.main_widget)
		#qbtn_addplot.connect(qbtn_addplot, QtCore.SIGNAL("clicked()"), self.oplot())
		qbtn_addplot.clicked.connect(self.oplot)
		qbtn_addplot.resize(qbtn_addplot.sizeHint())
		qbtn_addplot.move(700, 100)  		
	#==============================================================================		


	
	
	#=======================================ADD NEW PLOTS
	def oplot(self):
	    	filename = QtGui.QFileDialog.getOpenFileName(self, 'Open a data file', '.', 'txt files (*.txt)')
        
        	if filename:
        		
        		new_trace = data(filename)
	
	
		self.axes.plot(new_trace.xdata,new_trace.ydata)
		self.canvas.draw()
	#==============================================================================		
	
		
		
		
		
#==============================================================================		
#==============================================================================		
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
	
	
		active_trace = data(sys.argv[1])
		
		#Return control to the DSA
		gpib_write("++mode 0")
	else:
		active_trace = data(sys.argv[1])
		
	
	app = QtGui.QApplication(sys.argv)
    	w = GUI_window(active_trace)
    	#w.plot_data(freq,magnitude,'log')
    	#w.setWindowTitle("Current Trace")
 	#w.show()
	sys.exit(app.exec_())
	