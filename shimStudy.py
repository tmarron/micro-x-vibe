# ---------------
# shimStudy.py
# do the shims change lmo's response?
#
# jmrv 08.2012
# 
# looking at data from the low-frequency buttkicker 
# ---------------

from numpy import *
from matplotlib.pyplot import *
from matplotlib.backends.backend_pdf import PdfPages

def readSpectrum(fname):
	# has header, plus 4 comma-separated columns of freq, real, im, amplitude
	spectrumColumns = genfromtxt(fname, delimiter=',', dtype='f', skip_header=1)
	
	freq = spectrumColumns[:,0]
	amplitude = spectrumColumns[:,3]
	
	return freq, amplitude

def plotWithWithout(fnumWith, fnumWithout, titleStr = '', pdf = None):
	rootdir = 'vibe_plots/8-16-2012/'
	freq, ampWith = readSpectrum(rootdir+str(fnumWith)+'.txt')
	freq, ampWithout = readSpectrum(rootdir+str(fnumWithout)+'.txt')

	semilogx(freq, ampWith, 'k')
	semilogx(freq, ampWithout, 'b')
	xlim(10, 600)
	legend(['with shims','without'])
	title(titleStr)
	ylabel('amplitude [arb]')
	grid(which = 'both', axis='x')
	
	pdf.savefig()
	clf()
	
if __name__ == '__main__':
	pp = PdfPages('vibe_plots/8-16-2012/withwithout.pdf')
	plotWithWithout(1,10,'Insert Z',pp)
	plotWithWithout(2,11,'FEA Z',pp)
	plotWithWithout(3,12,'FEA/Insert Z',pp)
	plotWithWithout(4,13,'Insert Y',pp)
	plotWithWithout(5,14,'FEA Y',pp)
	plotWithWithout(6,15,'FEA/Insert Y',pp)
	plotWithWithout(7,16,'Insert X',pp)
	plotWithWithout(8,17,'FEA X',pp)
	plotWithWithout(9,18,'FEA/Insert X',pp)
	pp.close()
