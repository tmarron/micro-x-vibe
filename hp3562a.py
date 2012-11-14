#!/usr/bin/env python

# This program reads data from the HP 3562A DSA via (company)
# GPIB->USB converter.


import time
import sys
import math

# http://pypi.python.org/pypi/pyserial
import serial

#http://numpy.scipy.org/
import numpy as np

#http://matplotlib.sourceforge.net/
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.lines import Line2D
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams['axes.color_cycle'] = ['k', 'r', 'b']

#http://sourceforge.net/projects/pyqtx/files/latest/download?source=files
from PyQt4 import QtGui, QtCore


class Gpib():
    """GPIB"""
    def __init__(self, addr, port):
        """Initiate the GPIB controller"""
        self.ser = serial.Serial(port, rtscts=0, timeout=1)

        # Set controller to command mode
        self.ser.write("++mode 1\r")
        time.sleep(0.1)

        self.ser.write("++ifc\r")
        time.sleep(0.1)

        # Turn off auto read mode after write
        self.ser.write("++auto 0\r")
        time.sleep(0.1)

        # Turn on EOI - necessary for this device so it knows when a
        # command has been sent
        self.ser.write("++eoi 1\r")
        time.sleep(0.1)

        # Set the GPIB address. Currently at 30
        self.ser.write("++addr " + str(addr) + "\r")

        # Clear the device buffer
        self.gpib_clear_device()

    def gpib_read(self):
        '''Read from the device.'''

        # Tell the converter you want to read data
        self.ser.write("++read eoi\r")
        buffer = []
        readvalue = "data"
        # Read until there's nothing left to read
        while (readvalue != ""):
            readvalue = self.ser.readline()
            buffer.append(readvalue)

        # Get rid of the \r\n in the strings
        buffer = [lines.replace('\r\n', '') for lines in buffer]

        if (len(buffer[:-1]) == 1):
            # If the buffer only has 1 element then just return that
            # element instead of a list
            return buffer[0]
        else:
            # Otherwise return all but the last (empty) element
            return buffer[:-1]

    def gpib_write(self,gpibstr):
        '''Write to the device'''
        # Doesn't really need its own function, but might become more
        # elaborate later
        self.ser.write(gpibstr + "\r")

    def gpib_clear_device(self):
        '''Clear the device.'''
        # Clear the device buffer in case there are leftovers from
        # previous operation
        self.ser.write("++read eoi\r")
        empty_buffer = "full"
        while (empty_buffer != ""):
            empty_buffer = self.ser.readline()

    def verify_communication(self):
        '''Verify Communication'''
        gpib_write("ID?")
        device_id = gpib_read()
        if (device_id == "HP3562A"):
            print "HP3562A Functioning Properly"
        else:
            print "ID = " + device_id
            print "Bad Data Transfer - Exiting"
            sys.exit()

