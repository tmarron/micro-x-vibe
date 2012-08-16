# ---------------
# transfer-function
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
	data_array = numpy.genfromtxt(fname,delimiter=',',dtype='f',skip_header=1)
	
	f = data_array[:,0]
	A = data_array[:,3]
	
	return f, A

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
