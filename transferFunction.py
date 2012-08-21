# ---------------
# transferFunction
#
# jmrv 08.2012
# 
# given two vibe datasets from marimba, it calculates the transfer function
# ---------------

from numpy import *
from matplotlib.pyplot import *
import multiprocessing as multi

def readSpectrum(fname):
	# has header, plus 4 comma-separated columns of freq, real, im, amplitude
	data_array = genfromtxt(fname,delimiter=',',dtype='f',skip_header=1)
	
	f = data_array[:,0]
	A = data_array[:,3]
	
	return f, A
	
def converttog(inputSpectrum, outputSpectrum, accelerometer):
	#This function will convert values from voltages to acceleration (g's)
	#This can be moved / modified / inserted elsewhere, it's just a placeholder for now
	
	#3-axis internal accelerometers
	fea_x = 101.0 		 #mV/g
	fea_y = 104.1 		 #mV/g
	fea_z = 104.1 		 #mV/g
	
	
	insert_x = 103.2	 #mV/g
	insert_y = 102.3	 #mV/g
	insert_z = 104.5	 #mV/g
	
	#Charge amps
	#Charge amps are set to high gain mode which means they have a gain of 10-100 mV/pC
	#However I'm not yet sure where in this range they operate. Emailed wallops for more detail
	charge_amp = 10		mV/pC #WARNING - JUST A PLACEHOLDER FOR NOW
	
	
	#single axis external accelerometers
	skin_y = 16.51 * charge_amp	#(pC/g) * (mV/pC) = mV/g (#12540) (measured at 100 Hz with deviations <5% in our bandpass)
	skin_z = 16.16 * charge_amp	#mV/g (#12598)
	lmo_y =  17.85 * charge_amp	#mV/g (#12534)
	lmo_z =  17.71 * charge_amp	#mV/g (#12558)
	




def makeTransfer(inputSpectrum, outputSpectrum):
	f_in, A_in = readSpectrum(inputSpectrum)
	f_out, A_out = readSpectrum(outputSpectrum)

	xfer = A_out/A_in

	plot(f_in, xfer)
	show()

if __name__ == "__main__":
	inputSpectrum = sys.argv[1]
	outputSpectrum = sys.argv[2]
	makeTransfer(inputSpectrum, outputSpectrum)
	print 'success'
