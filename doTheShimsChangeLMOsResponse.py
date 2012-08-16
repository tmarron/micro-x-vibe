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

scaling = 1e4
A_with = A_with*scaling
A_without = A_without*scaling

subplot(211)
semilogx(f, A_with, 'k')
semilogx(f, A_without, 'b')
xlim(10, 600)
legend(['with shims','without'])
title('frequency shift from adding shims: Insert')
ylabel('amplitude [arb]')
grid(which = 'both', axis='x')

subplot(212)
plot(f, A_with, 'k')
plot(f, A_without, 'b')
xlim(40,100)
xlabel('frequency [Hz]')
ylabel('amplitude [arb]')

show()

# FEA data:
withshims = 'vibe_plots/8-15-2012/13.txt'
without = 'vibe_plots/8-15-2012/7.txt'

f, A_with = readSpectrum(withshims)
f, A_without = readSpectrum(without)

scaling = 1e4
A_with = A_with*scaling
A_without = A_without*scaling

subplot(211)
semilogx(f, A_with, 'k')
semilogx(f, A_without, 'b')
xlim(10, 1000)
legend(['with shims','without'])
title('frequency shift from adding shims: FEA')
ylabel('amplitude [arb]')
grid(which = 'both', axis='x')

subplot(212)
plot(f, A_with, 'k')
plot(f, A_without, 'b')
xlim(40,100)
xlabel('frequency [Hz]')
ylabel('amplitude [arb]')
ylim(0,3)

show()

print '\n looks like the resonant frequency shifts from 52 Hz to 58 Hz when the shims are added. \n'