class Data():
    '''Data class'''

    def __init__(self, gpib_device, filename, pcb_cal, phase=False):

        # Obtain the data. Either read it from the GPIB or from a file
        if (filename==""):
            self.transfer = self.read_active_trace(gpib_device)
        else:
            self.transfer = self.load_rawfile(filename)

	self.set_accelerometer_calibrations(pcb_cal)

        #Is it a freq resp plot or single power spectrum? Default = False (single power spectrum)
        self.freq_resp = False
        self.phase_plot = False
        
        # Extract the header and the actual trace
        self.extract_header_data(False)


        # Convert the data
        self.convert_data(phase)

        # Create the frequency array
        self.create_frequency_array()
        


    def set_accelerometer_calibrations(self, pcb_cal):
    	'''Set accelerometer calibrations'''
	
	if pcb_cal:
		#PCB Accelerometers (Rough average)
		self.accelerometer_calibration = .1020	#V/g

	else:
		#Wallops Accelerometers + Charge Amps
		#This scaling is for a unit set to +/- 100Gs
		#Ours is calibrated to +/-35Gs
		#[Voltage] = A * [g-forces] + B = 0.0152 [g-forces] + 0.002836.
		#Need to multiply this by 100/35
		
		#g-forces = ([Voltage] - 0.002836.) / 0.0152 * (35. / 100.)
		#Approximate to 23g = 1.0 V
		self.accelerometer_calibration = (1.0 / 23.0) #V/g


    def read_active_trace(self, gpib_device):
        '''Read active trace'''
        gpib_device.gpib_write("DDAS")
        trace = gpib_device.gpib_read()
        print "Read data from Device"
        return trace

    def load_rawfile(self,rawfilename):
        '''Load the raw file'''
        rawfile = open(rawfilename,"r")
        trace = rawfile.readlines()
        rawfile.close()
        trace = [lines.replace('\n', '') for lines in trace]
        print "Successfully read data from: " + rawfilename
        return trace

    def extract_header_data(self,verbose):
        '''Extract the header and data from the trace'''
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
            #print self.data

        # Extract relevant header information
	try:       
		self.num_data_points = int(float(self.header[2]))
		self.start_freq = float(self.header[65])
		self.delta_freq = float(self.header[56])
		self.complex_format = int(float(self.header[37]))
	except:
		print 'ERROR READING HEADER - DUMPING HEADER AND EXITING:'
		print header
		sys.exit()
		
        # For X-axis log = 1, linear = 0
        log = int(float(self.header[41]))
        if (log==1):
            self.log = "log"
        else:
            self.log = "linear"

    def create_frequency_array(self):
        '''Create frequency array'''

        # Create frequency array
        if (self.log == 'log'):
            xdata = self.start_freq * np.power(10,self.delta_freq * np.arange(self.num_data_points))
        else:
            xdata = self.start_freq + self.delta_freq * np.arange(self.num_data_points)

        self.xdata = np.array(xdata)

    def convert_data(self, phase):
        '''Convert data'''
        # Separate the real and imaginary components
        if (self.complex_format == 1):
        	self.freq_resp = True
		self.real = np.array(map(float,self.data[::2]))
		self.imaginary = np.array(map(float,self.data[1::2]))        	
		self.complex_values = []
		ydata = []
        	if (phase == True):
        		self.phase_plot = True
			#This data set is the ratio of two measurements and we want the phase information
			#self.phase = np.arctan(self.imaginary / self.real)
			self.phase = np.arctan2(self.imaginary, self.real)
			#self.phase = np.angle(self.imaginary / self.real)
	
			ydata = self.phase * 180. / 3.14
		else:
			self.phase_plot = False
			for k in range(self.num_data_points):
				self.complex_values.append(complex(self.real[k],self.imaginary[k]))
				self.voltage_data = abs(complex(self.real[k],self.imaginary[k])) 
				#self.g_data = np.sqrt(self.voltage_data) / self.accelerometer_calibration * math.sqrt(2)
				ydata.append(self.voltage_data)
			    
        else:
        	#This data is just one measurement and we want the amplitude
		self.real = map(float,self.data)
		self.imaginary = map(float,self.data)
		
		# Convert to magnitude
		self.complex_values = []
		ydata = []
		
		for k in range(self.num_data_points):
		    #self.complex_values.append(complex(self.real[k],self.imaginary[k]))
		    #self.voltage_data = abs(complex(self.real[k],self.imaginary[k])) 
		    
		    #I think the above lines are a mistake - we just want the real component to be the voltage:
		    self.voltage_data = self.real
		    self.g_data = np.sqrt(self.voltage_data) / self.accelerometer_calibration * math.sqrt(2)
		    #ydata.append(self.g_data)
		    ydata = self.g_data

        self.ydata = np.array(ydata)


    def save_rawfile(self, rawfilename):
        '''Save the raw file'''
        rawfile = open(rawfilename+"-raw.txt","w")
        for datapoint in self.transfer:
            rawfile.write(str(datapoint)+"\n")
        rawfile.close()

    def save_nicefile(self, rawfilename):
        '''Save the raw file'''
        nicefile = open(rawfilename+".txt","w")
        nicefile.write("Hz,real,imaginary,V^2 (rms) \n")
        for freq,real,imag,mag in zip(self.xdata,self.real,self.imaginary,self.ydata):
        	nicefile.write(str(freq)+","+str(real)+","+str(imag)+","+str(mag) + "\n")
        nicefile.close()

