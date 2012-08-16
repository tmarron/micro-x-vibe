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
	f = []
	A = []
	
	fp = open(fname)
	lines = fp.readlines()
	fp.close()
	lines = lines[1:]	# header
	for l in lines:
		entries = l.strip().split(',')
		f.append(double(entries[0]))
		A.append(double(entries[3]))

	f = array(f)
	A = array(A)
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
