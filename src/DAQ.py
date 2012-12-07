'''
Created on 18/10/2012

@author: Adrian
'''


import serial, struct
import inspect
import time

BAUDS = 115200


def print_hex(data):
    for c in data: print "%02x" % ord(c),
    print


def crc(data):
    suma = 0
    for c in data: suma += ord(c)
    return struct.pack('>H', suma)

def check_stream_crc(head,data):
    csum=(head[0]<<8)+head[1]
    suma = 0
    intData = head[2:]
    intData+=data
    l = len(intData)
    for i in range(l): 
        suma += intData[i]
    if csum != suma:
        return 0
    return 1

def check_crc(data):
    csum = data[:2]
    payload = data[2:]
    if csum != crc(payload):
        pass #raise CRCError("CRC error")
    return payload


class DAQ:
    def __init__(self, port):
        self.port = port
        self.ser = None
        self.errorDic={'size':0}
    def setPort(self,port):
        self.port = port

    def open(self):
        self.ser = serial.Serial(self.port, BAUDS, timeout=1)
        self.ser.setRTS(0)

    def close(self):
        self.ser.close()

    def id_config(self,callback=0):
        cmd = struct.pack('bb', 39, 0)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(10)

        if len(ret) != 10:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

        cmd, length, fv,hv,serial = struct.unpack('>bbbbI', check_crc(ret))

        if length != 6:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno)
        strOut="FV:"+str(fv)+" HV:"+str(hv)
        print strOut    
                
        return strOut

    def read_adc(self,callback=0):
        cmd = struct.pack('bb', 1, 0)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(6)

        if len(ret) != 6:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

        cmd, length, value = struct.unpack('>bbh', check_crc(ret))

        if length != 2:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno)
        
        print value

        return value

    def adc_cfg(self, pchan, nchan, gain, nsam,callback=0):
        cmd = struct.pack('bbbbbb', 2, 4, pchan, nchan, gain, nsam)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(10)
        cmd, length, value, d1, d2 = struct.unpack('>bbhhh', check_crc(ret))

        if len(ret) != 10:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

        check_crc(ret)

        return value
    
    def enableCRC(self,on,callback=0):
        cmd = struct.pack('bbb', 55, 1, on)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(5)

        if len(ret) != 5:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

        #print_hex(check_crc(ret))

        cmd, length, value = struct.unpack('bbb', check_crc(ret))
        if length != 1:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])      

    def set_led(self, color,callback=0):
        cmd = struct.pack('bbb', 18, 1, color)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(5)

        if len(ret) != 5:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

        #print_hex(check_crc(ret))

        cmd, length, value = struct.unpack('bbb', check_crc(ret))
        if length != 1:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

    def set_dac(self, value,callback=0):
        cmd = struct.pack('>bbh', 13, 2, value)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(6)

        if len(ret) != 6:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

        cmd, length, value = struct.unpack('bbh', check_crc(ret))
        if length != 2:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
        
    def setPORTDir(self,output,callback=0):
        cmd = struct.pack('bbb', 9,1, output)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(5)

        if len(ret) != 5:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

        #print_hex(check_crc(ret))

        cmd, length,output = struct.unpack('bbb', check_crc(ret))
        if length != 1:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])       
    def setPORTVal(self,value,callback=0):
        cmd = struct.pack('bbb', 7,1, value)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(5)

        if len(ret) != 5:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

        #print_hex(check_crc(ret))

        cmd, length, value = struct.unpack('bbb', check_crc(ret))
        if length != 1:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])   
        
        return value

    def setPIODir(self,number,output,callback=0):
        cmd = struct.pack('bbbb', 5,2, number, output)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(6)

        if len(ret) != 6:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

        #print_hex(check_crc(ret))

        cmd, length, number, output = struct.unpack('bbbb', check_crc(ret))
        if length != 2:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])      
    def setPIOVal(self,number,value,callback=0):
        cmd = struct.pack('bbbb', 3,2, number, value)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(6)

        if len(ret) != 6:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

        #print_hex(check_crc(ret))

        cmd, length, number, value = struct.unpack('bbbb', check_crc(ret))
        if length != 2:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])    
        return value
    def counter_init(self,edge,callback=0):
        cmd = struct.pack('>bbb',41,1,1)
        self.ser.write(crc(cmd)+cmd)
        
        ret  = self.ser.read(5)
        if len(ret) != 5:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
        
        cmd,length,edge = struct.unpack('>bbb',check_crc(ret))
        if length != 1:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
    def get_counter(self,reset,callback=0):
        cmd = struct.pack('>bbb',42,1,reset)
        self.ser.write(crc(cmd)+cmd)
        
        ret = self.ser.read(6)
        if len(ret) != 6:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
        
        cmd,length,count = struct.unpack('>bbH',check_crc(ret))
        if length != 2:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
        return count
    def capture_init(self,period,callback=0):
        cmd = struct.pack('>bbH',14,2,period)
        self.ser.write(crc(cmd)+cmd)
        
        ret = self.ser.read(6)
        if len(ret) != 6:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
        
        cmd,length,period = struct.unpack('>bbH',check_crc(ret))
        if length != 2:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
    def capture_stop(self,callback=0):
        cmd = struct.pack('>bb',15,0)
        self.ser.write(crc(cmd) + cmd)
        
        ret = self.ser.read(4)
        
        if len(ret) != 4:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
        
        cmd,length = struct.unpack('>bb',check_crc(ret))
        if length != 0:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
    def get_capture(self,mode,callback=0):
        cmd = struct.pack('>bbb',16,1,mode)
        self.ser.write(crc(cmd)+cmd)
        
        ret = self.ser.read(7)
        if len(ret) != 7:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
        
        cmd,length,mode,count = struct.unpack('>bbbH',check_crc(ret))
        if length != 3:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
        return count
    
    def encoder_init(self,resolution,callback=0):
        print "Encoder init"
        print resolution
        cmd = struct.pack('>bbB',50,1,resolution)
        self.ser.write(crc(cmd)+cmd)
        
        ret = self.ser.read(5)
        if len(ret) != 5:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
        
        cmd,length,res = struct.unpack('>bbb',check_crc(ret))
        if length != 1:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
    def encoder_stop(self,callback=0):
        cmd = struct.pack('>bb',51,0)
        self.ser.write(crc(cmd) + cmd)
        
        ret = self.ser.read(4)
        
        if len(ret) != 4:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
        
        cmd,length = struct.unpack('>bb',check_crc(ret))
        if length != 0:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
    def get_encoder(self,callback=0):
        cmd = struct.pack('>bb',52,0)
        self.ser.write(crc(cmd)+cmd)
        
        ret = self.ser.read(6)
        if len(ret) != 6:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
                return 0
                    
        cmd,length,count = struct.unpack('>bbH',check_crc(ret))
        if length != 2:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
        return count
    
    def pwm_init(self, duty, period,callback=0):
        cmd = struct.pack('>bbHH', 10, 4, duty, period)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(8)

        if len(ret) != 8:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

        cmd, length, myduty, myperiod = struct.unpack('bbHH', check_crc(ret))
        if length != 4:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
     
    def pwm_stop(self,callback=0):
        cmd = struct.pack('>bb',11,0)
        self.ser.write(crc(cmd)+cmd)
        
        ret = self.ser.read(4)
        
        if len(ret) != 4:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
                
        cmd,length = struct.unpack('bb',check_crc(ret))
        if length != 0:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])                   
        
    def get_calib(self,gains,offset,callback=0):
        for i in range(5):
            cmd = struct.pack('>bbb',36,1,i)
            self.ser.write(crc(cmd)+cmd)
            ret = self.ser.read(9)
            if len(ret) !=9:
                if callback!=0:
                    callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
            print 'calibration %d'%i, len(ret)
            cmd,length,channel,gain,oSet = struct.unpack('>bbbHh',check_crc(ret))
            if length !=5:
                if callback!=0:
                    callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
            gains.append(gain)
            offset.append(oSet)
            print gains,offset
            
    def set_calib(self,gains,offset,callback=0):
        for i in range(5):
            cmd = struct.pack('>bbbHh',37,5,i,gains[i],offset[i])
            self.ser.write(crc(cmd)+cmd)
            ret = self.ser.read(9)
            if len(ret) !=9:
                if callback!=0:
                    callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
            print 'calibration %d'%i, len(ret)
            cmd,length,channel,gain,oSet = struct.unpack('>bbbHh',check_crc(ret))
            if length !=5:
                if callback!=0:
                    callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
    
    def channel_cfg(self, number, mode, pchan, nchan, gain,samples,callback=0):
        cmd = struct.pack('>bbbbbbbb', 22, 6, number, mode, pchan, nchan, gain,samples)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(10)

        check_crc(ret);
    def channel_setup(self,number,numberPoints,mode,callback=0):
        print "Number of samples",numberPoints
        cmd = struct.pack('>bbbHb',32,4,number,numberPoints,mode)
        self.ser.write(crc(cmd)+cmd)
        
        ret = self.ser.read(8)
        if len(ret) != 8:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
                
        check_crc(ret)

    def channel_destroy(self,channel,callback=0):
        cmd = struct.pack('>bbb',57,1,channel)
        self.ser.write(crc(cmd)+cmd)
        
        ret = self.ser.read(5)
        if len(ret) != 5:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
                
        check_crc(ret)
        
    def stream_create(self, number, period,callback=0):
        cmd = struct.pack('>bbbH', 19, 3, number, period)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(7)
        if len(ret) != 7:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
            
        check_crc(ret)
        
    def burst_create(self,period,callback=0):
        cmd = struct.pack('>bbH', 21, 2, period)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(6)
        if len(ret) != 6:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
            
        check_crc(ret)

    def external_create(self,number,edge,callback=0):
        cmd = struct.pack('>bbbb', 20, 2, number, edge)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(6)
        if len(ret) != 6:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])
                
        check_crc(ret)

    def stream_start(self,callback=0):
        cmd = struct.pack('bb', 64, 0)
        self.ser.write(crc(cmd) + cmd)

        ret = self.ser.read(4)
        if len(ret) != 4:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])   
                
        check_crc(ret)

    def stream_stop(self,data,channel,callback=0):
        cmd = struct.pack('bb',80,0)
        self.ser.write(crc(cmd)+cmd)
        
        #receive all stream data in the in buffer
        while 1:
            ret = self.ser.read(1)
            if len(ret)==0:
                break
            else:
                cmd = struct.unpack('>b',ret)
                if cmd[0] == 0x7E:
                    self.header = []
                    self.data = []
                    while len(self.header)<8:
                        ret = self.ser.read(1)
                        char = struct.unpack('>B',ret)
                        if char[0] == 0x7D:
                            ret = self.ser.read(1)
                        self.header.append(char[0])
                    length=self.header[3]
                    self.dataLength=length-4
                    while len(self.data)<self.dataLength:
                        ret = self.ser.read(1)
                        char = struct.unpack('>B',ret)
                        if char[0] == 0x7D:
                            ret = self.ser.read(1)
                            char = struct.unpack('>B',ret)
                            tmp = char[0] | 0x20
                            self.data.append(tmp)
                        else:
                            self.data.append(char[0])
                    if check_stream_crc(self.header,self.data)!=1:
                        print "checksum invalid"
                        continue
                    for i in range(0, self.dataLength, 2):
                        value = (self.data[i]<<8) | self.data[i+1]
                        if value >=32768:
                            value=value-65536
                        data.append(int(value))
                        channel.append(self.header[4]-1)
                else:
                    break
        
        ret = self.ser.read(3)
        ret = str(cmd[0])+ret
        if len(ret) !=4:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])

    #This function get stream from serial.
    #Returns 0 if there aren't any incoming data
    #Returns 1 if data stream was precessed
    #Returns 2 if no data stream received. Useful for debuging
    def get_stream(self,data,channel,callback=0):
        self.header = []
        self.data = []
        ret = self.ser.read(1)
        if len(ret)==0:
            return 0
        head = struct.unpack('>b',ret)
        if head[0] != 0x7E:
            data.append(head[0])
            return 2
        #get header

        while len(self.header)<8:
            ret = self.ser.read(1)
            char = struct.unpack('>B',ret)
            if char[0] == 0x7D:
                ret = self.ser.read(1)
                char = struct.unpack('>B',ret)
                tmp = char[0] | 0x20
                self.header.append(tmp)
            else:
                self.header.append(char[0])
                
            if len(self.header)==3 and self.header[2] == 80:
                #ODaq send stop
                ret = self.ser.read(2)
                char,ch = struct.unpack('>BB',ret)
                channel.append(ch-1)
                return 3
        length=self.header[3]
        self.dataLength=length-4
        while len(self.data)<self.dataLength:
            ret = self.ser.read(1)
            char = struct.unpack('>B',ret)
            if char[0] == 0x7D:
                ret = self.ser.read(1)
                char = struct.unpack('>B',ret)
                tmp = char[0] | 0x20
                self.data.append(tmp)
            else:
                self.data.append(char[0])
        
        for i in range(0, self.dataLength, 2):
            value = (self.data[i]<<8) | self.data[i+1]
            if value >=32768:
                value=value-65536
            data.append(int(value))
        check_stream_crc(self.header,self.data)
        channel.append(self.header[4]-1)
        return 1
    def signal_load(self,data,offset,callback=0):
        l=len(data)
        cmd = struct.pack('>bBh', 23, l*2+2,offset)
        for i in range(l):
            cmd+=struct.pack('>h',data[i])
        self.ser.write(crc(cmd) + cmd)
        
        ret = self.ser.read(7)
        if len(ret) != 7:
            if callback!=0:
                callback(inspect.currentframe().f_back.f_lineno,inspect.stack()[0][3])   
  
        check_crc(ret)