class GUI_window(QtGui.QMainWindow):
    '''GUI Window'''
    # First input = QtGui.QMainWindow ?

    def __init__(self,args,parent=None):
        '''Initialize the GUI widget'''
        super(GUI_window, self).__init__(parent)
        
        self.working_directory = '.'
        
        #Position X, Position Y, Width, Height
        self.setGeometry(300,100,700,500)
        
        # Create the Main Widget
        self.main_widget = QtGui.QWidget()
        #self.main_widget.resize(600, 800)
        #self.main_widget.move(300, 300)
        self.setWindowTitle('HP3562A Spectrum Analyzer Datatool (SAD)')
	self.setCentralWidget(self.main_widget)


        #Add Status bar
        self.statusBar().showMessage("Waiting for commands")

	#Add Status bar
	#self.status_bar_text = QtGui.QLabel("TestTestTestTestTestTestTestTest")
	#self.statusBar().addWidget(self.status_bar_text, 1)
        
        

	#List for all the actual data
        self.trace_list = []
        
        #List for the number plot each data belongs to
        self.subplot_number = []
	
	#List for the legend labels for all the data        
        self.legend_list = []

        #List of possible colors
        self.color_list = ['k','r','b','c','m','g','y','w']
        
        #Total number of data (essentially the length of the trace_list array)
        self.num_data = 0

	#If a filename was supplied, load it up
        #I think this is no longer needed (10.31.2012)
        #if (len(args)>1):
        #    self.trace_list.append(Data("",args[1]))

        # Make the figure
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_widget)
        


        #Plot any and all data (if any)
        self.make_plots()

        # Define the toolbar
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_widget)

        # Want the plots to be in a nice vertical line on the left
        self.left_box = QtGui.QVBoxLayout()
        self.left_box.addWidget(self.canvas)
        self.left_box.addWidget(self.mpl_toolbar)

        #Add Buttons
        self.display_buttons()
        

        self.main_layout = QtGui.QHBoxLayout(self.main_widget)
        
        self.main_layout.addLayout(self.left_box)
        self.main_layout.addLayout(self.right_box)
	
        #self.setCentralWidget(self.main_widget)
        # Show the GUI
	
        #self.main_widget.show()
	self.show()
    def display_buttons(self):
        '''Display buttons'''

        # Quit Button
        self.qbtn_quit = QtGui.QPushButton('Quit', self.main_widget)
        #qbtn_quit.clicked.connect(QtCore.QCoreApplication.instance().quit)
        self.qbtn_quit.connect(self.qbtn_quit, QtCore.SIGNAL("clicked()"), app, QtCore.SLOT("quit()"))

        # Clear button
        self.qbtn_clear = QtGui.QPushButton('Clear Plots', self.main_widget)
        self.qbtn_clear.clicked.connect(self.clear)

        # Overplot button
        self.qbtn_oplot = QtGui.QPushButton('Over Plot', self.main_widget)
        self.qbtn_oplot.clicked.connect(self.oplot)

        # Addplot button
        self.qbtn_addplot = QtGui.QPushButton('Add Plot', self.main_widget)
        self.qbtn_addplot.clicked.connect(self.addplot)

        # Acquire button
        self.qbtn_acquire = QtGui.QPushButton('Acquire New Data', self.main_widget)
        self.qbtn_acquire.clicked.connect(self.acquire_newdata)
        
        # Want the buttons and stuff to be in a nice vertical line on
        # the right
        
        #Right box
        self.right_box = QtGui.QVBoxLayout()
        self.right2_box = QtGui.QVBoxLayout()
        
        #Top right box for legend labels
        self.topright_box = QtGui.QVBoxLayout()
        self.topright_box.addWidget(QtGui.QLabel("Plot Title"))
	self.plottitle_lineedit = QtGui.QLineEdit(self)
        #self.plottitle_lineedit.editingFinished.connect(self.make_title)
        self.topright_box.addWidget(self.plottitle_lineedit)
        self.topright_box.addWidget(QtGui.QLabel("Legend Labels"))
        
        #Make lines
        self.line = QtGui.QFrame(self.main_widget)
	self.line.setFrameShape(QtGui.QFrame.HLine)
	self.line.setFrameShadow(QtGui.QFrame.Sunken)
	self.line.setObjectName("line")
        self.line2 = QtGui.QFrame(self.main_widget)
	self.line2.setFrameShape(QtGui.QFrame.HLine)
	self.line2.setFrameShadow(QtGui.QFrame.Sunken)
	self.line2.setObjectName("line2")
        self.line3 = QtGui.QFrame(self.main_widget)
	self.line3.setFrameShape(QtGui.QFrame.HLine)
	self.line3.setFrameShadow(QtGui.QFrame.Sunken)
	self.line3.setObjectName("line3")
	        
        #Make Calibration buttons
   	self.widget1 = QtGui.QWidget()
        #self.widget2.setGeometry(QtCore.QRect(400, 330, 103, 39))
        self.widget1.setObjectName("widget1")
        self.calibration_label = QtGui.QLabel(self.main_widget)
        self.calibration_label.setText("Calibration Mode")
	font = QtGui.QFont()
	font.setPointSize(18)
	font.setBold(True)
	font.setWeight(75)
	self.calibration_label.setFont(font)
        self.pcb_button = QtGui.QRadioButton(self.widget1)
	self.pcb_button.setObjectName("pcb_button")
	self.pcb_button.setChecked(False)
	self.pcb_button.setText("PCB Accelerometers")
	self.wallops_button = QtGui.QRadioButton(self.widget1)
	self.wallops_button.setObjectName("wallops_button")
	self.wallops_button.setText("Wallops Accelerometers")
	self.wallops_button.setChecked(True)
		
        #Make Phase versus Ratio buttons
   	self.widget2 = QtGui.QWidget()
        #self.widget2.setGeometry(QtCore.QRect(400, 330, 103, 39))
        self.widget2.setObjectName("widget2")
        self.displaymode_label = QtGui.QLabel(self.widget2)
        self.displaymode_label.setText("Display Mode for Ratios")
	font = QtGui.QFont()
	font.setPointSize(18)
	font.setBold(True)
	font.setWeight(75)
	self.displaymode_label.setFont(font)
	
	#Not quite as good, but should work
	self.phase_plot_checkbox = QtGui.QCheckBox("Plot phase data instead of ratios", self.widget2)
	self.phase_plot_checkbox.setChecked(False)
		
	#This is the better way to do it, but has annoying radio button issues			
