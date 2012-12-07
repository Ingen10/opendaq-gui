'''
Created on 01/03/2012

@author: Adrian
'''

import os
import sys
import wx
from DAQ import *
import threading
import fractions
import time
from wx.lib.plot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker
from wx.lib.agw.floatspin import FloatSpin
import numpy as np
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


def drawLinePlot(data1,data2,data3,data4):
    line1 = PolyLine(data1,legend='Wide Line',colour="Red",width=1)
    line2 = PolyLine(data2,legend='Wide Line',colour="Green",width=1)
    line3 = PolyLine(data3,legend='Wide Line',colour="Blue",width=1)
    line4 = PolyLine(data4,legend='Wide Line',colour="Black",width=1)
    return PlotGraphics([line1,line2,line3,line4],"ADC","Time (s)","Value")

class ComThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running=1
        self.data = [[],[],[],[]]
        self.data_packet=[]
        self.delay=1
        self.threadSleep=1
        self.ch = []
    def stop(self):
        self.streaming=0
        self.stopping=1
        self.delay=1
        self.threadSleep=1
    def stopThread(self):
        self.running=0
    def restart(self):
        self.initTime=time.time()
        self.data = [[],[],[],[]]            
        self.data_packet=[]
        d.set_dac(800,frame.DaqError)
        self.streaming=1    
        self.count=0
        d.set_led(2,frame.DaqError)
        d.stream_start(frame.DaqError)
        timeList=[]
        for i in range(4):
            timeList.append(int(frame.p.rate[i]))
        r = min(timeList)
        self.threadSleep = r/4
        for i in range(3):
            if ( frame.p.enableCheck[i+1].GetValue()):
                value = int(frame.p.rate[i+1])
                if value < self.threadSleep:
                    self.threadSleep = value
        self.threadSleep = float(self.threadSleep)/2000
        print "Time:",self.threadSleep
    def run(self):  
        self.running=1
        self.stopping=0
        self.streaming=0                
        self.data_packet=[]
        while self.running:
            time.sleep(self.threadSleep)
            if self.streaming:
                self.data_packet=[]
                self.ch = []
                ret = d.get_stream(self.data_packet,self.ch,frame.DaqError)
                if ret==0:
                    continue
                if ret==2:
                    #Write information comming from OpenDaq
                    self.debug=''.join(map(chr,self.data_packet))
                    self.data_packet=[]
                    while 1:
                        ret = d.get_stream(self.data_packet,self.ch,frame.DaqError)
                        if ret == 0:
                            print "Debug message:"+self.debug
                            break
                        if ret==2:
                            self.debug+=''.join(map(chr,self.data_packet))
                            self.data_packet=[]
                        if ret==3:
                            #experiment stopped by Odaq
                            frame.stopChannel(self.ch[0])
                        if ret == 1:
                            print "Debug message:"+self.debug
                            break
                    if ret != 1:
                        continue
                if ret==3:
                    frame.stopChannel(self.ch[0])
                self.count = self.count + 1

                self.currentTime=time.time()
                self.difTime = self.currentTime-self.initTime

                for i in range(len(self.data_packet)):
                    data_int = self.data_packet[i]
                    data_int*=-frame.gains[frame.p.range[self.ch[0]]]
                    data_int/=100000
                    data_int+=frame.offset[frame.p.range[self.ch[0]]]
                    self.delay = float(frame.p.rate[self.ch[0]])
                    self.delay/=1000
                    self.time = self.delay*len(self.data[self.ch[0]])
                    self.data[self.ch[0]].append([])
                    if frame.p.externFlag[self.ch[0]] == 1:
                        self.data[self.ch[0]][len(self.data[self.ch[0]])-1].append(self.difTime)
                    else:
                        self.data[self.ch[0]][len(self.data[self.ch[0]])-1].append(self.time)
                    self.data[self.ch[0]][len(self.data[self.ch[0]])-1].append(float(data_int))
                t=time.time()
                frame.p.canvas.Draw(drawLinePlot(self.data[0],self.data[1],self.data[2],self.data[3]))
                print "TIME:",time.time()-t
            if self.stopping:
                self.data_packet=[]
                self.ch = []
                d.stream_stop(self.data_packet,self.ch,frame.DaqError)
                print len(self.data_packet)
                for i in range(len(self.data_packet)):
                    data_int = self.data_packet[i]
                    data_int*=-frame.gains[frame.p.range[self.ch[i]]]
                    data_int/=100000
                    data_int+=frame.offset[frame.p.range[self.ch[i]]]
                    self.delay = float(frame.p.rate[self.ch[i]])
                    self.delay/=1000
                    self.time = self.delay*len(self.data[self.ch[i]])
                    self.data[self.ch[i]].append([])
                    self.data[self.ch[i]][len(self.data[self.ch[i]])-1].append(self.time)
                    self.data[self.ch[i]][len(self.data[self.ch[i]])-1].append(float(data_int))
                t=time.time()
                frame.p.canvas.Draw(drawLinePlot(self.data[0],self.data[1],self.data[2],self.data[3]))
                print "TIME:",time.time()-t
                d.set_led(1,frame.DaqError)
                for i in range(4):
                    if frame.p.enableCheck[i].GetValue():
                        print "Destroying channel %d"%(i+1)
                        d.channel_destroy(i+1,frame.DaqError)
                self.stopping=0
                frame.p.buttonPlay.Enable(True)

