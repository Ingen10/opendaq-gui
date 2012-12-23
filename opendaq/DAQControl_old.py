'''
Created on 01/03/2012

@author: Adrian
'''

import os
import sys
import wx
from DAQ_old import *
import threading
import time
from wx.lib.agw.floatspin import FloatSpin
from wx.lib.plot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker
import csv

#-----------------------------------------------------------------------------
# Find available serial ports.
# INPUTS:
#-Num_ports: Number of ports scanned. Default 20
#-Verbose: verbose mode True / False. If turned on will
# print everything that is happening
# Returns:
# A list with all ports found. Each list item
# is a tuple with the number of the port and the device
#-----------------------------------------------------------------------------

def scan(num_ports = 20, verbose=True):
   
    #-- List of serial devices. Empty at start
    serial_dev = []
    
    if verbose:
        print "Scan %d serial ports:" % num_ports
    
    #-- Scan num_port posible serial ports
    for i in range(num_ports):
    
        if verbose:
            sys.stdout.write("Port %d: " % i)
            sys.stdout.flush()
    
        try:
      
            #-- Open serial port
            s = serial.Serial(i)
            
            if verbose: print "OK --> %s" % s.portstr
            
            #-- If no errors, add port name to the list
            serial_dev.append( (i, s.portstr))
            
            #-- Close port
            s.close()
            
        #-- Ignore possible errors     
        except:
            if verbose: print "NO"
            pass
    #-- Return list of serial devices    
    return serial_dev


def drawLinePlot(data):
    line1 = PolyLine(data,legend='Wide Line',colour='red',width=1)
    return PlotGraphics([line1],"ADC","Time (s)","Value (V)")

class ComThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running=1
        self.runningThread=1
        self.data=[]
        self.data_packet=[]
        self.delay=0.001
    def config(self,ch1,ch2,rangeV,rate):
        ch1+=1
        if ch2==1:
            ch2=25
        elif ch2>1:
            ch2+=3
        print "configure"
        print d.adc_cfg(ch1,ch2,rangeV,20,frame.DaqError)
        self.delay=float(rate)
        self.delay/=1000
    def stop(self):
        self.running=0
        d.set_led(1,frame.DaqError)
    def stopThread(self):
        self.runningThread=0
    def restart(self):
        self.running=1
        self.data = []                   
        self.data_packet=[]
    def run(self):  
        self.running=1
        d.set_led(2,frame.DaqError)
        
        self.data = []                   
        self.data_packet=[]
        while self.runningThread:
            time.sleep(1)
            while self.running:
                time.sleep(self.delay)
                data_int = d.read_adc(frame.DaqError)
                data_int*=-frame.gains[frame.page1.editrange.GetCurrentSelection()]
                data_int/=100000
                data_int+=frame.offset[frame.page1.editrange.GetCurrentSelection()]
                data_V= float(data_int)
                data_V = data_V/1000
                frame.page1.inputValue.Clear()
                frame.page1.inputValue.AppendText(str(data_V))
                self.data_packet.append(data_V)
                self.data.append([])
                self.data[len(self.data)-1].append(float((len(self.data)-1)*self.delay))
                self.data[len(self.data)-1].append(float(data_V))
                frame.page1.canvas.Draw(drawLinePlot(self.data))

class TimerThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running=1
        self.delay=0.25
        self.counterFlag=0
        self.captureFlag=0
        self.encoderFlag=0
    def stop(self):
        self.counterFlag=0
        self.captureFlag=0
        self.encoderFlag=0
    def startCounter(self):
        self.counterFlag=1
        self.captureFlag=0
        self.encoderFlag=0
    def startCapture(self):
        self.counterFlag=0
        self.captureFlag=1
        self.encoderFlag=0
    def startEncoder(self):
        self.counterFlag=0
        self.captureFlag=0
        self.encoderFlag=1
    def stopThread(self):
        self.running=0
    def run(self):  
        self.running=1
        while self.running:
            time.sleep(self.delay)
            if self.counterFlag:
                frame.page4.counterValue.Clear()
                cnt= d.get_counter(0,frame.DaqError)
                frame.page4.counterValue.AppendText(str(cnt))
            if self.captureFlag:
                frame.page4.captureValue.Clear()
                selection = frame.page4.rb.GetSelection()
                cnt= d.get_capture(selection,frame.DaqError)
                frame.page4.captureValue.AppendText(str(cnt))
            if self.encoderFlag:
                cnt = d.get_encoder(frame.DaqError)
                frame.page4.currentPosition.Clear()
                frame.page4.currentPosition.AppendText(str(cnt))
                if frame.page4.encoderResolution !=0:
                    cnt*=100
                    cnt = cnt / frame.page4.encoderResolution
                    frame.page4.gauge.SetValue(pos=cnt)
                                
