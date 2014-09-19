#!/usr/bin/python

import pyqrcode, sys, Image, math, time,base64, argparse
import multiprocessing
from functools import partial

"""
An overview:
Load file as bytes. 
Base64 it.
Split file into chunks that fit in a QR code, including some metadata on the first chunk, and the chunk's number.
Create QR codes.
Create overall image.
Save.
"""

def encode(chunk,redundancy):
	bitString = pyqrcode.create(chunk,version=40,error=redundancy,mode='binary').text()
	x = y = bitString.find('\n')
	bitString = "".join(bitString.split('\n'))

	img = Image.new( 'RGB', (x,y), "white") # create a new white image
	pixels = img.load() # create the pixel map

	z = 0
	for i in range(img.size[0]):    # for every pixel:
		for j in range(img.size[1]):
			if bitString[z] == '1':
				pixels[j,i] = (0, 0, 0) # set the colour accordingly
			elif bitString[z] == '0':
				pixels[j,i] = (255, 255, 255)
			else:
				print 'What?'
				
			z += 1
	
	img = {'pixels': img.tostring(),'size': img.size,'mode': img.mode}
	return img

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("inputFile",help="The file to store on paper.")
	parser.add_argument("-o","--outputFile",help="What to call the image. Default is Out.png",default="Out.png")
	parser.add_argument("-r","--redundancy",help="The level of redundancy. Either L, M, Q or H. L = 7 percent, M = 15 percent, Q = 25, H = 30. M by default.",default="M")
	parser.add_argument("-x","--width",help='Page width in inches. Default A4',default="8.276")
	parser.add_argument("-y","--height",help='Page height in inches. Default A4',default="11.692")
	parser.add_argument("-dpi",help='If included, this will tell you if your file will fit on the page.',default="-1")
	parser.add_argument("-cores",help='The number of cores to use. Defaults to all of them.',default="-1")
	
	args = parser.parse_args()
	
	t=time.time()

	height = float(args.height)
	width = float(args.width)
	dpi = float(args.dpi)
	redundancyLevel = args.redundancy
	infile = args.inputFile
	outfile = args.outputFile
	cores = args.cores
	
	if cores == "-1":
		cores = multiprocessing.cpu_count()
	cores = int(cores)

	extraBorder = 0# MUST be even or 0 4 bibles
	squareSize = 179 + extraBorder ## The size of a code block.
	
	versionChunkSizes = {"L":2953,"M":2331,"Q":1663,"H":1273}

	chunkSize = versionChunkSizes[redundancyLevel] - 2 #From the ISO specification, minus two bytes for the chunk's number.

	aspect = width/height

	def toChrs(n):
		b = n//128
		a = n - 128*b
		return chr(a) + chr(b)
		
	def fromChrs(chrs):
		a = ord(chrs[0])
		b = ord(chrs[1])
		return a + 128*b


	f = open(infile,'rb')

	allFileBytes = base64.b64encode(f.read()) 

	infile.replace("\\","/")
	fileName = infile.split("/")[-1]

	totalFileSizeInBytes = len(allFileBytes) + len(fileName) + 9 # bytes for number of chunks and fileName length
	print "Processing", fileName, "at", totalFileSizeInBytes, "bytes." 

	area = (totalFileSizeInBytes/chunkSize) * squareSize**2

	fullX = int( math.floor(math.sqrt( aspect * area )) + 1)
	fullY = int( math.floor(fullX/aspect) + 1)

	nChunks = int(math.floor(totalFileSizeInBytes / chunkSize) + 1)

	if fullX % squareSize != 0:
		fullX = int((math.floor(fullX/squareSize) + 1) * squareSize)

	fullY = int(math.floor(fullY/squareSize) * squareSize)
	while fullX * fullY < nChunks*squareSize**2:
		fullY += squareSize
		
	gridNX = fullX/squareSize
	gridNY = fullY/squareSize
	
	if dpi != -1:
		if fullX > width*dpi or fullY > height*dpi:
			print "File too large for page at this size and resolution. Sorry."
			sys.exit(1)
		else:
			print "File will fit on page."
			
	imgs = []

	chunk = toChrs(0) + "START" + chr(len(fileName)) + fileName + toChrs(nChunks) + allFileBytes[0:(chunkSize-(9+len(fileName)))]
	chunks = [chunk]
	k = 1
	for c in range((chunkSize-(9+len(fileName))),totalFileSizeInBytes,chunkSize): #from 1, as you just did 0
		chunk = toChrs(k) + allFileBytes[c:c+chunkSize]
		chunks.append(chunk)
		k +=1
		
		
	print "Processing... This should take less than 3 minutes."


	pool = multiprocessing.Pool(cores)
	rightEncode = partial(encode, redundancy=redundancyLevel)
	imgs = pool.map(rightEncode,chunks)
	for i in range(len(imgs)):
		imgs[i] = Image.fromstring(imgs[i]['mode'], imgs[i]['size'], imgs[i]['pixels'])
		
	fullImg = Image.new( 'RGB', (fullX,fullY), "white") # create a new white image

	z = 0
	for i in range(gridNX):
		for j in range(gridNY):
			if z >= nChunks: break
			fullImg.paste(imgs[z],(squareSize*i+extraBorder/2,squareSize*j+extraBorder/2))
			z += 1

	fullImg = fullImg.resize((fullImg.size[0]*2,fullImg.size[1]*2))
	w = open(outfile,'wb')
	fullImg.save(w,'png')
	w.close()

	print "Time taken:", time.time() - t, "seconds"
	print "Stored as", outfile