#       self.phase_button = QtGui.QRadioButton(self.widget2)
# 	self.phase_button.setObjectName("phase_button")
# 	self.phase_button.setChecked(True)
# 	self.phase_button.setText("Phase")
# 	self.ratio_button = QtGui.QRadioButton(self.widget2)
# 	self.ratio_button.setObjectName("ratio_button")
# 	self.ratio_button.setText("Ratio")
# 	self.ratio_button.setChecked(False)
		
				
        
        #Bottom right box for buttons
        self.botright_box = QtGui.QVBoxLayout()
        self.botright_box.addWidget(self.qbtn_acquire)	
        self.botright_box.addWidget(self.qbtn_addplot)
        self.botright_box.addWidget(self.qbtn_oplot)
        self.botright_box.addWidget(self.line)
        self.botright_box.addWidget(self.calibration_label)
	self.botright_box.addWidget(self.pcb_button)
	self.botright_box.addWidget(self.wallops_button)
        self.botright_box.addWidget(self.line2)
        
        #Another layout so the 2 sets of radio buttons don't get linked
        self.botbotright_box = QtGui.QVBoxLayout()      
        self.botbotright_box.addWidget(self.displaymode_label)
	self.botbotright_box.addWidget(self.phase_plot_checkbox)
	#self.botbotright_box.addWidget(self.phase_button)
	#self.botbotright_box.addWidget(self.ratio_button)
        self.botbotright_box.addWidget(self.line3)        
        self.botbotright_box.addWidget(self.qbtn_clear)        
        self.botbotright_box.addWidget(self.qbtn_quit)
        
        #Add the two mini layouts to the main right layout
        self.right_box.addLayout(self.topright_box)
        self.right_box.addLayout(self.botright_box)
        self.right_box.addLayout(self.botbotright_box)    
  
  
    def acquire_newdata(self):
        '''Acquire the new data'''
        
        self.statusBar().showMessage("Connecting to GPIB to aquire new data")

	#Connection settings
        addr=30
        port = '/dev/tty.usbserial-PXG7UUUG'
        
        #Establish GPIB class (at the moment this is overwritten each acquire, which probably isn't the most elegant method)
        self.dsa = Gpib(addr,port)
        
        #Check which calibration to use
        #If the pcb button is checked use it, otherwise use wallops
        pcb_cal = self.pcb_button.isChecked()
        
        #Check whether we want to plot phase or ratio information (default is ratio)
        phase = self.phase_plot_checkbox.isChecked()
        
        #Establish the new data class
        newdata = Data(self.dsa,"", pcb_cal, phase)
        
        #Append the trace to the big trace_list 
        self.trace_list.append(newdata)
        
	#Assign which plot the new data belongs to
	if (self.num_data == 0):
		self.subplot_number.append(0)
	else:
		self.subplot_number.append(self.subplot_number[-1]+1)
	
	self.num_data += 1
	
        #Get the filename base to save the new data to
        save_filename_base = self.savefile_dialog()
        
        #Save the raw and nice data        
	newdata.save_rawfile(save_filename_base)
	newdata.save_nicefile(save_filename_base)
	

		
		
	#Make the plots
        self.add_legend_label()
        self.make_plots()

	self.dsa.gpib_write("++mode 0")

		

    def oplot(self):
        '''Overplot'''
        
        if (len(self.trace_list) > 0):
		self.statusBar().showMessage("Loading data for overplotting")
		
		success = self.openfile_dialog()
		
		if success:
			#Assign which plot the new data belongs to
			if (self.num_data == 0):
				self.subplot_number.append(0)
			else:
				self.subplot_number.append(self.subplot_number[-1])
			self.num_data += 1
			