class PageOne(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
       
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        grid = wx.GridBagSizer(hgap=5, vgap=5)
        grid2 = wx.GridBagSizer(hgap=5, vgap=5)
        hSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hSizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.StaticBox(self, -1, 'Input', size=(240, 140))
        self.inputLbl = box
        self.inputSizer=wx.StaticBoxSizer(self.inputLbl, wx.HORIZONTAL)    

        
        self.sampleList = []
        self.sampleList.append("A1")
        self.sampleList.append("A2")
        self.sampleList.append("A3")
        self.sampleList.append("A4")
        self.sampleList.append("A5")
        self.sampleList.append("A6")
        self.sampleList.append("A7")
        self.sampleList.append("A8")
        self.lblch1 = wx.StaticText(self, label="Ch+")
        grid.Add(self.lblch1,pos=(0,0))
        self.editch1 = wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_DROPDOWN)
        self.editch1.SetSelection(0)
        grid.Add(self.editch1,pos=(0,1)) 
        
        self.sampleList = []
        self.sampleList.append("AGND")
        self.sampleList.append("VREF")
        self.sampleList.append("A5")
        self.sampleList.append("A6")
        self.sampleList.append("A7")
        self.sampleList.append("A8")
        self.lblch2 = wx.StaticText(self, label="Ch-")
        grid.Add(self.lblch2,pos=(1,0))
        self.editch2 = wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_DROPDOWN)
        self.editch2.SetSelection(0)
        grid.Add(self.editch2,pos=(1,1)) 
        
        self.sampleList = []
        self.sampleList.append("+-12")
        self.sampleList.append("+-4")    
        self.sampleList.append("+-2")   
        self.sampleList.append("+-0.4")
        self.sampleList.append("+-0.04")        
        self.lblrange = wx.StaticText(self, label="Range")
        grid.Add(self.lblrange,pos=(2,0))
        self.editrange = wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_DROPDOWN)
        self.editrange.SetSelection(0)
        grid.Add(self.editrange,pos=(2,1)) 
        

        self.lblrate = wx.StaticText(self, label="Rate(ms)")
        grid.Add(self.lblrate,pos=(3,0))      
        self.editrate=(wx.TextCtrl(self,style=wx.TE_CENTRE))
        self.editrate.AppendText("100")
        grid.Add(self.editrate,pos=(3,1)) 
        
        self.buttonPlay = wx.Button(self, label="Play")
        self.Bind(wx.EVT_BUTTON, self.PlayEvent,self.buttonPlay)
        self.buttonStop = wx.Button(self, label="Stop")
        self.Bind(wx.EVT_BUTTON, self.StopEvent,self.buttonStop)
        self.buttonStop.Enable(False) 
        
        grid.Add(self.buttonPlay,pos=(4,0))
        grid.Add(self.buttonStop,pos=(4,1))
        
        self.lblvalue = wx.StaticText(self, label="Last value (V)")
        grid.Add(self.lblvalue,pos=(5,0))   
        self.inputValue = wx.TextCtrl(self,style=wx.TE_READONLY)
        grid.Add(self.inputValue,pos=(5,1))
        
        self.inputSizer.Add(grid,0,wx.ALL)
        
        box = wx.StaticBox(self, -1, 'Output', size=(240, 140))
        self.outputLbl = box
        self.outputSizer=wx.StaticBoxSizer(self.outputLbl, wx.HORIZONTAL)   
        
        
        self.editvalue = FloatSpin(self,value=0,min_val=-4.0,max_val=4.0,increment=0.1,digits=3)
        self.Bind(wx.lib.agw.floatspin.EVT_FLOATSPIN,self.sliderChange,self.editvalue)
        
        grid2.Add(self.editvalue,pos=(0,0),span=(1,2))
        
        self.outputSizer.Add(grid2,0,wx.ALL)
        
        box = wx.StaticBox(self, -1, 'Export', size=(240, 140))
        self.exportLbl = box
        self.exportSizer=wx.StaticBoxSizer(self.exportLbl, wx.HORIZONTAL)   
        
        
        self.png = wx.Button(self,label="As PNG file...")
        self.Bind(wx.EVT_BUTTON,self.saveAsPNGEvent,self.png)
        self.csv= wx.Button(self,label="As CSV file...")
        self.Bind(wx.EVT_BUTTON,self.saveAsCSVEvent,self.csv)
        
        hSizer2.Add(self.png,0,wx.ALL)
        hSizer2.Add(self.csv,0,wx.ALL)
        
        self.exportSizer.Add(hSizer2,0,wx.ALL)
        
        self.canvas = PlotCanvas(self)
        self.canvas.SetInitialSize(size=(600,600))
        self.canvas.SetEnableZoom(True)
        
        
        hSizer.Add(self.inputSizer,0,wx.CENTRE)
        hSizer.Add(self.outputSizer,0,wx.EXPAND)
        hSizer.Add(self.exportSizer,0,wx.EXPAND)
        mainSizer.Add(hSizer, 0 , wx.CENTRE,border=10)
        mainSizer.Add(self.canvas,0,wx.CENTRE,border=10)
        self.SetSizerAndFit(mainSizer)
        
    def saveAsPNGEvent(self,event):
        self.dirname=''
        dlg = wx.FileDialog(self, "Choose a file",self.dirname,"", "*.png",wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            print self.filename
            print self.dirname
            self.canvas.SaveFile(self.dirname+"\\"+self.filename)
        dlg.Destroy()          
    def saveAsCSVEvent(self,event):
        self.dirname=''
        dlg = wx.FileDialog(self, "Choose a file",self.dirname,"", "*.odq",wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            print self.filename
            print self.dirname 
            with open(self.dirname+"\\"+self.filename, 'wb') as csvfile:
                spamwriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
                for i in range(len(comunicationThread.data)):
                    spamwriter.writerow([comunicationThread.data[i][0] ,comunicationThread.data[i][1]])
        dlg.Destroy()          
    def ZoomUp(self,event):
        print "Evento capturado"
    def PlayEvent(self,event):
        self.ch1 = self.editch1.GetCurrentSelection()
        self.ch2 = self.editch2.GetCurrentSelection()
        self.range = self.editrange.GetCurrentSelection()
        self.rate = self.editrate.GetValue()
        
        string= self.editrate.GetLineText(0)
        if string.isdigit():    
            self.rate = int(self.editrate.GetLineText(0))
            if self.rate<100 or self.rate>65535:
                dlg = wx.MessageDialog(self,"Time can not be neither greater than 65535 nor lower than 100","Error!", wx.OK|wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()   
                return
        else:
            dlg = wx.MessageDialog(self,"Not a valid time","Error!", wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()   
            return
        
        if self.ch1 == -1:
            frame.ShowErrorParameters()
            return
        if self.ch2 == -1:
            frame.ShowErrorParameters()
            return
        if self.range == -1:
            frame.ShowErrorParameters()
            return
        
        comunicationThread.config(self.ch1,self.ch2,self.range,self.rate)
        
        self.buttonPlay.Enable(False)
        self.buttonStop.Enable(True)
        self.editch1.Enable(False)
        self.editch2.Enable(False)
        self.editrange.Enable(False)
        self.editrate.Enable(False)
        
        if comunicationThread.is_alive():
            comunicationThread.restart()
        else:
            comunicationThread.start()
    def StopEvent(self,event):
        self.buttonPlay.Enable(True)
        self.buttonStop.Enable(False)
        self.editch1.Enable(True)
        self.editch2.Enable(True)
        self.editrange.Enable(True)
        self.editrate.Enable(True)
        
        
        comunicationThread.stop()
    def sliderChange(self,event):
        self.value = self.editvalue.GetValue()
        self.valuemv = self.value*1000
        d.set_dac(self.valuemv,frame.DaqError);

class PageThree(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)    
        indice=100
        
        self.rb=[]
        self.label=[]
        self.buttons=[]
        self.output=[]
        self.value=[]
        self.status=0
        self.values=0
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=20, vgap=20)
        hSizer  =wx.BoxSizer(wx.HORIZONTAL)
        
        imageFile = "red.jpg"
        bm = wx.Image(imageFile, wx.BITMAP_TYPE_ANY)
        bm.Rescale(40,40)
        self.imageRed=bm.ConvertToBitmap()
        imageFile = "green.jpg"
        bm = wx.Image(imageFile, wx.BITMAP_TYPE_ANY)
        bm.Rescale(40,40)
        self.imageGreen=bm.ConvertToBitmap()
        imageFile = "switchon.jpg"
        bm = wx.Image(imageFile, wx.BITMAP_TYPE_ANY)
        bm.Rescale(40,40)
        self.imageSwOn=bm.ConvertToBitmap()
        imageFile = "switchoff.jpg"
        bm = wx.Image(imageFile, wx.BITMAP_TYPE_ANY)
        bm.Rescale(40,40)
        self.imageSwOff=bm.ConvertToBitmap()
        
        for i in range(6):
            radioList=[]
            radioList.append("Input")
            radioList.append("Output")
            self.label.append(wx.StaticText(self, label="D%d" % (i+1)))
            self.rb.append(wx.RadioBox(self, label="Select input or output?",  choices=radioList, majorDimension=2,style=wx.RA_SPECIFY_COLS))
            self.buttons.append(wx.BitmapButton(self, id=indice+i,bitmap=self.imageGreen,pos=(10, 20), size = (self.imageGreen.GetWidth()+5, self.imageGreen.GetHeight()+5)))
            self.output.append(False)
            self.value.append(False)
            self.Bind(wx.EVT_BUTTON,self.OutputChange,self.buttons[i])
            self.Bind(wx.EVT_RADIOBOX,self.UpdateEvent,self.rb[i])
            grid.Add(self.label[i],pos=(i,0))
            grid.Add(self.rb[i],pos=(i,1))
            grid.Add(self.buttons[i],pos=(i,2))
        #hSizer.Add(grid,0,wx.ALL)
        #mainSizer.Add(hSizer, 0 , wx.ALL)
       
        d.setPORTDir(self.status)
       
        self.buttonUpdate = wx.Button(self, label="Update")
        self.Bind(wx.EVT_BUTTON, self.UpdateEvent,self.buttonUpdate)
       
        mainSizer.Add(grid,0,wx.ALL,border=20)
        mainSizer.Add(self.buttonUpdate,0,wx.ALL,border=20)
        self.SetSizerAndFit(mainSizer)
        
    def UpdateEvent(self,event):
        self.status=0
        for i in range(6):
            if self.rb[i].GetSelection():
                self.output[i]=True
                self.status = self.status | (1<<i) 
            else:
                self.output[i]=False
        print "Status"
        print "%X"%self.status
        d.setPORTDir(self.status)
        valueInput = d.setPORTVal(self.values)
        print "VAlues"
        print "%X"%valueInput
        for i in range(6):
            if valueInput & (1<<i):
                if self.output[i]==False:
                    self.buttons[i].SetBitmapLabel(self.imageGreen)
                else:
                    self.buttons[i].SetBitmapLabel(self.imageSwOn)
            else: 
                if self.output[i]==False:
                    self.buttons[i].SetBitmapLabel(self.imageRed)
                else:
                    self.buttons[i].SetBitmapLabel(self.imageSwOff)
        frame.page4.stopCounterEvent(self)
        frame.page4.stopPwmEvent(self)
        frame.page4.stopCaptureEvent(self)
        timerThread.stop()
    def OutputChange(self,event):
        button = event.GetEventObject()
        indice=button.GetId()-100
        if self.output[indice]:
            if self.value[indice]:
                self.value[indice]=False
                button.SetBitmapLabel(self.imageSwOff)
                self.values = self.values & ~(1<<indice)
            else:
                self.value[indice]=True
                button.SetBitmapLabel(self.imageSwOn) 
                self.values = self.values | (1<<indice)    
            print "VALUE"         
            print "%X"%self.values
        d.setPORTVal(self.values)

class PageFour(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.pwmLbl = wx.StaticBox(self, -1, 'PWM:', size=(240, 140))
        self.pwmgraphSizer = wx.StaticBoxSizer(self.pwmLbl, wx.VERTICAL)
        
        self.captureLbl = wx.StaticBox(self, -1, 'Capture:', size=(240, 140))
        self.capturegraphSizer = wx.StaticBoxSizer(self.captureLbl, wx.VERTICAL)
        
        self.counterLbl = wx.StaticBox(self, -1, 'Counter:', size=(240, 140))
        self.countergraphSizer = wx.StaticBoxSizer(self.counterLbl, wx.VERTICAL)
        
        self.encoderLbl = wx.StaticBox(self,-1,'Encoder',size=(240,140))
        self.encondergraphSizer = wx.StaticBoxSizer(self.encoderLbl,wx.VERTICAL)
        
        mainSizer = wx.BoxSizer(wx.HORIZONTAL) 
        verticalSizer = wx.BoxSizer(wx.VERTICAL)
        grid= wx.GridBagSizer(hgap=20, vgap=20)
        
        pwmSizer = wx.BoxSizer(wx.VERTICAL) 
        captureSizer = wx.BoxSizer(wx.VERTICAL) 
        counterSizer = wx.BoxSizer(wx.VERTICAL) 
        encoderSizer = wx.GridBagSizer(hgap=20, vgap=20)
         
        self.periodLabel = wx.StaticText(self, label="Period (us):")
        self.dutyLabel = wx.StaticText(self, label="Duty (%):")
        
        self.periodEdit = wx.TextCtrl(self,style=wx.TE_CENTRE)
        self.dutyEdit = wx.Slider(self, -1, 0, 0, 100, pos=(0,0),size=(100,50),style=wx.SL_HORIZONTAL |  wx.SL_LABELS)
        
        self.setPWM = wx.Button(self,label="Set PWM")
        self.Bind(wx.EVT_BUTTON,self.setPWMEvent,self.setPWM)
        self.stopPwm = wx.Button(self,label="Stop PWM")
        self.Bind(wx.EVT_BUTTON,self.stopPwmEvent,self.stopPwm)
        
        self.counterValue = wx.TextCtrl(self,style=wx.TE_READONLY)
        
        
        pwmSizer.Add(self.periodLabel,0,wx.ALL,border=5)
        pwmSizer.Add(self.periodEdit,0,wx.ALL,border=5)
        pwmSizer.Add(self.dutyLabel,0,wx.ALL,border=5)
        pwmSizer.Add(self.dutyEdit,0,wx.ALL,border=5)
        pwmSizer.Add(self.setPWM,0,wx.ALL,border=5)
        pwmSizer.Add(self.stopPwm,0,wx.ALL,border=5)
        
        
        self.setCounter = wx.Button(self,label="Start counter")
        self.Bind(wx.EVT_BUTTON,self.startCounter,self.setCounter)
        self.stopCounter = wx.Button(self,label="Stop counter")
        self.stopCounter.Enable(False)
        self.Bind(wx.EVT_BUTTON,self.stopCounterEvent,self.stopCounter)
        
        counterSizer.Add(self.setCounter,0,wx.ALL,border=5)
        counterSizer.Add(self.counterValue,0,wx.ALL,border=5)
        counterSizer.Add(self.stopCounter,0,wx.ALL,border=5)
  
        self.captureValue = wx.TextCtrl(self,style=wx.TE_READONLY)
        self.setCapture = wx.Button(self,label="Start capture")
        self.Bind(wx.EVT_BUTTON,self.startCapture,self.setCapture)
        self.stopCapture = wx.Button(self,label="Stop capture")
        self.stopCapture.Enable(False)
        self.Bind(wx.EVT_BUTTON,self.stopCaptureEvent,self.stopCapture)
        
        radioList=[]
        radioList.append("Low time")
        radioList.append("High time")
        radioList.append("Full period")
        self.rb = wx.RadioBox(self, label="Select width:",  choices=radioList, majorDimension=3,style=wx.RA_SPECIFY_COLS)
        
        captureSizer.Add(self.setCapture,0,wx.ALL,border=5)
        captureSizer.Add(self.captureValue,0,wx.ALL,border=5)
        captureSizer.Add(self.stopCapture,0,wx.ALL,border=5)  
        captureSizer.Add(self.rb,0,wx.ALL,border=5)  
        
        self.setEncoder = wx.Button(self,label='Start encoder')
        self.Bind(wx.EVT_BUTTON,self.startEncoderEvent,self.setEncoder)
        self.stopEncoder = wx.Button(self,label='Stop encoder')
        self.Bind(wx.EVT_BUTTON,self.stopEncoderEvent,self.stopEncoder)
        self.stopEncoder.Enable(False)
        self.gauge = wx.Gauge(self,range=100,size=(100,15))
        self.currentPosition = wx.TextCtrl(self,style=wx.TE_READONLY | wx.TE_CENTRE)
        self.encoderValue = wx.TextCtrl(self,style=wx.TE_CENTRE)
        radioList=[]
        radioList.append("Circular")
        radioList.append("Linear")
        self.modeEncoder = wx.RadioBox(self, label="Select mode:",  choices=radioList, majorDimension=3,style=wx.RA_SPECIFY_COLS)
        self.resolutionLabel = wx.StaticText(self, label="Resolution:")
        
        encoderSizer.Add(self.gauge,pos=(0,1))
        encoderSizer.Add(self.currentPosition,pos=(0,0)) 
        encoderSizer.Add(self.modeEncoder,pos=(1,0),span=(1,2)) 
        encoderSizer.Add(self.resolutionLabel,pos=(2,0))
        encoderSizer.Add(self.encoderValue,pos=(2,1))
        encoderSizer.Add(self.setEncoder,pos=(3,0),span=(1,2))
        encoderSizer.Add(self.stopEncoder,pos=(4,0),span=(1,2))
        
        self.pwmgraphSizer.Add(pwmSizer,0,wx.CENTRE)
        self.capturegraphSizer.Add(captureSizer,0,wx.CENTRE)
        self.countergraphSizer.Add(counterSizer,0,wx.CENTRE)
        self.encondergraphSizer.Add(encoderSizer,0,wx.CENTRE)
        
        
        grid.Add(self.pwmgraphSizer,flag=wx.EXPAND,pos=(1,1))
        grid.Add(self.capturegraphSizer,flag=wx.EXPAND,pos=(0,1))
        grid.Add(self.countergraphSizer,flag=wx.EXPAND,pos=(1,0))
        grid.Add(self.encondergraphSizer,flag=wx.EXPAND,pos=(0,0))
        
        verticalSizer.Add(grid,0,wx.ALL,border=20)
        mainSizer.Add(verticalSizer,0,wx.ALL,border=20)
        self.SetSizer(mainSizer)
    def setPWMEvent(self,event):
        self.setCapture.Enable(True)
        self.stopCapture.Enable(False)
        self.stopCounter.Enable(False)
        self.setCounter.Enable(True)

        self.counterValue.Clear()
        self.captureValue.Clear()        
        timerThread.stop()

        string=self.periodEdit.GetLineText(0)
        if string.isdigit():    
            self.period= int(string)
            self.duty = self.dutyEdit.GetValue()
            self.duty *= 1023
            self.duty /=100
            print "Duty %d"%self.duty
 
        else:
            dlg = wx.MessageDialog(self,"Not a valid value","Error!", wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()  
    def startCounter(self,event):
        d.counter_init(0)
        self.setCounter.Enable(False)
        self.setEncoder.Enable(True)
        self.setCapture.Enable(True)
        self.stopCapture.Enable(False)
        self.stopCounter.Enable(True)
        self.stopEncoder.Enable(False) 
        
        self.captureValue.Clear()
        
        timerThread.startCounter()
    def startCapture(self,event):
        d.capture_init(2000)
        self.setCapture.Enable(False)
        self.setEncoder.Enable(False)
        self.stopCapture.Enable(True)
        self.setCounter.Enable(True)
        self.stopCounter.Enable(False)
        self.stopEncoder.Enable(False) 
        
        self.counterValue.Clear()
        
        timerThread.startCapture()
    def stopCaptureEvent(self,event):
        d.capture_stop()
        self.setCounter.Enable(True)
        self.setCapture.Enable(True)
        self.setEncoder.Enable(True)
        
        self.stopCapture.Enable(False)
        self.stopCounter.Enable(False)
        self.stopEncoder.Enable(False) 
        timerThread.stop()
        
        self.counterValue.Clear()
        self.captureValue.Clear()
        
    def stopPwmEvent(self,event):
        d.capture_stop()
        self.setCounter.Enable(True)
        self.setCapture.Enable(True)
        self.setEncoder.Enable(True)
        
        self.stopCapture.Enable(False)
        self.stopCounter.Enable(False)
        self.stopEncoder.Enable(False) 
        
        d.pwm_stop(frame.DaqError)
    def stopCounterEvent(self,event):
        d.capture_stop()
        self.setCounter.Enable(True)
        self.setCapture.Enable(True)
        self.setEncoder.Enable(True)        
    
        self.stopCapture.Enable(False)
        self.stopCounter.Enable(False)
        self.stopEncoder.Enable(False) 
        timerThread.stop()
        
        self.counterValue.Clear()
        self.captureValue.Clear()
        
    def startEncoderEvent(self,event):
        if self.modeEncoder.GetSelection()==0:
            string= self.encoderValue.GetLineText(0)
            if string.isdigit():    
                self.encoderResolution = int(self.encoderValue.GetLineText(0))
                if self.encoderResolution<0 or self.encoderResolution>65535:
                    dlg = wx.MessageDialog(self,"Resolution can not be neither greater than 65535 nor lower than 1","Error!", wx.OK|wx.ICON_WARNING)
                    dlg.ShowModal()
                    dlg.Destroy()   
                    return
            else:
                dlg = wx.MessageDialog(self,"Not a valid resolution","Error!", wx.OK|wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()   
                return
        else:
            self.encoderResolution=0
        self.encoderValue.Enable(False)
        d.encoder_init(self.encoderResolution,frame.DaqError)
        self.setCounter.Enable(True)
        self.setCapture.Enable(True)
        self.setEncoder.Enable(False)
        self.stopCapture.Enable(False)
        self.stopCounter.Enable(False)
        self.stopEncoder.Enable(True)   
        
        timerThread.startEncoder()     
        
    def stopEncoderEvent(self,event):
        self.encoderValue.Enable(True)
        d.encoder_stop(frame.DaqError)
        
        self.setCounter.Enable(True)
        self.setCapture.Enable(True)
        self.setEncoder.Enable(True)
        self.stopCapture.Enable(False)
        self.stopCounter.Enable(False)
        self.stopEncoder.Enable(False)
        
        timerThread.stop()
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="DAQControl",style=wx.DEFAULT_FRAME_STYLE &~(wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX) )
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        icon =wx.Icon("./icon64.ico",wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        
        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetStatusText(d.id_config(self.DaqError))
        
        # Here we create a panel and a notebook on the panel
        self.p = wx.Panel(self)
        self.nb = wx.Notebook(self.p)
        
        # create the page windows as children of the notebook
        self.page1 = PageOne(self.nb)
        #self.page2 = PageTwo(self.nb)
        self.page3 = PageThree(self.nb)
        self.page4 = PageFour(self.nb)

        
        # add the pages to the notebook with the label to show on the tab
        self.nb.AddPage(self.page1, "Analog I/O")
        #self.nb.AddPage(self.page2, "Analog Output")
        self.nb.AddPage(self.page3, "Digital I/O")
        self.nb.AddPage(self.page4, "Timer-Counter")
        
        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.p.SetSizer(sizer)
        self.sizer = sizer

        self.data=[]
        self.page1.canvas.Draw(drawLinePlot(self.data))

        sz=self.page1.GetSize()
        sz[1]+=80
        sz[0]+=10
        self.SetSize(sz)
        
        d.enableCRC(1, self.DaqError)
        
        self.gains=[]
        self.offset=[]
        d.get_calib(self.gains,self.offset)
        
        d.set_dac(0,self.DaqError);
    
    def OnClose(self,event):
        dlg = wx.MessageDialog(self,"Do you really want to close this application?","Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            comunicationThread.stopThread()
            timerThread.stopThread()
            self.Destroy()
            d.close()
    def ShowErrorParameters(self):
        dlg = wx.MessageDialog(self,"Verify parameters","Error!", wx.OK|wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()       
    def DaqError(self,number=0,foo=0):
        errorStr = "DAQ invokes an error. Line number:"+str(number)+" in "+foo+" function." 
        dlg = wx.MessageDialog(self,errorStr,"Error!", wx.OK|wx.ICON_WARNING)
        result = dlg.ShowModal()
        dlg.Destroy()    
            
class InitThread (threading.Thread):
    def __init__(self,dial):
        threading.Thread.__init__(self)
        self.dial=dial
    def run(self):  
        for i in range(10):
            self.dial.gauge.SetValue(pos=i*10)
            time.sleep(0.2)
        self.dial.Close()


class InitDlg(wx.Dialog): 
    def __init__(self): 
        wx.Dialog.__init__(self, None, title="DAQControl",style=(wx.STAY_ON_TOP | wx.CAPTION)) 
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL) 
        self.vsizer = wx.BoxSizer(wx.VERTICAL) 
        
        self.gauge = wx.Gauge(self,range=100,size=(100,15))
        self.hsizer.Add(self.gauge,wx.EXPAND) 
        
        
        puertos_disponibles=scan(num_ports=255,verbose=False)
        self.sampleList = []
        #-- Recorrer la lista mostrando los que se han podido abrir
        if len(puertos_disponibles)!=0:
            for n,nombre in puertos_disponibles:
                self.sampleList.append(nombre)
        self.lblhear = wx.StaticText(self, label="Select Serial Port")
        self.edithear = wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_DROPDOWN)
        self.edithear.SetSelection(0)
        
        self.hsizer.Add(self.lblhear,wx.EXPAND)
        self.hsizer.Add(self.edithear,wx.EXPAND)

        self.buttonOk = wx.Button(self,label="OK")
        self.Bind(wx.EVT_BUTTON,self.okEvent,self.buttonOk)
        
        self.vsizer.Add(self.hsizer,wx.EXPAND)
        self.vsizer.Add(self.buttonOk,wx.EXPAND)

        self.gauge.Show(False)

        self.SetSizer(self.vsizer) 
        self.SetAutoLayout(1) 
        self.vsizer.Fit(self)
        
        
    def OnClose(self,event):
        if d.id_config()!=0:
            dlg = wx.MessageDialog(self,"DAQControl started","Continue", wx.OK | wx.ICON_QUESTION)
            dlg.ShowModal()
            dlg.Destroy()
            self.EndModal(1)
        else:
            dlg = wx.MessageDialog(self,"DAQControl not found","Exit", wx.OK | wx.ICON_QUESTION)
            dlg.ShowModal()
            dlg.Destroy()
            self.EndModal(0)
    def okEvent(self,event):
        portN = self.edithear.GetCurrentSelection()
        if portN>=0:
            self.buttonOk.Show(False)
            self.edithear.Show(False)
            self.gauge.Show()
            
            self.timerThread = InitThread(self)
            self.timerThread.start()
            d.setPort(self.sampleList[portN])
            d.open()
        else:
            dlg = wx.MessageDialog(self,"Not a valid port","Retry", wx.OK | wx.ICON_QUESTION)
            dlg.ShowModal()
            dlg.Destroy()
class MyApp(wx.App):
    def OnInit(self):
        dial = InitDlg()
        ret=dial.ShowModal()
        self.connected=ret
        return True



if __name__ == "__main__":
    d = DAQ("COM1")
    comunicationThread=ComThread()
    timerThread=TimerThread()
    timerThread.start()
    app = MyApp(False)
    if app.connected:
        frame=MainFrame()
        frame.Centre()
        frame.Show()
        app.MainLoop()
    else:
        comunicationThread.stopThread()
        timerThread.stopThread()
        d.close()       
