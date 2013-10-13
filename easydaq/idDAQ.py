'''
Mediante este programa se puede modificar el ID del openDAQ
Argumentos:
1: Puerto de comunicaciones (ej. COM3)
2: Referencia del openDAQ (ej. 153)
'''

import sys
from daq import *

puerto=sys.argv[1]
id=sys.argv[2]
daq = DAQ(puerto)
resp = daq.set_id(int(id))
print "ID updated. New ID = ", resp[2]