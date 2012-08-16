# ---------------
# do the shims change lmo's response?
#
# jmrv 08.2012
# 
# looking at data from the low-frequency buttkicker 
# ---------------

from numpy import *
from matplotlib.pyplot import *
import multiprocessing as multi

from transferFunction import readSpectrum

# insert data:
withshims = 'vibe_plots/8-15-2012/12.txt'
without = 'vibe_plots/8-15-2012/6.txt'

f, A_with = readSpectrum(withshims)
f, A_without = readSpectrum(without)

semilogx(f, A_with, 'k')
semilogx(f, A_without, 'b')
xlim(10, 600)
legend(['with shims','without'])
title('frequency shift from adding shims')
xlabel('frequency [Hz]')
ylabel('amplitude [arb]')

show()