# 			opened_data = len(self.trace_list)-1
# 			self.axes.plot(self.trace_list[opened_data].xdata,self.trace_list[opened_data].ydata)
# 			self.canvas.draw()
			self.add_legend_label()
			self.make_plots()
	else:
		self.statusBar().showMessage("Can't overplot until a plot is first added")


    def addplot(self):
        '''Add new plot'''
        
        self.statusBar().showMessage("Loading data for new plot pane")

        success = self.openfile_dialog()

	if success:
		#Assign which plot the new data belongs to
		if (self.num_data == 0):
			self.subplot_number.append(0)
		else:
			self.subplot_number.append(self.subplot_number[-1]+1)
		self.num_data += 1
		
		self.add_legend_label()
		self.make_plots()



    def add_legend_label(self):
    	'''Adds a new legend label to the GUI'''
    	
        newlegend_label = QtGui.QLineEdit(self)
        
        newlegend_label.editingFinished.connect(self.make_plots)
        self.legend_list.append(newlegend_label)
        self.topright_box.addWidget(self.legend_list[self.num_data-1])
        
    
    def legend_label_changed(self):

	#Below is a real mess. I had a lot of trouble getting the legend labels correct with the right plot/line
	#This works. I should make it better, but not now.
	for k in range(len(self.axes_list)):
		locations = [i for i, x in enumerate(self.subplot_number) if x == k]

		spot_start = min(locations)
		spot_end = max(locations)
		
		lines = self.line_list[spot_start:spot_end+1]
		label_list = self.legend_list[spot_start:spot_end+1]
		labels = []
		for item in label_list:
			labels.append(str(item.text()))
			
		self.axes_list[k].legend(lines,labels,'upper left',prop={'size':10})
	

    def make_title(self):
    	'''Makes the figure title'''
    	#self.axes.set_title(self.plottitle_lineedit.text())
	self.fig.suptitle(self.plottitle_lineedit.text())
	
    def openfile_dialog(self):
        '''Open new data'''
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open a data file', self.working_directory, 'txt files (*.txt)')

        if filename:
		#Determine the file path to make that the current working directory
		self.working_directory = str(filename)
		self.working_directory = self.working_directory[0:self.working_directory.rfind('/')+1]


		#Check which calibration to use
		#If the pcb button is checked use it, otherwise use wallops
		pcb_cal = self.pcb_button.isChecked()
	        phase = self.phase_plot_checkbox.isChecked()
	        
        	newdata = Data("",filename, pcb_cal, phase)
            	self.trace_list.append(newdata)
            	return 1
        else:
        	return 0

    def savefile_dialog(self):
        '''Open new data'''
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Filename base to save new data to', self.working_directory)
	#Determine the file path to make that the current working directory
	self.working_directory = str(filename)
	self.working_directory = self.working_directory[0:self.working_directory.rfind('/')+1]


        return filename
            

    def make_plots(self):
        '''Make plots'''

        self.fig.clear()
        #Want the axes cleared every time plot() is called
        #self.axes.hold(False)

        # Take care of all the plotting
        
        self.axes_list = []
        self.line_list = []
        
        #Loop the all the traces
        for k in range(len(self.trace_list)):
		#If it's the first trace, or starting a new subplot
		if (k == 0) or (self.subplot_number[k] != self.subplot_number[k-1]):	
			self.axes = self.fig.add_subplot(max(self.subplot_number)+1,1,self.subplot_number[k]+1)
			self.axes.set_xscale(self.trace_list[k].log)
			self.axes.set_yscale('linear')
			self.axes.set_xlim(min(self.trace_list[k].xdata),max(self.trace_list[k].xdata)+1)
			self.axes.set_ylim(min(self.trace_list[k].ydata),max(self.trace_list[k].ydata))
			
			#If it's a phase plot show that in the ytitle. This is a little kludgy as I'm 
			#just assuming any phase plot will have at least 1 negative value, whereas
			#magnitude plots can't. Need a better solution later.
			if self.trace_list[k].freq_resp == True:
				if self.trace_list[k].phase_plot == True:
					self.axes.set_ylabel("Phase [Degrees]")
				else:
					self.axes.set_ylabel("Ratio")
			
			else:
				self.axes.set_ylabel("Acceleration [g]")				
				
			if (k==0):
				self.make_title()
							
			#Commented these lines out because it also erased the grid lines at f=100. Annoying!
			#if (self.subplot_number[k] != max(self.subplot_number)):
			#	self.axes.get_xaxis().set_ticks([])
			self.axes_list.append(self.axes)

		#If it's the very last line
		if (k == len(self.trace_list)-1):
			self.axes.set_xlabel("Frequency [Hz]")
			#This is making the xaxis invisible, not just the labels. Need to fix this.
			#self.axes.get_xaxis().set_visible(True)
				
		newline = Line2D(self.trace_list[k].xdata,self.trace_list[k].ydata,color=self.color_list[k])
		self.line_list.append(newline)
		self.axes.add_line(newline)		
		self.axes.grid(True, which = 'major',axis="y")
		self.axes.grid(True, which = 'both',axis="x")
		
		self.legend_label_changed()		
		
	# Re-draw the axes canvas!
	
	self.canvas.draw()
	
        self.statusBar().showMessage("Waiting for commands")
        
    def clear(self):
	#List for all the actual data
        self.trace_list = []
        
        #List for the number plot each data belongs to
        self.subplot_number = []
	
	#List for the legend labels for all the data
	for delete_listitem in self.legend_list:        
		delete_listitem.close()
        self.legend_list = []
       
        #Total number of data (essentially the length of the trace_list array)
        self.num_data = 0

	self.make_plots()	
        
class LoadFirstFile(QtGui.QMainWindow):
    '''What am I for?'''

    def __init__(self,parent=None):
        super(LoadFirstFile, self).__init__(parent)
        self.filename = QtGui.QFileDialog.getOpenFileName(self, 'Open a data file', '.', 'txt files (*.txt)')


if __name__ == "__main__":
    # QT App
    app = QtGui.QApplication(sys.argv)

    # GUI Widget
    w = GUI_window(sys.argv)

    sys.exit(app.exec_())
