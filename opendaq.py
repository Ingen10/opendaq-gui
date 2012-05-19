

import serial, struct

BAUDS = 115200

def print_hex(data):
    for c in data: print "%02x" % ord(c),
    print


class CRCError(ValueError):
    pass

class LengthError(ValueError):
    pass


def crc(data):
    sum = 0
    for c in data: sum += ord(c)
    return struct.pack('>H', sum)


def check_crc(data):
    csum = data[:2]
    payload = data[2:]
    if csum != crc(payload):
        raise CRCError("CRC error")
    return payload


class DAQ:
    def __init__(self, port):
        self.port = port
        self.ser = None
        self.open()

        self.ser.setDTR(1)
        time.sleep(0.5)
        self.ser.setDTR(0)
        time.sleep(1)

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

        cmd, length, value = struct.unpack('>bbH', check_crc(ret))

        if length != 2:
            raise LengthError

        return value


    def set_led(self, color):
        cmd = struct.pack('bbbb', 18, 2, 0, color)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(4)

        if len(ret) != 4:
            raise LengthError

        cmd, length = struct.unpack('bb', check_crc(ret))

        if length != 0:
            raise LengthError



""" Test code """

if __name__ == "__main__":

    import time

    d = DAQ("/dev/ttyUSB0")
    time.sleep(8)

    t = time.time()
    for i in range(1000):
        print d.read_adc()
        #d.set_led(i%4)

    print time.time() - t


    #print_hex(load)
    #data = crc(load) + load
    #print_hex(data)
    #print_hex(check_crc(data))

