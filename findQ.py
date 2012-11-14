'''
findQ.py

10.2012 jmrv

skeleton code to find the Q of a frequency response in the 'peaky approximation'

otherwise, the functional form of the amplitude (normalized to f = 0 Hz) is:

A(f, Q) = 1.0/sqrt( (1 - Omega**2)**2 + (Omega/Q)**2 )

where

Omega = 2*pi*f/w_0
w_0 = sqrt(k/m)
'''

from numpy import *
from matplotlib.pyplot import *
import sys

def obtain_data(filename):
	data_array = np.genfromtxt(filename,delimiter=',',dtype='f',skip_header=1)
	freqs = data_array[:,0]
	real = data_array[:,1]
	imaginary = data_array[:,2]
	peak = data_array[:,3]
	return freqs, peak

def main(filename, f_low, f_high, titleStr = ''):

	print "Loading File: " + filename
	print "Starting at Frequency: " + str(f_low)
	print "Ending at Frequency: " + str(f_high)
	'''
	freqs - 			the 'x-axis' of frequencies
	gs - 				the corresponding g^2/Hz read from wallops data, e.g.
	f_low, f_high - 	bracket the peak
	titleStr -			for the plot (optional)
	'''
	
	#Convert from strings to floats
	f_low = float(f_low)
	f_low = float(f_low)
	
	
	freqs, gs = obtain_data(filename)

	fslice = np.logical_and(freqs>f_low, freqs<f_high)

	f = freqs[fslice]
	g2 = gs[fslice]

	
	# find q:
	E = g2			# proportional to energy, the context in which Q is used
	E0 = max(E)		# max
	f0 = f[where(E==E0)[0][0]]
	peakIdxs = where(E>E0/2+.01)[0]
	up = peakIdxs[0]
	dn = peakIdxs[-1]

	# range
	f1 = f[up-1]	+(E0/2-E[up-1])/(E[up]-E[up-1])	*(f[up]-f[up-1])
	f2 = f[dn]		+(E[dn]-E0/2)/(E[dn]-E[dn+1])	*(f[dn+1]-f[dn])
	Q = f0/(f2 - f1)	# Q roughly the max freq over the range

	plot(f, g2)
	ylabel('Ratio of Accelerations')
	xlabel('Frequency [Hz]')
	title(titleStr + ' Q = '+ '%.1f' % Q)
	plot([f1, f2], [E0/2, E0/2], 'k')
	text(f0, E0*0.55, 'df = '+ '%.1f' % (f2-f1) +' Hz', ha='center')
	text(f0, E0*0.45, '@ '+ '%.1f' % (f0) +' Hz', ha='center')
	xlim(10,60)
	show()
	
if __name__ == "__main__":
	main(sys.argv[1],sys.argv[2],sys.argv[3])

