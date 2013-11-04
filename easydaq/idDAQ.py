'''
This program allows to modify the openDAQ ID
Arguments:
1: Communications port (ex. COM3)
2: openDAQ ID (ex. 153)
'''

import sys

from daq import DAQ

puerto = sys.argv[1]
id = sys.argv[2]
daq = DAQ(puerto)
resp = daq.set_id(int(id))
print "ID updated. New ID = ", resp[2]
