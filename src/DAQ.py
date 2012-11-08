'''
Created on 18/10/2012

@author: Adrian
'''


import serial, struct

BAUDS = 115200

def print_hex(data):
    for c in data: print "%02x" % ord(c),
    print




def crc(data):
    sum = 0
    for c in data: sum += ord(c)
    return struct.pack('>H', sum)


def check_crc(data):
    csum = data[:2]
    payload = data[2:]
    #if csum != crc(payload):
    #    raise CRCError("CRC error")
    return payload


class DAQ:
    def __init__(self, port):
        self.port = port
        self.ser = None
        
    def setPort(self,port):
        self.port = port

    def open(self):
        self.ser = serial.Serial(self.port, BAUDS, timeout=0.1)
        self.ser.setRTS(0)

    def close(self):
        self.ser.close()

    def read_adc(self):
        cmd = struct.pack('bb', 1, 0)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(6)

        if len(ret) != 6:
            raise LengthError

        cmd, length, value = struct.unpack('>bbh', check_crc(ret))

        if length != 2:
            raise LengthError

        return value

    def adc_cfg(self, pchan, nchan, gain, nsam):
        cmd = struct.pack('bbbbbb', 2, 4, pchan, nchan, gain, nsam)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(10)
        cmd, length, value, d1, d2 = struct.unpack('>bbhhh', check_crc(ret))

        if len(ret) != 10:
            raise LengthError

        return value

    def set_led(self, color):
        cmd = struct.pack('bbb', 18, 1, color)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(5)

        if len(ret) != 5:
            raise LengthError

        #print_hex(check_crc(ret))

        cmd, length, value = struct.unpack('bbb', check_crc(ret))
        if length != 1:
            raise LengthError

    def set_dac(self, value):
        cmd = struct.pack('>bbh', 13, 2, value)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(6)

        if len(ret) != 6:
            raise LengthError

        cmd, length, value = struct.unpack('bbh', check_crc(ret))
        if length != 2:
            raise LengthError
        
    def setPORTDir(self,output):
        cmd = struct.pack('bbb', 9,1, output)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(5)

        if len(ret) != 5:
            raise LengthError

        #print_hex(check_crc(ret))

        cmd, length,output = struct.unpack('bbb', check_crc(ret))
        if length != 1:
            raise LengthError       
    def setPORTVal(self,value):
        cmd = struct.pack('bbb', 7,1, value)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(5)

        if len(ret) != 5:
            raise LengthError

        #print_hex(check_crc(ret))

        cmd, length, value = struct.unpack('bbb', check_crc(ret))
        if length != 1:
            raise LengthError       
        
        return value

    def setPIODir(self,number,output):
        cmd = struct.pack('bbbb', 5,2, number, output)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(6)

        if len(ret) != 6:
            raise LengthError

        #print_hex(check_crc(ret))

        cmd, length, number, output = struct.unpack('bbbb', check_crc(ret))
        if length != 2:
            raise LengthError       
    def setPIOVal(self,number,value):
        cmd = struct.pack('bbbb', 3,2, number, value)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(6)

        if len(ret) != 6:
            raise LengthError

        #print_hex(check_crc(ret))

        cmd, length, number, value = struct.unpack('bbbb', check_crc(ret))
        if length != 2:
            raise LengthError       
        return value
    def pwm_init(self, duty, period):
        cmd = struct.pack('>bbHH', 10, 4, duty, period)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(8)

        if len(ret) != 8:
            raise LengthError

        cmd, length, myduty, myperiod = struct.unpack('bbHH', check_crc(ret))
        if length != 4:
            raise LengthError

    def channel_cfg(self, number, mode, pchan, nchan, gain):
        cmd = struct.pack('>bbbbbbbb', 22, 6, number, mode, pchan, nchan, gain,0)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(10)
        print 'cfg: ', len(ret)
        print struct.unpack('>bbbbbbbbbb', ret)

    
    def stream_create(self, number, period):
        cmd = struct.pack('>bbbHb', 19, 4, number, period, 0)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(8)
        print 'create: ', len(ret)
        print struct.unpack('>bbbbb', ret)

    def get_stream(self):
        cmd = struct.pack('bb', 64, 0)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(4)
        if len(ret) != 4:
            raise LengthError

        count = 0
        while (count < 9):
            print count,': '
            count = count + 1
            ret = self.ser.read(8)
            print struct.unpack('>bbbbbbbb', ret)
            cmd, length, num, pch,nch,gain = struct.unpack('>bbBBBB', check_crc(ret))
            print '( cmd= ',cmd, ', length= ',length, ', num= ',num, ', pch= ',pch, ', nch= ',nch, ',gain= ',gain,' )'
            for i in range(6, length, 2):
                ret = self.ser.read(2)
                value = struct.unpack('>h', ret)
                print 'val= ',value

        print 'FIN DE LA TRAMA'

        #end of frame
        cmd = struct.pack('bb', 80, 0)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(4)
        if len(ret) != 4:
            raise LengthError