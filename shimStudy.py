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

rootdir = 'vibe_plots/8-16-2012/'

def readSpectrum(fname):
	# has header, plus 4 comma-separated columns of freq, real, im, amplitude
	spectrumColumns = genfromtxt(fname, delimiter=',', dtype='f', skip_header=1)
	
	freq = spectrumColumns[:,0]
	amplitude = spectrumColumns[:,3]
	
	return freq, amplitude

# plotTwo - plot two traces together for comparison
# A = with shims, or input...
# B = without shims, or output...
def plotTwo(freq, ampA, ampB, titleStr = '', pdf = None, legendNames = ['','']):
	semilogx(freq, ampA, 'k')
	semilogx(freq, ampB, 'b')
	xlim(10, 600)
	legend(legendNames)
	title(titleStr)
	ylabel('amplitude [arb]')
	grid(which = 'both', axis='x')

	if pdf is not None:
		pdf.savefig()
		clf()
	else:
		show()

def plotAB(fnumA, fnumB, titleStr = '', pdf = None, legendNames = ['','']):
	freq, ampA = readSpectrum(rootdir+str(fnumA)+'.txt')
	freq, ampB = readSpectrum(rootdir+str(fnumB)+'.txt')
	plotTwo(freq, ampA, ampB, titleStr, pdf, legendNames)

def plotXferAB(fnumAin, fnumAout, fnumBin, fnumBout, titleStr='',pdf=None,legendNames=['','']):
	freq, ampAin = readSpectrum(rootdir+str(fnumAin)+'.txt')
	freq, ampAout = readSpectrum(rootdir+str(fnumAout)+'.txt')
	freq, ampBin = readSpectrum(rootdir+str(fnumBin)+'.txt')
	freq, ampBout = readSpectrum(rootdir+str(fnumBout)+'.txt')

	# data given in V^2, so need to take root for xfer function:
	ampA = sqrt(ampAout/ampAin)
	ampB = sqrt(ampBout/ampBin)
	plotTwo(freq, ampA, ampB, titleStr, pdf, legendNames)
	

if __name__ == '__main__':
	# with and without shims:
	pp = PdfPages(rootdir+'withwithout.pdf')
	plotAB(1,10,'Insert Z',pp,['with shims', 'without'])
	plotAB(2,11,'FEA Z',pp,['with shims', 'without'])
	plotAB(3,12,'FEA/Insert Z',pp,['with shims', 'without'])
	plotAB(4,13,'Insert Y',pp,['with shims', 'without'])
	plotAB(5,14,'FEA Y',pp,['with shims', 'without'])
	plotAB(6,15,'FEA/Insert Y',pp,['with shims', 'without'])
	plotAB(7,16,'Insert X',pp,['with shims', 'without'])
	plotAB(8,17,'FEA X',pp,['with shims', 'without'])
	plotAB(9,18,'FEA/Insert X',pp,['with shims', 'without'])
	pp.close()

	# transfer functions:
	pp = PdfPages(rootdir+'xfer.pdf')
	#	lid/skin
	plotXferAB(28,29,19,20, 'XFER lid/skin Z', pp, ['with shims','without'])
	plotXferAB(25,26,22,23, 'XFER lid/skin Y', pp, ['with shims','without'])
	#	insert/skin
	#	fea/skin
	#	insert/lid
	#	fea/lid
	#	fea/insert
	plotXferAB(1,2,10,11, 'XFER fea/insert Z', pp, ['with shims','without'])
	plotXferAB(4,5,13,14, 'XFER fea/insert Y', pp, ['with shims','without'])
	plotXferAB(7,8,16,17, 'XFER fea/insert X', pp, ['with shims','without'])
	pp.close()

