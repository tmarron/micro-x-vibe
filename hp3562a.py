#! /usr/bin/env python

# Try out some gpib data collection using the Prologix gpib-usb controller
#

import os
import termios
import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import sys

def gpib_init(addr) :
	ser.write("++mode 1\r")
	time.sleep(0.1)
	ser.write("++ifc\r")
	time.sleep(0.1)
	ser.write("++auto 0\r")
	time.sleep(0.1)
	ser.write("++eoi 1\r")
	time.sleep(0.1)
	ser.write("++addr " + str(addr) + "\r")
        
def gpib_read():
        ser.write("++read eoi\r")
        buffer = []
        readvalue = "data"
        while (readvalue != ""):
		readvalue = ser.readline()
		buffer.append(readvalue)
	
	buffer = [lines.replace('\r\n', '') for lines in buffer]	
		
			
	if (len(buffer[:-1]) == 1):
		return buffer[0]
	else:
		return buffer[:-1]
		
		
def gpib_write(gpibstr):
        ser.write(gpibstr + "\r")
      
def gpib_clear_device():
        ser.write("++read eoi\r")
	empty_buffer = "full"
	while (empty_buffer != ""):   
		empty_buffer = ser.readline()

def check_sync():
	gpib_write("ID?")
	device_id = gpib_read()
	if (device_id == "HP3562A"):
		print "HP3562A Functioning Properly"
	else:
		print "ID = " + device_id
		print "Bad Data Transfer - Exiting"
		sys.exit()
		

		
#
# test program...
#

ser = serial.Serial('/dev/tty.usbserial-PXG7UUUG',rtscts=0,timeout=1)

addr=30

gpib_init(addr)
gpib_clear_device()
check_sync()



gpib_write("++ver")
version = gpib_read()

gpib_write("ID?")
device_id = gpib_read()

gpib_write("RDY?")
ready_status = gpib_read()

gpib_write("DDAS")
trace = gpib_read()

#trace = map(float,trace)
print "Test = "
header = trace[0:65]
data = trace[66:]
real = map(float,data[::2])
imaginary = map(float,data[1::2])
print real
print imaginary

complex_values = []
magnitude = []
for k in range(len(real)):
	complex_values.append(complex(real[k],imaginary[k]))
	magnitude.append(abs(complex(real[k],imaginary[k])))
	

print "Size = " + str(len(data))

print "ID = " + device_id
print "Ready? " + ready_status
print "Version = " + version

plt.figure()
plt.plot(magnitude)

plt.ylim(0,1)
plt.show()

gpib_write("++mode 0")