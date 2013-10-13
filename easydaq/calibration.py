import os
import sys
import wx
from daq import *
import threading
import time
import numpy
from wx.lib.agw.floatspin import FloatSpin

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
   
    #-- List of serial devices. Initially empty
    serial_devices = []
    
    if verbose:
        print "Escanenado %d puertos serie:" % num_ports
    
    #-- Scan num_port possible serial ports
    for i in range(num_ports):
    
        if verbose:
            sys.stdout.write("puerto %d: " % i)
            sys.stdout.flush()
    
        try:
      
            #-- open serial port
            s = serial.Serial(i)
            
            if verbose: print "OK --> %s" % s.portstr
            
            #-- If no errors, add the number and name to the list
            serial_devices.append( (i, s.portstr))
            
            s.close()
            
        #-- Ignore possible errors      
        except:
            if verbose: print "NO"
            pass
    #-- Return list of found serial devices   
    return serial_devices


class MainFrame(wx.Frame):
    def __init__(self,commPort):
        wx.Frame.__init__(self, None, title="openDAQ")
        self.Bind(wx.EVT_CLOSE,self.OnClose)    
        self.daq = DAQ(commPort)
        self.daq.enable_crc(1)
        
        self.vHW = self.daq.get_vHW()                                
                    
        self.adcgains=[]
        self.adcoffset=[]
        self.adcgains,self.adcoffset = self.daq.get_cal()
        
        self.dacgain=0
        self.dacoffset=0
        self.dacgain,self.dacoffset = self.daq.get_dac_cal()
        
        # Here we create a panel and a notebook on the panel
        self.p = wx.Panel(self)
        self.nb = wx.Notebook(self.p)
        
        # create the page windows as children of the notebook
        self.page1 = AdcPage(self.nb,self.adcgains,self.adcoffset, self)
        self.page1.SetBackgroundColour('#ece9d8')
        self.page2 = DacPage(self.nb,self.dacgain,self.dacoffset, self)
        self.page2.SetBackgroundColour('#ece9d8')

        
        # add the pages to the notebook with the label to show on the tab
        self.nb.AddPage(self.page1, "ADC")
        self.nb.AddPage(self.page2, "DAC")
        
        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.p.SetSizer(sizer)
        
        sz=self.page1.GetSize()
        sz[1]+=80
        sz[0]+=10
        self.SetSize(sz)
        
    def OnClose(self,event):
        dlg = wx.MessageDialog(self,"Do you really want to close this application?","Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()
            frame.daq.close()
    def ShowErrorParameters(self):
            dlg = wx.MessageDialog(self,"Verify parameters","Error!", wx.OK|wx.ICON_WARNING)
            result = dlg.ShowModal()
            dlg.Destroy()       

class AdcPage(wx.Panel):
    def __init__(self, parent,gains,offset, frame):
        wx.Panel.__init__(self, parent)

        self.status=0
        self.values=0
        
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        valuesSizer = wx.GridBagSizer(hgap=8, vgap=8)
        grid = wx.GridBagSizer(hgap=4, vgap=9)
        
        
        self.gains=gains
        self.offset=offset
        
        gLabel = wx.StaticText(self, label="Slope")
        offsetLabel = wx.StaticText(self, label="Intercept")
        valuesSizer.Add(gLabel,pos=(0,1))
        valuesSizer.Add(offsetLabel,pos=(0,2))
        self.gainLabel= []
        self.gainsEdit = []
        self.offsetEdit= []
        if frame.vHW == "m":
            for i in range(5):
                self.gainLabel.append(wx.StaticText(self, label=" Gain %d" % (i+1)))
                self.gainsEdit.append(wx.TextCtrl(self,value=str(self.gains[i+1]),style=wx.TE_READONLY))
                self.offsetEdit.append(wx.TextCtrl(self,value=str(self.offset[i+1]),style=wx.TE_READONLY))
                valuesSizer.Add(self.gainLabel[i],pos=(i+1,0))
                valuesSizer.Add(self.gainsEdit[i],pos=(i+1,1))
                valuesSizer.Add(self.offsetEdit[i],pos=(i+1,2))
        if frame.vHW == "s":
            for i in range(8):     
                self.gainLabel.append(wx.StaticText(self, label="    A%d " % (i+1)))                
                self.gainsEdit.append(wx.TextCtrl(self,value=str(self.gains[i+1]),style=wx.TE_READONLY))
                self.offsetEdit.append(wx.TextCtrl(self,value=str(self.offset[i+1]),style=wx.TE_READONLY))
                valuesSizer.Add(self.gainLabel[i],pos=(i+1,0))
                valuesSizer.Add(self.gainsEdit[i],pos=(i+1,1))
                valuesSizer.Add(self.offsetEdit[i],pos=(i+1,2))        
        
        self.valueEdit=[]
        self.adcValues=[]
        self.buttons=[]
        for i in range(5):
            self.valueEdit.append(FloatSpin(self,value=0,min_val=-4.096,max_val=4.096,increment=0.001,digits=3))
            self.adcValues.append(wx.TextCtrl(self,value="--",style=wx.TE_READONLY))
            self.buttons.append(wx.Button(self,id=100+i,label="Update"))
            self.Bind(wx.EVT_BUTTON,self.updateEvent,self.buttons[i])
            grid.Add(self.valueEdit[i],pos=(i+3,0))
            grid.Add(self.adcValues[i],pos=(i+3,1))
            grid.Add(self.buttons[i],pos=(i+3,2))
            if i<2:
                self.valueEdit[i].Enable(True)
                self.adcValues[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.valueEdit[i].Enable(False)
                self.adcValues[i].Enable(False)
            
        self.nPointsList = []    
        for i in range(4):
            self.nPointsList.append("%d"%(i+2))
        self.npointsLabel = wx.StaticText(self, label="Number of points")
        self.editnpoints = wx.ComboBox(self, size=(95,-1),value="2",choices=self.nPointsList, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX,self.nPointsChange,self.editnpoints)
            
            
        self.sampleList = []
        self.sampleList2 = []
        if frame.vHW == "m":
            self.sampleList.append("+-12 V")
            self.sampleList.append("+-4 V")    
            self.sampleList.append("+-2 V")   
            self.sampleList.append("+-0.4 V")
            self.sampleList.append("+-0.04 V")        
        if frame.vHW == "s":
            self.sampleList.append("SE")
            self.sampleList.append("DE")
            for i in range(1,9):
                self.sampleList2.append("A%d" % i)
                    
            
        self.editrange = wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_READONLY)
        self.editrange.SetSelection(0)
        self.Bind(wx.EVT_COMBOBOX,self.rangeChange,self.editrange)
        grid.Add(self.editrange,pos=(1,0)) 
        
        if frame.vHW == "s":
            self.selection = wx.ComboBox(self, size=(95,-1),choices=self.sampleList2, style=wx.CB_READONLY)
            self.selection.SetSelection(0)
            grid.Add(self.selection,pos=(1,1)) 
        
        self.setDAC = wx.Button(self,label="Set DAC")        
        self.editDAC = FloatSpin(self,value=0,min_val=-4.096,max_val=4.096,increment=0.001,digits=3)
        self.Bind(wx.EVT_BUTTON,self.updateDAC,self.setDAC)
        grid.Add(self.editDAC,pos=(2,0))
        grid.Add(self.setDAC,pos=(2,1))
        
        self.update=wx.Button(self,label="Get values")
        self.Bind(wx.EVT_BUTTON,self.getValuesEvent,self.update)
        grid.Add(self.update,pos=(8,0))
        
        self.export=wx.Button(self,label="Export...")
        self.Bind(wx.EVT_BUTTON,self.exportEvent,self.export)
        grid.Add(self.export,pos=(8,1))
        
        grid.Add(self.npointsLabel,pos=(0,0))
        grid.Add(self.editnpoints,pos=(0,1))
       
        mainSizer.Add(grid,0,wx.ALL,border=10)
        mainSizer.Add(valuesSizer,0,wx.ALL,border=10)
        self.SetSizerAndFit(mainSizer)
        
    def nPointsChange(self,event):
        npoint=self.editnpoints.GetValue()         
        for i in range(5):
            if i<int(npoint):
                self.valueEdit[i].Enable(True)
                self.adcValues[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.valueEdit[i].Enable(False)
                self.adcValues[i].Enable(False)             
        
    def rangeChange(self,event):
        if self.editrange.GetValue() == "SE":
            self.selection.Clear()
            list = []
            for i in range (0,8):
                self.gainLabel[i].Label = "A%d" %(i+1)
                self.selection.Append("A%d" %(i+1))
                self.gainsEdit[i].Clear()
                self.gainsEdit[i].AppendText(str(frame.adcgains[i+1]))
                self.offsetEdit[i].Clear()
                self.offsetEdit[i].AppendText(str(frame.adcoffset[i+1]))
                                
            self.selection.SetSelection(0)

        if self.editrange.GetValue() == "DE":
            self.selection.Clear()
            self.selection.Append("A1-A2")
            self.selection.Append("A2-A1")
            self.selection.Append("A3-A4")
            self.selection.Append("A4-A3")
            self.selection.Append("A5-A6")
            self.selection.Append("A6-A5")
            self.selection.Append("A7-A8")
            self.selection.Append("A8-A7")
            self.selection.SetSelection(0)
            self.gainLabel[0].Label = "A1-A2"
            self.gainLabel[1].Label = "A2-A1"
            self.gainLabel[2].Label = "A3-A4"
            self.gainLabel[3].Label = "A4-A3"
            self.gainLabel[4].Label = "A5-A6"
            self.gainLabel[5].Label = "A6-A5"
            self.gainLabel[6].Label = "A7-A8"
            self.gainLabel[7].Label = "A8-A7"            
                
            for i in range (8):
                self.gainsEdit[i].Clear()
                self.gainsEdit[i].AppendText(str(frame.adcgains[i+9]))
                self.offsetEdit[i].Clear()
                self.offsetEdit[i].AppendText(str(frame.adcoffset[i+9]))
                
    def updateEvent(self,event):
        self.range = self.editrange.GetCurrentSelection()
        if frame.vHW == "s":
            input = self.selection.GetCurrentSelection()+1
        button = event.GetEventObject()
        index1=button.GetId()-100                
        
        if frame.vHW == "m":
            frame.daq.conf_adc(8,0,self.range,20)
            
        if frame.vHW == "s":
            if self.range == 0: #SE
                frame.daq.conf_adc(input)
            if self.range == 1: #DE
                frame.daq.conf_adc(input, 1)  

        time.sleep(0.5)
        data_int = frame.daq.read_adc()
        time.sleep(0.5)
        data_int = frame.daq.read_adc()
                    
        self.adcValues[index1].Clear()
        self.adcValues[index1].AppendText(str(data_int))
            
    def getValuesEvent(self,event):
        npoints = self.editnpoints.GetValue()
        self.range = self.editrange.GetCurrentSelection()
        if frame.vHW == "s":
            sel = self.selection.GetCurrentSelection()
        
        self.x = []
        self.y = []
        for i in range(int(npoints)):
            dacValue = self.valueEdit[i].GetValue()
            dacValueInt= int(dacValue*1000)
            adcValue = self.adcValues[i].GetLineText(0)
            adcValueInt = int(adcValue)
            self.y.append(dacValueInt)
            self.x.append(adcValueInt)
        
        r = numpy.polyfit(self.x,self.y,1)

        
        if frame.vHW == "m":
            self.slope = int(r[0]*100000)
            
        if frame.vHW == "s":
            self.slope = int(r[0]*10000)
            
        self.slope = abs (self.slope)    
               
        self.intercept = int(r[1])
        
        if frame.vHW == "m":
            self.gainsEdit[self.range].Clear()
            self.gainsEdit[self.range].AppendText(str(self.slope))

            self.offsetEdit[self.range].Clear()
            self.offsetEdit[self.range].AppendText(str(self.intercept))
            
            frame.adcgains[self.range+1] = self.slope
            frame.adcoffset[self.range+1] = self.intercept
            
        if frame.vHW == "s":
            self.gainsEdit[sel].Clear()
            self.gainsEdit[sel].AppendText(str(self.slope))

            self.offsetEdit[sel].Clear()
            self.offsetEdit[sel].AppendText(str(self.intercept))
            
            if self.range == 0:#SE                
                frame.adcgains[sel+1] = self.slope
                frame.adcoffset[sel+1] = self.intercept
            if self.range == 1:#DE
                frame.adcgains[sel+9] = self.slope
                frame.adcoffset[sel+9] = self.intercept
            
        frame.daq.set_gains_offsets(frame.adcgains, frame.adcoffset)
        self.saveCalibration()

    def updateDAC(self,event):
        
        dacValue = self.editDAC.GetValue()
        frame.daq.set_analog(dacValue)

    def saveCalibration(self):
        self.slope= []
        self.intercept = []
        self.flag = ""
        if frame.vHW == "m":            
            for i in range(5):
                value = self.gainsEdit[i].GetLineText(0)
                self.slope.append(int(value))
                value = self.offsetEdit[i].GetLineText(0)
                self.intercept.append(int(value))            
            self.flag = "M"
                
        if frame.vHW == "s":
            if self.editrange.Value == "SE":
                self.flag = "SE"
                for i in range(8):
                    value = self.gainsEdit[i].GetLineText(0)
                    self.slope.append(int(value))
                    value = self.offsetEdit[i].GetLineText(0)
                    self.intercept.append(int(value)) 
                
            if self.editrange.Value == "DE":
                self.flag = "DE"
                for i in range(8):
                    value = self.gainsEdit[i].GetLineText(0)
                    self.slope.append(int(value))
                    value = self.offsetEdit[i].GetLineText(0)
                    self.intercept.append(int(value)) 
            
        frame.daq.set_cal(self.slope,self.intercept, self.flag)
        
        frame.daq.get_cal()
        
    def exportEvent(self, event):        
        dlg = wx.TextEntryDialog(self, 'openDAQ ID:', 'ID', style=wx.OK|wx.CANCEL)
        res = dlg.ShowModal()
        id = dlg.GetValue()        
        dlg.Destroy()
                
        if res == wx.ID_CANCEL:
            return
        
        self.dirname=''
        dlg = wx.FileDialog(self, "Choose a file",self.dirname,"", "*.txt",wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            self.exportCalibration(self.dirname+"/"+self.filename, id)            
        dlg.Destroy() 
        
    def exportCalibration(self, file, id):
        outputfile = open(file,'w')        
        model = "unknown"
        if frame.vHW == "m":
            model = "M"
        if frame.vHW == "s":
            model = "S"                        
            
        output="CALIBRATION REPORT OPENDAQ-" + model + ": " + id + "\n\n"
        outputfile.write(output)
        output = "DAC CALIBRATION\n"
        outputfile.write(output)
        output = "Slope: " + str(frame.dacgain) + "    Intercept: " + str(frame.dacoffset) + "\n\n"
        outputfile.write(output)
        output = "ADC CALIBRATION\n"
        outputfile.write(output)
        
        if frame.vHW == "s":
            for i in range(1,9):
                output = "A%d:\n"%i
                outputfile.write(output)
                output = "Slope: " + str(frame.adcgains[i]) + "    Intercept: " + str(frame.adcoffset[i]) + "\n"
                outputfile.write(output)
            outputfile.write("\n")
            for i in range (9, 17):
                if i%2:
                    output = "A" + str(i-8) + "-A" + str(i-7)
                else:
                    output = "A" + str(i-8) + "-A" + str(i-9)
                
                output+=":\n"
                outputfile.write(output)
                output = "Slope: " + str(frame.adcgains[i]) + "    Intercept: " + str(frame.adcoffset[i]) + "\n"
                outputfile.write(output)
                
        if frame.vHW == "m":
            for i in range(1,6):
                output = "Gain%d:\n"%i
                outputfile.write(output)
                output = "Slope: " + str(frame.adcgains[i]) + "    Intercept: " + str(frame.adcoffset[i]) + "\n"
                outputfile.write(output)      
                
        dlg = wx.MessageDialog(self,"Report saved","Report saved", wx.OK | wx.ICON_QUESTION)
        dlg.ShowModal()
        dlg.Destroy()
        
        
class DacPage(wx.Panel):
    def __init__(self, parent,gains,offset, frame):
        wx.Panel.__init__(self, parent)
        self.status=0
        self.values=0
        
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        valuesSizer = wx.GridBagSizer(hgap=8, vgap=8)
        grid = wx.GridBagSizer(hgap=4, vgap=9)
        
        self.realDAC = numpy.zeros(5)
        self.readDAC = numpy.zeros(5)
        
        self.gain=gains
        self.offset=offset
        
        gLabel = wx.StaticText(self, label="Slope")
        offsetLabel = wx.StaticText(self, label="Intercept")
        valuesSizer.Add(gLabel,pos=(0,1))
        valuesSizer.Add(offsetLabel,pos=(0,2))
        self.gainLabel= wx.StaticText(self, label=" Gain ")
        self.gainsEdit = wx.TextCtrl(self,value=str(self.gain),style=wx.TE_READONLY)
        self.offsetEdit= wx.TextCtrl(self,value=str(self.offset),style=wx.TE_READONLY)

        self.checkDAC = wx.Button(self,label="Check DAC")
        if frame.vHW == "m":
            self.editCheck = FloatSpin(self,value=0,min_val=-4.096,max_val=4.095,increment=0.001,digits=3)
        else:
            self.editCheck = FloatSpin(self,value=0,min_val=0,max_val=4.095,increment=0.001,digits=3)
			
        self.Bind(wx.EVT_BUTTON,self.checkDacEvent,self.checkDAC)

        valuesSizer.Add(self.gainLabel,pos=(1,0))
        valuesSizer.Add(self.gainsEdit,pos=(1,1))
        valuesSizer.Add(self.offsetEdit,pos=(1,2))
        valuesSizer.Add(self.checkDAC,pos=(3,0))
        valuesSizer.Add(self.editCheck,pos=(3,1))
        
        self.valueEdit=[]
        self.adcValues=[]
        self.buttons=[]
        for i in range(5):
            self.valueEdit.append(FloatSpin(self,value=0,min_val=-4.096,max_val=4.096,increment=0.001,digits=3))
            self.buttons.append(wx.Button(self,id=100+i,label="Fix"))
            self.Bind(wx.EVT_BUTTON,self.updateEvent,self.buttons[i])
            grid.Add(self.valueEdit[i],pos=(i+3,0))
            grid.Add(self.buttons[i],pos=(i+3,1))
            if i<2:
                self.valueEdit[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.valueEdit[i].Enable(False)
            
        self.nPointsList = []    
        for i in range(4):
            self.nPointsList.append("%d"%(i+2))
        self.npointsLabel = wx.StaticText(self, label="Number of points")
        self.editnpoints = wx.ComboBox(self, size=(95,-1),value="2",choices=self.nPointsList, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX,self.nPointsChange,self.editnpoints)
            

        self.setDAC = wx.Button(self,label="Set DAC")
        self.editDAC = FloatSpin(self,value=0,min_val=-4.096,max_val=4.096,increment=0.001,digits=3)
        self.Bind(wx.EVT_BUTTON,self.updateDAC,self.setDAC)
        grid.Add(self.editDAC,pos=(1,0))
        grid.Add(self.setDAC,pos=(1,1))
        
        self.update=wx.Button(self,label="Get values")
        self.Bind(wx.EVT_BUTTON,self.getValuesEvent,self.update)
        grid.Add(self.update,pos=(8,0))
        
        self.reset=wx.Button(self,label="Reset")
        self.Bind(wx.EVT_BUTTON,self.resetEvent,self.reset)
        grid.Add(self.reset,pos=(8,1))        
        
        grid.Add(self.npointsLabel,pos=(0,0))
        grid.Add(self.editnpoints,pos=(0,1))
       
        mainSizer.Add(grid,0,wx.ALL,border=10)
        mainSizer.Add(valuesSizer,0,wx.ALL,border=10)
        self.SetSizerAndFit(mainSizer)
        
    def nPointsChange(self,event):
        npoint=self.editnpoints.GetValue()                 
        for i in range(5):
            if i<int(npoint):
                self.valueEdit[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.valueEdit[i].Enable(False)
                      
    def updateEvent(self,event):
        button = event.GetEventObject()
        index1=button.GetId()-100
        
        self.realDAC[index1] = self.editDAC.GetValue()
        self.readDAC[index1] = self.valueEdit[index1].GetValue()
            
        self.valueEdit[index1].Enable(False)
        self.buttons[index1].Enable(False)
            
    def getValuesEvent(self,event):
        npoints = self.editnpoints.GetValue()
        
        self.x = []
        self.y = []
        for i in range(int(npoints)):
            self.y.append(self.realDAC[i]*1000)
            self.x.append(self.readDAC[i]*1000)
               
        r = numpy.polyfit(self.x,self.y,1)        
        self.slope = int(r[0]*1000)
        self.slope = abs (self.slope)
        self.intercept = int(round(r[1],0))
        self.gainsEdit.Clear()
        self.gainsEdit.AppendText(str(self.slope))
        
        self.offsetEdit.Clear()
        self.offsetEdit.AppendText(str(self.intercept))

        frame.adcgains[0] = self.slope
        frame.adcoffset[0] = self.intercept
        frame.dacgain = self.slope
        frame.dacoffset = self.intercept
        frame.daq.set_DAC_gain_offset(self.slope, self.intercept)
                
        self.saveCalibration()
        
    def resetEvent(self,event):
        npoints = self.editnpoints.GetValue()
        for i in range(int(npoints)):
            self.buttons[i].Enable(True)
            self.valueEdit[i].Enable(True)
            
        self.realDAC = numpy.zeros(5)
        self.readDAC = numpy.zeros(5)

    def checkDacEvent(self,event):
        
        dacValue = self.editCheck.GetValue()
        frame.daq.set_analog(dacValue)

    def updateDAC(self,event):
        
        dacValue = self.editDAC.GetValue()
        dacValue *=1000
        dacValue +=4096
        dacValue *=2
        frame.daq.set_dac(dacValue)

    def saveCalibration(self):
        frame.daq.set_DAC_cal(self.slope,self.intercept)
        

class InitThread (threading.Thread):
    def __init__(self,dial):
        threading.Thread.__init__(self)
        self.dial=dial
    def run(self):  
        for i in range(10):
            self.dial.gauge.SetValue(pos=i*10)
            time.sleep(0.7)
        self.dial.Close()


class InitDlg(wx.Dialog): 
    def __init__(self): 
        wx.Dialog.__init__(self, None, title="openDAQ calibration",style=(wx.STAY_ON_TOP | wx.CAPTION)) 
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL) 
        self.vsizer = wx.BoxSizer(wx.VERTICAL) 
        
        self.gauge = wx.Gauge(self,range=100,size=(100,15))
        self.hsizer.Add(self.gauge,wx.EXPAND) 
        
        
        puertos_disponibles=scan(num_ports=255,verbose=False)
        self.sampleList = []
        if len(puertos_disponibles)!=0:
            for n,nombre in puertos_disponibles:
                self.sampleList.append(nombre)
        self.lblhear = wx.StaticText(self, label="Select Serial Port")
        self.edithear = wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_READONLY)
        self.edithear.SetSelection(0)
  
        self.hsizer.Add(self.lblhear,wx.EXPAND)
        self.hsizer.Add(self.edithear,wx.EXPAND)

        self.buttonOk = wx.Button(self,label="OK")
        self.Bind(wx.EVT_BUTTON,self.okEvent,self.buttonOk)
        
        self.buttonCancel = wx.Button(self,label="Cancel", pos=(115, 22))
        self.Bind(wx.EVT_BUTTON,self.cancelEvent,self.buttonCancel)
        
        self.vsizer.Add(self.hsizer,wx.EXPAND)
        self.vsizer.Add(self.buttonOk,wx.EXPAND)

        self.gauge.Show(False)

        self.SetSizer(self.vsizer) 
        self.SetAutoLayout(1) 
        self.vsizer.Fit(self)
    
    def okEvent(self,event):
        portN = self.edithear.GetCurrentSelection()
        if portN>=0:
            self.buttonOk.Show(False)
            self.edithear.Show(False)
            self.buttonCancel.Show(False)
            self.gauge.Show()
            daq = DAQ(self.sampleList[portN])
            try:
                daq.get_info()
                dlg = wx.MessageDialog(self,"openDAQ calibration started","Continue", wx.OK | wx.ICON_QUESTION)
                dlg.ShowModal()
                dlg.Destroy()
                self.port = self.sampleList[portN]
                self.EndModal(1)
            except:
                dlg = wx.MessageDialog(self,"DAQControl not found","Exit", wx.OK | wx.ICON_QUESTION)
                dlg.ShowModal()
                dlg.Destroy()
                self.port=0
                self.EndModal(0)
        else:
            dlg = wx.MessageDialog(self,"Not a valid port","Retry", wx.OK | wx.ICON_QUESTION)
            dlg.ShowModal()
            dlg.Destroy()
            
    def cancelEvent(self, event):
	self.port=0
	self.EndModal(0)        
            
class MyApp(wx.App):
    def OnInit(self):
        dial = InitDlg()
        ret=dial.ShowModal()
        dial.Destroy()
        self.commPort = dial.port
        self.connected=ret
        return True

if __name__ == "__main__":
    app = MyApp(False)
    if app.commPort != 0:        
        frame=MainFrame(app.commPort)
        frame.Centre()
        frame.Show()
        app.MainLoop()
