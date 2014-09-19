import zbar, Image, sys, math, base64, argparse

parser = argparse.ArgumentParser()
parser.add_argument("inputFile",help="The scanned image to read.")
parser.add_argument("-o","--outputFile",help="What the read file should be called. Defaults to the stored file's name. Warning: this file will be replaced.",default="-1")
args = parser.parse_args()

infile = args.inputFile

"""
Read the QR codes, reassemble the file.

The scanning procedure takes subsets of the image, because the library used struggles with the density. Which is pretty fair.

"""

print "Searching for the header QR, this may take a few seconds..."

def fromChrs(chrs):
	a = ord(chrs[0])
	b = ord(chrs[1])
	return a + 128*b
	
wholeIm = Image.open(infile).convert('L')

dataDic = {}

corner = wholeIm
if wholeIm.size[0] > 1000 and wholeIm.size[1] > 1000:
	corner = wholeIm.crop((0,0,600,600))

scanner = zbar.ImageScanner()
scanner.parse_config('enable')
syms = []
sub = corner
width, height = sub.size
raw = sub.tostring()
# wrap image data
zImage = zbar.Image(width, height, 'Y800', raw)
# scan the image for barcodes
result = scanner.scan(zImage)
for sym in zImage:
	if len(sym.data) > 3:
		if ord(sym.data[0]) + ord(sym.data[1]) == 0 and sym.data[2:7] == "START":
			dataDic[0] = sym.data[2:]
			symSize = sym.location[3][0] - sym.location[0][0]
			
if (0 in dataDic) != True:
	print "Sorry, I couldn't read that image! Ensure the image is the right way up, or try re-scanning."
	#print dataDic.keys()
	sys.exit(1)

	
fNameLength = ord(dataDic[0][5]) #Because you dropped the first zero
fName = dataDic[0][6:6+fNameLength]
nChunks = fromChrs(dataDic[0][6+fNameLength:8+fNameLength])


dataDic[0] = dataDic[0][7+fNameLength:] # Drop the metadata

print "Ok, I'm looking for", nChunks, "chunks to restore", fName
done = False

if args.outputFile == "-1":
	outfile = fName
else:
	outfile = args.outputFile

boxSize = int(symSize * 1.75)
increment = int(symSize * 0.75)
for i in range(0,wholeIm.size[0]-boxSize,increment) + [wholeIm.size[0]-boxSize]:
	if done: break
	for j in range(0,wholeIm.size[1]-boxSize,increment) + [wholeIm.size[1]-boxSize]:
		if done: break
		box = (i,j,i+boxSize,j+boxSize)
		scanner = zbar.ImageScanner()
		scanner.parse_config('enable')
		syms = []
		sub = wholeIm.crop(box)
		width, height = sub.size
		raw = sub.tostring()
		# wrap image data
		zImage = zbar.Image(width, height, 'Y800', raw)
		# scan the image for barcodes
		result = scanner.scan(zImage)
		for sym in zImage:
			if len(sym.data) > 1:
				if (fromChrs(sym.data[:2]) in dataDic) == False and fromChrs(sym.data[:2]) < nChunks:
					dataDic[fromChrs(sym.data[:2])] = sym.data[2:]
				
		sys.stdout.write('\r' + "Got " + str(len(dataDic)) + " chunks.")
		if len(dataDic) == nChunks: done = True

print ""

if len(dataDic) < nChunks:
	print "Couldn't find them all"
	print "Got", dataDic.keys()
	sys.exit(1)
	
keys = dataDic.keys()
keys.sort()
#print keys
for i in range(nChunks):
	if keys[i] != i:
		print "Error."
		break
		
bytes = bytearray()
for k in keys:
	bytes.extend(dataDic[k])
	
bytes = base64.b64decode(str(bytes))
print "Success, ", fName, "read and stored locally as", outfile	
w = open(outfile,'wb')
w.write(bytes)
w.close()