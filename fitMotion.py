import numpy as np
import matplotlib
matplotlib.use("Agg")	# for video
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.animation as anim
import pdb
import sys
import os
from matplotlib.backends.backend_pdf import PdfPages

root = '/Users/jmrv/Documents/school/mit/research/micro-x/vibe/hsv/'
fps = 2900		# frames per second, on all videos

# return with a 5 pixel black border.
def border(im):
	w = 5
	mask = np.ones(im.shape)
	mask[0:w,:] = 0
	mask[:,0:w] = 0
	mask[-w:,:] = 0
	mask[:,-w:] = 0
	return im*mask

# shift an image by dx pixels right and dy pixels down.
def shift(im, dx, dy):
	nx = int(np.fix(dx))
	ny = int(np.fix(dy))
	ddx = dx-nx
	ddy = dy-ny

	# move whole pixels:
	rolled = np.roll(im,ny,axis=0)
	rolled = np.roll(rolled,nx,axis=1)

	# sum contributions from sub-pixel shift: 
	rolly = np.roll(rolled,int(np.sign(ddy)),axis=0)
	rollx = np.roll(rolled,int(np.sign(ddx)),axis=1)
	rollxy = np.roll(rolly,int(np.sign(ddx)),axis=1)

	shifted = rolled*(1-abs(ddx))*(1-abs(ddy))					# how much is kept
	shifted = shifted + rolly*(1-abs(ddx))*abs(ddy)				# from top/bottom pixel
	shifted = shifted + rollx*abs(ddx)*(1-abs(ddy))				# from side pixel
	shifted = shifted + rollxy*abs(ddx)*abs(ddy)				# from corner neighbor pixel
			
	return shifted

# the algorithm.
# starting at (x0,y0), look in a square region for best fit. if best fit is on the edge,
# restart fit, centering there. should take less time than a huge fine grid. 
def findBestLoc(im, im0, x0, y0):
	best = None
	bestxy = None
	im = border(im)

	w = 1
	dd = 0.1
	ep = dd/10
	lastRadius = None
	# can optimize with cacheing, but hey:
	while True:
		delta = np.arange(-dd*w,(dd+ep)*w,dd/5)		# fraction pixel grid
		for dx in delta:
			for dy in delta:
				if lastRadius is not None and np.sqrt(dx**2 + dy**2) < lastRadius:
					# been there
					continue
				shifted = border(shift(im0, x0+dx, y0+dy))

				# evaluate score:
				score = np.sum((shifted - im)**2)
				if best is None or score < best:
					best = score
					bestxy = [dx,dy]
		onborder = (bestxy[0] == delta[0] or bestxy[0] == delta[-1] or bestxy[1] == delta[0] or bestxy[1] == delta[-1])
		if onborder:	
			# widen search
			lastRadius = dd*w
			w = w + 1
			print w
		else:
			break

	print bestxy
	return np.array(bestxy) + np.array([x0,y0])

# adapted from: http://matplotlib.org/examples/animation/moviewriter.html
def makeVideo(images, traj, fname, bounds):
	FFMpegWriter = anim.writers['ffmpeg']
	writer = FFMpegWriter(fps=5)

	x0 = (bounds[0]+bounds[1])/2
	y0 = (bounds[2]+bounds[3])/2
	scale = 50
	
	fig = plt.figure()
	p1 = plt.imshow(images[0], cmap='gray', extent = bounds, interpolation='nearest')
	p2, = plt.plot(x0,y0,'ro')
	p3, = plt.plot([],[],'y-')

	n = len(images)
	with writer.saving(fig, fname, n):
		for i in range(n):
			dx = traj[i][0]
			dy = traj[i][1]
			p1.set_data(images[i])
			p2.set_data(x0+scale*dx,y0+scale*dy)
			p3.set_data(x0+scale*traj[0:i+1,0], y0+scale*traj[0:i+1,1])
			writer.grab_frame()

# load all the cropped frames in order:
def loadData(folder, bounds):
	files = os.listdir(folder)
	for f in files:
		if f[0:-1] is not '.tif':
			files.remove(f)
	ntif = len(files)

	images = []
	for i in range(ntif):
		img = mpimg.imread(folder+str(i)+'.tif')
		images.append(img[bounds[3]:bounds[2], bounds[0]:bounds[1]])
	return images	

def getBounds(subdir):
	bounds = [0,800,600,0] # full
	
	img = mpimg.imread(root+subdir+'0.tif')	
	pp = PdfPages('/Users/jmrv/Desktop/bounds.pdf')
	plt.imshow(img, cmap='gray',interpolation='nearest',extent=bounds)
	print('look at the file on the desktop for bounds')
	pp.savefig()
	pp.close()

	x_l = np.double(raw_input('leftmost x: '))
	x_r = np.double(raw_input('rightmost x: '))
	y_t = np.double(raw_input('top y: '))
	y_b = np.double(raw_input('bottom y: '))
	
	return [x_l,x_r,y_b,y_t] 		# cropped

def runOne(subdir):
	if subdir[-1] != '/':
		subdir = subdir + '/'

	bounds = getBounds(subdir)
	
	images = loadData(root+subdir, bounds)

	traj = [np.zeros(2)]
	for i in range(1,len(images)):
		xy = findBestLoc(images[i],images[0],traj[-1][0],traj[-1][1])
		traj.append(xy)
	traj = np.array(traj)

	np.savetxt(root+subdir+'trajectory.txt',traj,delimiter=',')

	print('\n\nmaking video....\n\n')
	fname = root+subdir+subdir[0:-1]+'.mp4'
	makeVideo(images, traj, fname,bounds)
	print('wrote '+fname)

def findFreqs(subdir):
	if subdir[-1] != '/':
		subdir = subdir + '/'
	traj = np.genfromtxt(root+subdir+'trajectory.txt',delimiter=',')
	x = traj[:,0]
	y = traj[:,1]
	dt = 1.0/fps
	t = np.arange(len(x))*dt

	# timeseries:
	pp = PdfPages('/Users/jmrv/Desktop/'+subdir[0:-1]+'.pdf')
	plt.subplot(2,1,1)
	plt.plot(t, x)
	plt.ylabel('Y (pixel fraction)')
	plt.subplot(2,1,2)
	plt.plot(t, y)
	plt.ylabel('X (pixel fraction)')
	plt.xlabel('time (s)')
	pp.savefig()

	# frequency response:
	x_hat = np.abs(np.fft.fft(x))
	y_hat = np.abs(np.fft.fft(y))	
	f = np.fft.fftfreq(len(x),d=dt)
	
	frange = np.where(np.double(f>5)*np.double(f<500))
	x_hat = x_hat[frange]
	y_hat = y_hat[frange]
	f = f[frange]

	plt.clf()
	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	ax1.plot(f, x_hat, 'r-')
	ax1.set_xlabel('frequency (Hz)')
	ax1.set_ylabel('Y power', color='r')
	for tl in ax1.get_yticklabels():
		tl.set_color('r')
	ax2 = ax1.twinx()
	ax2.plot(f, y_hat, 'b-')
	ax2.set_ylabel('X power', color='b')
	for tl in ax2.get_yticklabels():
		tl.set_color('b')

	ymax = np.max( [np.max(x_hat), np.max(y_hat)])
	ax1.set_ylim(0,ymax)
	ax2.set_ylim(0,ymax)

	pp.savefig()
	pp.close()
	

if __name__ == '__main__':
	if len(sys.argv)>1:
		subdir = sys.argv[1]
		print('taking subdir = '+subdir)
	#runOne(subdir)
	findFreqs(subdir)

	#testVideo()
	#run()
	#testShift()

