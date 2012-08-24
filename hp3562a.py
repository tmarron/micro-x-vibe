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
		
	
		#Convert the data
		self.convert_data()

		#Create the frequency array
		self.create_frequency_array()		
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
		self.complex_format = int(float(self.header[37]))
		
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

		if (self.log == 'log'):
			xdata = self.start_freq * np.power(10,self.delta_freq * np.arange(self.num_data_points))
		else:
			xdata = self.start_freq + self.delta_freq * np.arange(self.num_data_points)
			
		self.xdata = np.array(xdata)
	#==============================================================================		






	#=======================================CONVERT DATA
	def convert_data(self):
		#Separate the real and imaginary components
		if (self.complex_format == 1):
			self.real = map(float,self.data[::2])
			self.imaginary = map(float,self.data[1::2])
		else:
			self.real = map(float,self.data)
			self.imaginary = map(float,self.data)	
			
			
		#Convert to magnitude
		self.complex_values = []
		ydata = []
		
		for k in range(self.num_data_points):
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
	def __init__(self,trace,parent=None):
   		super(GUI_window, self).__init__(parent)
   		#Create the Main Widget
   		self.main_widget = QtGui.QWidget()
		self.main_widget.resize(800, 600)
		self.main_widget.move(300, 300)
		self.main_widget.setWindowTitle('HP3562A GUI')     
		
		
		self.trace_list =[]
		self.trace_list.append(trace)
		
		
		#Make the figure
		self.fig = Figure()
        
		#add subplot
		self.make_plots()
		
		
		#Define the toolbar	
		self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_widget)
		
	
			
		#Want the plots to be in a nice vertical line on the left
		self.left_box = QtGui.QVBoxLayout()
		self.left_box.addWidget(self.canvas)
		self.left_box.addWidget(self.mpl_toolbar)



		#Add Buttons
		self.display_buttons()
		

		
		self.main_layout = QtGui.QHBoxLayout(self.main_widget)
		self.main_layout.addLayout(self.left_box)
		self.main_layout.addLayout(self.right_box)

		

		#self.setCentralWidget(self.main_widget)
		#Show the GUI
		self.main_widget.show()
	#==============================================================================		




	#=======================================DISPLAY BUTTONS
	def display_buttons(self):
	
		#Quit Button
		self.qbtn_quit = QtGui.QPushButton('Quit', self.main_widget)
		#qbtn_quit.clicked.connect(QtCore.QCoreApplication.instance().quit)
		self.qbtn_quit.connect(self.qbtn_quit, QtCore.SIGNAL("clicked()"), app, QtCore.SLOT("quit()"))		
		
		#Overplot button
		self.qbtn_oplot = QtGui.QPushButton('Over Plot', self.main_widget)
		self.qbtn_oplot.clicked.connect(self.oplot)

		#Addplot button
		self.qbtn_addplot = QtGui.QPushButton('Add Plot', self.main_widget)
		self.qbtn_addplot.clicked.connect(self.addplot)			
		
		
		
		#Want the buttons and stuff to be in a nice vertical line on the right
		self.right_box = QtGui.QVBoxLayout()
		self.right_box.addWidget(self.qbtn_quit)
		self.right_box.addWidget(self.qbtn_oplot)
		self.right_box.addWidget(self.qbtn_addplot)
	#==============================================================================		



	
	
	#=======================================ADD OVERPLOT
	def oplot(self):
		self.openfile_dialog()
		self.axes.plot(self.trace.xdata,self.trace.ydata)
		self.canvas.draw()
	#==============================================================================		
	
	
	
	
	
	#=======================================ADD NEW PLOT
	def addplot(self):
		self.openfile_dialog()
		self.make_plots()
		#self.axes = self.fig.add_subplot(212)
		#self.axes.plot(self.trace_list[len(self.trace_list)-1].xdata,self.trace_list[len(self.trace_list)-1].ydata)
		#self.canvas.draw()
	#==============================================================================		
			
	
	
	
	

	#=======================================OPEN NEW DATA
	def openfile_dialog(self):
	    	filename = QtGui.QFileDialog.getOpenFileName(self, 'Open a data file', '.', 'txt files (*.txt)')
        
        	if filename:
        		self.trace_list.append(data(filename))
	#==============================================================================		
	
	
		

			
	#=======================================MAKE PLOTS
	def make_plots(self):
		
		
		self.fig.clear()
		#Want the axes cleared every time plot() is called
		#self.axes.hold(False)
	
	
		#Take care of all the plotting
		for k in range(len(self.trace_list)):
			self.axes = self.fig.add_subplot(len(self.trace_list),1,k+1)		
			self.plt = self.axes.plot(self.trace_list[k].xdata,self.trace_list[k].ydata)
			self.axes.set_xscale(self.trace_list[k].log)
			self.axes.set_xlim(min(self.trace_list[k].xdata),max(self.trace_list[k].xdata))
			self.axes.grid(True, 'both')
			
		self.canvas = FigureCanvas(self.fig)
		self.canvas.setParent(self.main_widget)
		self.canvas.draw()
		self.main_widget.show()	
	#==============================================================================		
		
		
		
		
#==============================================================================		
#==============================================================================		
#==============================================================================		
        

class load_first_file(QtGui.QMainWindow):

	def __init__(self,parent=None):
   		 super(load_first_file, self).__init__(parent)
		 self.filename = QtGui.QFileDialog.getOpenFileName(self, 'Open a data file', '.', 'txt files (*.txt)')

        
        

#=======================================MAIN PROGRAM		
if __name__ == "__main__":


	app = QtGui.QApplication(sys.argv)


	if len(sys.argv) == 1:
		#If no argument is passed then ask the user to pick one	
		first_file = load_first_file()
       		first_trace = data(first_file.filename)
        		
        else:
        	if (sys.argv[1] == "gpib"):
        		#Read from the GPIB Controller
        	
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
	 		print "Size = " + str(len(data))
	 		print "ID = " + device_id
			print "Ready? " + ready_status
	 		print "Version = " + version
		
		
			first_trace = data(sys.argv[1])
			
			#Return control to the DSA
			gpib_write("++mode 0")
		else:
			#Load the indicated filename
			first_trace = data(sys.argv[1])
		
	
    	w = GUI_window(first_trace)
    	#w.plot_data(freq,magnitude,'log')
    	#w.setWindowTitle("Current Trace")
 	#w.show()
	sys.exit(app.exec_())
	