class StreamDialog(wx.Dialog):
    def __init__(self,parent):
        # Call wxDialog's __init__ method
        wx.Dialog.__init__ ( self, parent, -1, 'Config', size = ( 200, 200 ) )
        
        boxSizer = wx.GridBagSizer(hgap=5, vgap=5)
        mainLayout = wx.BoxSizer(wx.VERTICAL)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        burstSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.csvFlag=0
        self.burstModeFlag=0
        
        self.dataLbl=[]
        self.datagraphSizer=[]
        dataSizer=[]
        self.enable=[]
        self.periodoLabel=wx.StaticText(self,label="Period (ms)")
        self.periodoEdit=FloatSpin(self,value=frame.p.periodStreamOut,min_val=1,max_val=65535,increment=100,digits=3)
        self.offsetLabel=wx.StaticText(self,label="Offset")
        self.offsetEdit=FloatSpin(self,value=frame.p.offsetStreamOut/1000,min_val=-4.0,max_val=4.0,increment=0.1,digits=3)
        self.amplitudeLabel=wx.StaticText(self,label="Amplitude")
        self.amplitudeEdit=FloatSpin(self,value=frame.p.amplitudeStreamOut/1000,min_val=0.001,max_val=4.0,increment=0.1,digits=3)
        
        #sine
        box = wx.StaticBox(self, -1, 'Sine', size=(240, 140))
        self.dataLbl.append(box)
        self.datagraphSizer.append(wx.StaticBoxSizer(self.dataLbl[0], wx.HORIZONTAL))
        dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))

        self.datagraphSizer[0].Add(dataSizer[0],0,wx.ALL)
        
        #Square
        box = wx.StaticBox(self, -1, 'Square', size=(240, 140))
        self.dataLbl.append(box)
        self.datagraphSizer.append(wx.StaticBoxSizer(self.dataLbl[1], wx.HORIZONTAL))
        dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))
        
        self.tOnLabel=wx.StaticText(self,label="Time On")
        self.tOnEdit=FloatSpin(self,value=frame.p.tOnStreamOut,min_val=1,max_val=65535,increment=100,digits=3)

        self.datagraphSizer[1].Add(dataSizer[1],0,wx.ALL)
    
        #SawTooth
        box = wx.StaticBox(self, -1, 'Sawtooth', size=(240, 140))
        self.dataLbl.append(box)
        self.datagraphSizer.append(wx.StaticBoxSizer(self.dataLbl[2], wx.HORIZONTAL))
        dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))

        self.datagraphSizer[2].Add(dataSizer[2],0,wx.ALL)

        #sTriangle
        box = wx.StaticBox(self, -1, 'Triangle', size=(240, 140))
        self.dataLbl.append(box)
        self.datagraphSizer.append(wx.StaticBoxSizer(self.dataLbl[3], wx.HORIZONTAL))
        dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))
        
        self.tRiseLabel=wx.StaticText(self,label="Rise time")
        self.tRiseEdit=FloatSpin(self,value=frame.p.tRiseStreamOut,min_val=1,max_val=65535,increment=100,digits=3)
   
        self.datagraphSizer[3].Add(dataSizer[3],0,wx.ALL)
        
        hSizer.Add(self.periodoLabel,0,wx.ALL,border=10)
        hSizer.Add(self.periodoEdit,0,wx.ALL,border=10)
        hSizer.Add(self.offsetLabel,0,wx.ALL,border=10)
        hSizer.Add(self.offsetEdit,0,wx.ALL,border=10)
        hSizer.Add(self.amplitudeLabel,0,wx.ALL,border=10)
        hSizer.Add(self.amplitudeEdit,0,wx.ALL,border=10)
        
        for i in range(4):
            self.enable.append(wx.CheckBox(self,label='Enable',id=200+i))          
            dataSizer[i].Add(self.enable[i],0,wx.ALL,border=10)          
            self.Bind(wx.EVT_CHECKBOX,self.enableEvent,self.enable[i])

        dataSizer[1].Add(self.tOnLabel,0,wx.ALL,border=10)
        dataSizer[1].Add(self.tOnEdit,0,wx.ALL,border=10)
        dataSizer[3].Add(self.tRiseLabel,0,wx.ALL,border=10)
        dataSizer[3].Add(self.tRiseEdit,0,wx.ALL,border=10)

        boxSizer.Add(self.datagraphSizer[0],pos=(0,0))
        boxSizer.Add(self.datagraphSizer[1],pos=(0,1))
        boxSizer.Add(self.datagraphSizer[2],pos=(1,0))
        boxSizer.Add(self.datagraphSizer[3],pos=(1,1))
        
        self.csv=wx.Button(self,label="Import CSV")
        self.Bind(wx.EVT_BUTTON,self.importEvent,self.csv)
        
        self.burstMode = wx.CheckBox(self,label='Burst Mode')
        self.periodoBurstLabel=wx.StaticText(self,label="Period (us)")
        self.periodoBurstEdit=FloatSpin(self,value=frame.p.periodStreamOut*100,min_val=100,max_val=65535,increment=10,digits=0)
        burstSizer.Add(self.burstMode,0,wx.ALL)
        burstSizer.Add(self.periodoBurstLabel,0,wx.ALL)
        burstSizer.Add(self.periodoBurstEdit,0,wx.ALL)
        
        boxSizer.Add(self.csv,pos=(0,2))
        boxSizer.Add(burstSizer,pos=(1,2))
        
        self.submit=wx.Button(self,label="Submit")
        self.Bind(wx.EVT_BUTTON,self.submitEvent,self.submit)        

        mainLayout.Add(boxSizer,0,wx.ALL,border=10)
        mainLayout.Add(hSizer,0,wx.ALL,border=10)
        mainLayout.Add(self.submit,0,wx.ALL,border=10)
            
        self.SetSizerAndFit(mainLayout)
    def importEvent(self,event):
        self.dirname=''
        dlg = wx.FileDialog(self, "Choose a file",self.dirname,"", "*.odq",wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            print self.filename
            print self.dirname
             
            with open(self.dirname+"\\"+self.filename, 'rb') as csvfile:
                reader = csv.reader(csvfile)
                self.csvBuffer=[]
                for index,row in enumerate(reader):
                    for i in range(len(row)):
                        self.csvBuffer.append(int(row[i]))
        dlg.Destroy()       
        self.csvFlag=1
        for i in range(4):
            self.enable[i].SetValue(0)
            self.enable[i].Enable(False)
        self.tOnEdit.Enable(False)
        self.tRiseEdit.Enable(False)
        self.amplitudeEdit.Enable(False)
        self.offsetEdit.Enable(False)
    def submitEvent(self,event):
        self.burstModeFlag=self.burstMode.GetValue()
        #check values 
        if self.csvFlag:
            self.period = self.periodoEdit.GetValue()
            self.EndModal ( wx.ID_OK )
            return 0    
        self.signal=-1
        for i in range(4):
            if(self.enable[i].IsChecked()):
                self.signal=i

        self.amplitude = self.amplitudeEdit.GetValue()
        self.amplitude = self.amplitude*1000
        
        self.offset = self.offsetEdit.GetValue()
        self.offset = self.offset*1000
        
        self.ton = self.tOnEdit.GetValue()
        self.tRise =self.tRiseEdit.GetValue()
        if self.burstMode.GetValue():
            self.period=self.periodoBurstEdit.GetValue()/100
        else:
            self.period = self.periodoEdit.GetValue()

        if self.signal<0:
            dlg = wx.MessageDialog(self,"At least one signal should be selected","Error!", wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()   
            return 0   

        if self.amplitude+abs(self.offset)>4000:
            dlg = wx.MessageDialog(self,"Maximun value can not be greater than 4000","Error!", wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()   
            return 0       
       
        if self.ton+1>=self.period:
            dlg = wx.MessageDialog(self,"Time on can not be greater than period","Error!", wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()   
            return 0 
 
        if self.tRise+1>=self.period:
            dlg = wx.MessageDialog(self,"Time rise can not be greater than period","Error!", wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()   
            return 0 
               
        self.EndModal ( wx.ID_OK )
    def enableEvent(self,event):
        button = event.GetEventObject()
        indice=button.GetId()-200
        if(self.enable[indice].IsChecked()):
            for i in range(4):
                if i!=indice:
                    self.enable[i].SetValue(0)


class ConfigDialog ( wx.Dialog ):
    def __init__ ( self, parent, indice ):
        # Call wxDialog's __init__ method
        wx.Dialog.__init__ ( self, parent, -1, 'Config', size = ( 200, 200 ) )
        
        dataSizer = wx.GridBagSizer(hgap=5, vgap=5)
        mainLayout = wx.BoxSizer(wx.HORIZONTAL)
            
        self.sampleList = []
        self.sampleList.append("A1")
        self.sampleList.append("A2")
        self.sampleList.append("A3")
        self.sampleList.append("A4")
        self.sampleList.append("A5")
        self.sampleList.append("A6")
        self.sampleList.append("A7")
        self.sampleList.append("A8")
        self.lblch1=wx.StaticText(self, label="Ch+")
        dataSizer.Add(self.lblch1,pos=(0,0))
        self.editch1=wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_DROPDOWN)
        selection = frame.p.ch1[indice] -1
        self.editch1.SetSelection(selection)
        dataSizer.Add(self.editch1,pos=(0,1))
        
        self.sampleList = []
        self.sampleList.append("AGND")
        self.sampleList.append("VREF")
        self.sampleList.append("A5")
        self.sampleList.append("A6")
        self.sampleList.append("A7")
        self.sampleList.append("A8")
        self.lblch2=wx.StaticText(self, label="Ch-")
        dataSizer.Add(self.lblch2,pos=(1,0))
        self.editch2=wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_DROPDOWN)
        selection = frame.p.ch2[indice]
        if selection == 25:
            selection=1
        else:
            if selection !=0:
                selection -=3
        self.editch2.SetSelection(selection)
        dataSizer.Add(self.editch2,pos=(1,1))
        self.sampleList = []
        self.sampleList.append("+-12")
        self.sampleList.append("+-4")    
        self.sampleList.append("+-2")   
        self.sampleList.append("+-0.4")
        self.sampleList.append("+-0.04")        
        self.lblrange=wx.StaticText(self, label="Range")
        dataSizer.Add(self.lblrange,pos=(2,0))
        self.editrange=wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_DROPDOWN)
        self.editrange.SetSelection(frame.p.range[indice])
        dataSizer.Add(self.editrange,pos=(2,1))
        

        self.lblrate=wx.StaticText(self, label="Rate(ms)")
        dataSizer.Add(self.lblrate,pos=(0,3))    
        self.editrate=wx.TextCtrl(self,style=wx.TE_CENTRE)
        self.editrate.AppendText(str(frame.p.rate[indice]))
        dataSizer.Add(self.editrate,pos=(0,4))
        
        self.enableExtern = wx.CheckBox(self,label="Enable extern")
        self.Bind(wx.EVT_CHECKBOX,self.externModeEvent,self.enableExtern)
        self.enableExtern.SetValue(False)
        dataSizer.Add(self.enableExtern,pos=(0,5))
        
        self.lblsamples = wx.StaticText(self, label="Samples to read")
        dataSizer.Add(self.lblsamples,pos=(1,3)) 
        self.editsamples = wx.TextCtrl(self,style=wx.TE_CENTRE)
        self.editsamples.AppendText(str(frame.p.samples[indice]))
        dataSizer.Add(self.editsamples,pos=(1,4))
        
        self.sampleList = []
        self.sampleList.append("Continuous")
        self.sampleList.append("Single run: 20")    
        self.sampleList.append("Single run:40")   
        self.sampleList.append("Single run: 100")     
        self.lblmode = wx.StaticText(self, label="Mode")
        dataSizer.Add(self.lblmode,pos=(2,3))
        self.editmode = wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_DROPDOWN)
        self.editmode.SetSelection(frame.p.mode[indice])
        dataSizer.Add(self.editmode,pos=(2,4))    
        
        self.okButton = wx.Button(self,label="Confirm")
        self.Bind(wx.EVT_BUTTON,self.confirmEvent,self.okButton)       
        dataSizer.Add(self.okButton,pos=(3,0))
        
        mainLayout.Add(dataSizer,1, wx.EXPAND | wx.ALL, 20)
        
        self.SetSizerAndFit(mainLayout)
        
    def externModeEvent(self,event):
        if self.enableExtern.GetValue()==  True:
            self.editrate.Enable(False)
        else:
            self.editrate.Enable(True)
    def confirmEvent(self,event):
        string= self.editrate.GetLineText(0)
        if string.isdigit():    
            self.rate = int(self.editrate.GetLineText(0))
            if self.rate<1 or self.rate>65535:
                dlg = wx.MessageDialog(self,"Time can not be neither greater than 65535 nor lower than 1","Error!", wx.OK|wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()   
                return 0
        else:
            dlg = wx.MessageDialog(self,"Not a valid time","Error!", wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()   
            return
        string= self.editsamples.GetLineText(0)
        if string.isdigit():    
            self.samples = int(self.editsamples.GetLineText(0))
            if self.samples<1 or self.samples>255:
                dlg = wx.MessageDialog(self,"Samples can not be neither greater than 255 nor lower than 1","Error!", wx.OK|wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()   
                return 0
        else:
            dlg = wx.MessageDialog(self,"Not a valid time","Error!", wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()   
            return 0
        self.EndModal ( wx.ID_OK )

class InterfazPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.enableCheck=[]
        
        '''configuration save'''
        self.ch1=[1,1,1,1]
        self.ch2=[0,0,0,0]
        self.range=[1,1,1,1]
        self.rate=[100,100,100,100]
        self.samples=[20,20,20,20]
        self.mode=[0,0,0,0]
        self.npoint=[0,0,0,0]
        self.externFlag=[0,0,0,0]
        
        self.burstModeStreamOut=0
        self.amplitudeStreamOut=1000
        self.offsetStreamOut=1000
        self.tOnStreamOut=5
        self.tRiseStreamOut=5
        self.periodStreamOut=15
        
        self.configure=[]
        self.color=[]
    
    
        self.dataLbl=[]
        self.datagraphSizer=[]
        dataSizer=[]  
       
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        datasSizer  =wx.BoxSizer(wx.VERTICAL)
        graphSizer = wx.BoxSizer(wx.VERTICAL)
        hSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        
        for i in range(4):
            box = wx.StaticBox(self, -1, 'Experiment %d'%(i+1), size=(240, 140))
            self.dataLbl.append(box)
            self.datagraphSizer.append(wx.StaticBoxSizer(self.dataLbl[i], wx.HORIZONTAL))
            dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))
            
            self.enableCheck.append(wx.CheckBox(self,label="Enable"))
            self.enableCheck[i].SetValue(False)
            dataSizer[i].Add(self.enableCheck[i],0,wx.ALL,border=10)
                       
            self.configure.append(wx.Button(self,id=i+100,label="Configure"))
            self.Bind(wx.EVT_BUTTON,self.configureEvent,self.configure[i])
            dataSizer[i].Add(self.configure[i],0,wx.ALL,border=10)
            
            self.color.append(wx.StaticText(self,label="..........."))
            if i<3:
                color=(255*(i==0),255*(i==1),255*(i==2))
            else:
                color=(0,0,0)
            self.color[i].SetForegroundColour(color) # set text color
            self.color[i].SetBackgroundColour(color) # set text back color
            dataSizer[i].Add(self.color[i],0,wx.ALL,border=10)
            
            self.datagraphSizer[i].Add(dataSizer[i],0,wx.ALL)
            datasSizer.Add(self.datagraphSizer[i],0,wx.ALL,border=10)
            
        #stream out panel
        box = wx.StaticBox(self, -1, 'Stream out', size=(240, 140))
        self.dataLbl.append(box)
        self.datagraphSizer.append(wx.StaticBoxSizer(self.dataLbl[4], wx.HORIZONTAL))
        dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))
        
        self.enableCheck.append(wx.CheckBox(self,label="Enable"))
        self.Bind(wx.EVT_CHECKBOX,self.streamEnable,self.enableCheck[4])
        self.enableCheck[4].SetValue(False)
        dataSizer[4].Add(self.enableCheck[4],0,wx.ALL,border=10)
           
        self.configure.append(wx.Button(self,id=400,label="Configure"))
        self.Bind(wx.EVT_BUTTON,self.configureStream,self.configure[4])
        dataSizer[4].Add(self.configure[4],0,wx.ALL,border=10)
        
        self.datagraphSizer[4].Add(dataSizer[4],0,wx.ALL)
        datasSizer.Add(self.datagraphSizer[4],0,wx.ALL,border=10)
        
        #export
        box = wx.StaticBox(self, -1, 'Export', size=(240, 140))
        self.exportLbl = box
        self.exportSizer=wx.StaticBoxSizer(self.exportLbl, wx.HORIZONTAL)   
        
        
        self.png = wx.Button(self,label="As PNG file...")
        self.Bind(wx.EVT_BUTTON,self.saveAsPNGEvent,self.png)
        self.csv= wx.Button(self,label="As CSV file...")
        self.Bind(wx.EVT_BUTTON,self.saveAsCSVEvent,self.csv)
        
        hSizer2.Add(self.png,0,wx.ALL,border=10)
        hSizer2.Add(self.csv,0,wx.ALL,border=10)
        
        self.exportSizer.Add(hSizer2,0,wx.ALL)
           
        self.buttonPlay = wx.Button(self, label="Play")
        self.Bind(wx.EVT_BUTTON, self.PlayEvent,self.buttonPlay)
        self.buttonStop = wx.Button(self, label="Stop")
        self.Bind(wx.EVT_BUTTON, self.StopEvent,self.buttonStop)
        self.buttonStop.Enable(False)
        
        datasSizer.Add(self.exportSizer,0,wx.ALL,border=10)
        
        graphSizer.Add(datasSizer,0,wx.ALL)
        graphSizer.Add(self.buttonPlay,0,wx.CENTRE,border=5)
        graphSizer.Add(self.buttonStop,0,wx.CENTRE,border=5)    
        
        self.canvas = PlotCanvas(self)
        self.canvas.SetInitialSize(size=(600,600))
        self.canvas.SetEnableZoom(True)
        
        mainSizer.Add(graphSizer,0,wx.ALL)
        mainSizer.Add(self.canvas,0,wx.ALL)
        self.SetSizerAndFit(mainSizer)
        
        self.gains=[]
        self.offset=[]
        d.get_calib(self.gains,self.offset,parent.DaqError)
        
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
            for j in range(4):
                if self.enableCheck[j].IsChecked():
                    with open(self.dirname+"\\"+str(j)+self.filename, 'wb') as csvfile:
                        spamwriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
                        for i in range(len(comunicationThread.data[j])):
                            spamwriter.writerow([comunicationThread.data[j][i][0] ,comunicationThread.data[j][i][1]])
        dlg.Destroy()   
        
    def configureStream(self,event):
        
        dlg = StreamDialog(self)
        if dlg.ShowModal()==wx.ID_OK:
            self.burstModeStreamOut=dlg.burstModeFlag
            print "Burst mode",self.burstModeStreamOut
            if dlg.csvFlag:
                self.buffer=dlg.csvBuffer[:140]
                self.interval=int(dlg.period/(len(self.buffer)))
                print "CSV interval",self.interval
            else:
                self.periodStreamOut=dlg.period;
                self.amplitudeStreamOut=dlg.amplitude
                self.offsetStreamOut=dlg.offset
                self.signalStreamOut=dlg.signal
                self.tRiseStreamOut=dlg.tRise
                self.tOnStreamOut=dlg.ton
                self.signalCreate()
        dlg.Destroy()
        self.streamEnable(0)
        
    def streamEnable(self,event):
        if self.enableCheck[4].IsChecked():
            if self.burstModeStreamOut:
                for i in range(3):
                    self.enableCheck[i].SetValue(0)
                    self.enableCheck[i].Enable(False)
            self.enableCheck[3].SetValue(0)
            self.enableCheck[3].Enable(False)
        else:
            for i in range(4):
                    self.enableCheck[i].SetValue(0)
                    self.enableCheck[i].Enable(True)          
        
        
    def configureEvent(self,event):
        button = event.GetEventObject()
        indice=button.GetId()-100

        dlg = ConfigDialog(self,indice)
        if dlg.ShowModal()==wx.ID_OK:

            self.ch1[indice] = dlg.editch1.GetCurrentSelection()
            self.ch2[indice] = dlg.editch2.GetCurrentSelection()
            self.range[indice] = dlg.editrange.GetCurrentSelection()
    
            self.ch1[indice]+=1
            if self.ch2[indice]==1:
                self.ch2[indice]=25
            elif self.ch2[indice]>1:
                self.ch2[indice]+=3
            
            if dlg.enableExtern.GetValue()==  True:
                self.rate[indice] = int(dlg.editrate.GetLineText(0))
                self.externFlag[indice] = 1
            else:
                self.rate[indice] = int(dlg.editrate.GetLineText(0))
                self.externFlag[indice] = 0
            
            self.samples[indice] = int(dlg.editsamples.GetLineText(0))
            
            self.mode[indice] = dlg.editmode.GetCurrentSelection()
            if self.mode[indice] == 0:
                self.npoint[indice] = 0
                self.mode[indice] = 0
            else:
                self.npoint[indice] = 20*self.mode[indice]
                self.mode[indice] = 1
            
            dlg.Destroy()
    def PlayEvent(self,event):
        self.channel = []
        for i in range(4):
            if self.enableCheck[i].GetValue():                
                frame.channelState[i]=1
                
                self.channel.append([self.ch1[i],self.ch2[i],self.rate[i],self.range[i]])
                
                if self.externFlag[i]==1:
                    d.external_create(i+1,0,frame.DaqError)
                else:
                    d.stream_create(i+1, self.rate[i],frame.DaqError)
                d.channel_setup(i+1,self.npoint[i],self.mode[i],frame.DaqError) #mode continuous
                d.channel_cfg(i+1, 0, self.ch1[i], self.ch2[i], self.range[i],self.samples[i],frame.DaqError) #analog input
                   
        if self.enableCheck[4].GetValue():
            print "interval",self.interval
            if self.burstModeStreamOut:
                d.burst_create(self.interval*100,frame.DaqError)
                d.channel_setup(1,len(self.buffer),0,frame.DaqError) #mode continuous
                d.channel_cfg(1, 1,0,0,0,0,frame.DaqError) #analog output
            else:
                d.stream_create(4,self.interval,frame.DaqError)
                d.channel_setup(4,len(self.buffer),0,frame.DaqError) #mode continuous
                d.channel_cfg(4, 1,0,0,0,0,frame.DaqError) #analog output
            #cut signal buffer into x length buffers
            xLength=20
            nBuffers = len(self.buffer)/xLength
            for i in range(nBuffers):
                self.init=i*xLength
                self.end=self.init+xLength
                self.interBuffer=self.buffer[self.init:self.end]
                d.signal_load(self.interBuffer,self.init,frame.DaqError)
            self.init=nBuffers*xLength
            self.interBuffer=self.buffer[self.init:]
            if len(self.interBuffer)>0:
                d.signal_load(self.interBuffer,self.init,frame.DaqError)
                   
        self.buttonPlay.Enable(False)
        self.buttonStop.Enable(True)
        comunicationThread.restart()
        
    def StopEvent(self,event):
        self.buttonStop.Enable(False)
        
        comunicationThread.stop()
        
    def signalCreate(self):
        if self.signalStreamOut==0:
            #sine
            if self.periodStreamOut<140:
                self.interval = 1
            else:
                self.interval = int(self.periodStreamOut/140)
                self.interval +=1
            self.t = np.arange(0, self.periodStreamOut,self.interval)
            self.buffer= np.sin(2*np.pi/self.periodStreamOut*self.t)*self.amplitudeStreamOut
            for i in range(len(self.buffer)):
                self.buffer[i]=self.buffer[i]+self.offsetStreamOut
                

            
        if self.signalStreamOut==1:
            #square
            self.buffer = []
            self.interval= fractions.gcd(self.periodStreamOut, self.tOnStreamOut)
            self.pointsOn =int(self.tOnStreamOut / self.interval)
            self.points = int(self.periodStreamOut / self.interval)
            for i in range(self.pointsOn):
                self.buffer.append(self.amplitudeStreamOut+self.offsetStreamOut)
            for i in range(self.points-self.pointsOn):
                self.buffer.append(self.offsetStreamOut)
        if self.signalStreamOut==2:
            #sawtooth
            if self.periodStreamOut<140:
                self.interval=1
                self.points=int(self.periodStreamOut)
                self.increment = int(self.amplitudeStreamOut/self.periodStreamOut)
            else:
                self.interval = int(self.periodStreamOut/140)
                self.interval +=1
                self.points = int(self.periodStreamOut/self.interval)
                self.increment = int(self.amplitudeStreamOut/self.points)
                
            self.init=int(self.offsetStreamOut)
            self.buffer=[]
            for i in range(self.points):
                self.value=self.init
                self.value+=(self.increment*i)
                self.buffer.append(self.value)
        if self.signalStreamOut==3:
            #triangle
            if self.periodStreamOut<140:
                self.interval=1
                self.points=int(self.tRiseStreamOut)
                self.increment = int(self.amplitudeStreamOut/self.tRiseStreamOut)
            else:
                self.relation = int(self.periodStreamOut/self.tRiseStreamOut)
                self.points=int(140/self.relation)  #ideal n points
                self.interval = int(self.tRiseStreamOut/self.points)
                self.interval +=1
                self.points = int(self.tRiseStreamOut/self.interval)
                self.increment = int(self.amplitudeStreamOut/self.points)
            self.init=int(self.offsetStreamOut)
            self.buffer=[]
            for i in range(self.points):
                self.value=self.init
                self.value+=(self.increment*i)
                self.buffer.append(self.value)
            if self.periodStreamOut<140:
                self.points=int(self.periodStreamOut-self.tRiseStreamOut)
                self.increment = int(self.amplitudeStreamOut/(self.periodStreamOut-self.tRiseStreamOut))
            else:
                self.time = int(self.periodStreamOut-self.tRiseStreamOut)
                self.points=140-self.points #ideal n points
                self.interval = int(self.time/self.points)
                self.interval +=1
                self.points = int(self.time/self.interval)
                self.increment = int(self.amplitudeStreamOut/self.points) 
            self.init=int(self.offsetStreamOut+self.amplitudeStreamOut)
            for i in range(self.points):
                self.value=self.init
                self.value-=(self.increment*i)
                self.buffer.append(self.value)
        if len(self.buffer)>=140:
            self.buffer=self.buffer[:140]
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="EasyDAQ",style=wx.DEFAULT_FRAME_STYLE &~(wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        
        icon =wx.Icon("./icon64.ico",wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        
        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetStatusText(d.id_config(self.DaqError))
        
        self.channelState=[0,0,0,0]
        
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        self.errorDic={'size':0}
        self.errorInfo={'Failure data size':0}

        # Here we create a panel
        self.p = InterfazPanel(self)
        
        sz=self.p.GetSize()
        sz[1]+=50
        sz[0]+=10
        self.SetSize(sz)
        
        self.p.canvas.Draw(drawLinePlot([],[],[],[]))
        
        d.enableCRC(1, self.DaqError)
    
        
        self.gains=[]
        self.offset=[]
        d.get_calib(self.gains,self.offset,self.DaqError)
    def OnClose(self,event):
        dlg = wx.MessageDialog(self,"Do you really want to close this application?","Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            comunicationThread.stopThread()
            self.Destroy()
            d.close()
    def ShowErrorParameters(self):
        dlg = wx.MessageDialog(self,"Verify parameters","Error!", wx.OK|wx.ICON_WARNING)
        result = dlg.ShowModal()
        dlg.Destroy() 
    def DaqError(self,number=0,foo=0):
        errorStr = "DAQ invokes an error. Line number:"+str(number)+" in "+foo+" function." 
        dlg = wx.MessageDialog(self,errorStr,"Error!", wx.OK|wx.ICON_WARNING)
        result = dlg.ShowModal()
        dlg.Destroy()   
    def stopChannel(self,number):
        print "Stopping ch",number
        self.channelState[number]=0
        
        suma=0
        for i in range(3):
            suma=suma+self.channelState[i]
        if suma==0:
            self.p.buttonPlay.Enable(True)
            self.p.buttonStop.Enable(False)
            comunicationThread.stop()
            
class InitThread (threading.Thread):
    def __init__(self,dial):
        threading.Thread.__init__(self)
        self.dial=dial
    def run(self):  
        for i in range(10):
            self.dial.gauge.SetValue(pos=i*10)
            time.sleep(0.1)
        self.dial.Close()


class InitDlg(wx.Dialog): 
    def __init__(self): 
        wx.Dialog.__init__(self, None, title="EasyDAQ",style=(wx.STAY_ON_TOP | wx.CAPTION)) 
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
        dlg = wx.MessageDialog(self,"EasyDAQ started","Continue", wx.OK | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        self.Destroy()
    def okEvent(self,event):
        self.buttonOk.Show(False)
        self.edithear.Show(False)
        self.gauge.Show()
        
        self.timerThread = InitThread(self)
        self.timerThread.start()
        portN = self.edithear.GetCurrentSelection()
        d.setPort(self.sampleList[portN])
        d.open()
class MyApp(wx.App):
    def OnInit(self):
        dial = InitDlg()
        dial.ShowModal()
        return True



if __name__ == "__main__":
    d = DAQ("COM1")
    comunicationThread=ComThread()
    comunicationThread.start()
    app = MyApp(False)
    frame=MainFrame()
    frame.Centre()
    frame.Show()
    app.MainLoop()
