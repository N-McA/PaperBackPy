
PaperBackPy

The following python code transforms files into printable, machine readable images.
It is, more or less, a clone of paperback - see http://ollydbg.de/Paperbak/

It depends on zbar - http://zbar.sourceforge.net/
A windows installer is included. Or on debian derived linux, get it with "sudo apt-get install python-zbar"

It uses a modified version of PyQRCode, see http://pyqrcode.sourceforge.net/

It works by splitting a file into chunks. These chunks are numbered, and encoded as QR codes.
See code for more details.

Usage is as follows - 

Generate.py produces a printable image, Read.py takes that image and reproduces a file.

Use the python Generate.py -h for more help.
