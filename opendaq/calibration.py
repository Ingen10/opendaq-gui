import os
import sys
import wx
from DAQ import *
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
    dispositivos_serie = []
    
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
            dispositivos_serie.append( (i, s.portstr))
            
            s.close()
            
        #-- Ignore possible errors      
        except:
            if verbose: print "NO"
            pass
    #-- Return list of found serial devices   
    return dispositivos_serie


class MainFrame(wx.Frame):
    def __init__(self,commPort):
        wx.Frame.__init__(self, None, title="OpenDaq")
        self.Bind(wx.EVT_CLOSE,self.OnClose)

        self.daq = DAQ(commPort)
        self.daq.enable_crc(1)
    
        self.gains=[]
        self.offset=[]
        self.gains,self.offset = self.daq.get_cal()
        
        # Here we create a panel
        self.p = InterfazPanel(self,self.gains,self.offset)
        
        sz=self.p.GetSize()
        sz[1]+=50
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

class InterfazPanel(wx.Panel):
    def __init__(self, parent,gains,offset):
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
        for i in range(5):
            self.gainLabel.append(wx.StaticText(self, label=" Gain %d" % (i+1)))
            self.gainsEdit.append(wx.TextCtrl(self,value=str(self.gains[i]),style=wx.TE_READONLY))
            self.offsetEdit.append(wx.TextCtrl(self,value=str(self.offset[i]),style=wx.TE_READONLY))
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
        self.editnpoints = wx.ComboBox(self, size=(95,-1),value="2",choices=self.nPointsList, style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX,self.nPointsChange,self.editnpoints)
            
            
        self.sampleList = []
        self.sampleList.append("+-12")
        self.sampleList.append("+-4")    
        self.sampleList.append("+-2")   
        self.sampleList.append("+-0.4")
        self.sampleList.append("+-0.04")        
        self.lblrange = wx.StaticText(self, label="Range")
        grid.Add(self.lblrange,pos=(1,0))
        self.editrange = wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_DROPDOWN)
        self.editrange.SetSelection(1)
        grid.Add(self.editrange,pos=(1,1)) 
        
        self.setDAC = wx.Button(self,label="Set DAC")
        self.editDAC = FloatSpin(self,value=0,min_val=-4.096,max_val=4.096,increment=0.001,digits=3)
        self.Bind(wx.EVT_BUTTON,self.updateDAC,self.setDAC)
        grid.Add(self.editDAC,pos=(2,0))
        grid.Add(self.setDAC,pos=(2,1))
        
        self.update=wx.Button(self,label="Get values")
        self.Bind(wx.EVT_BUTTON,self.getValuesEvent,self.update)
        grid.Add(self.update,pos=(8,0))
        
        grid.Add(self.npointsLabel,pos=(0,0))
        grid.Add(self.editnpoints,pos=(0,1))
       
        mainSizer.Add(grid,0,wx.ALL,border=10)
        mainSizer.Add(valuesSizer,0,wx.ALL,border=10)
        self.SetSizerAndFit(mainSizer)
        
    def nPointsChange(self,event):
        npoint=self.editnpoints.GetValue()         
        print npoint
        for i in range(5):
            if i<int(npoint):
                self.valueEdit[i].Enable(True)
                self.adcValues[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.valueEdit[i].Enable(False)
                self.adcValues[i].Enable(False)           
    def updateEvent(self,event):
        self.range = self.editrange.GetCurrentSelection()
        button = event.GetEventObject()
        indice=button.GetId()-100
            
        frame.daq.conf_adc(8,0,self.range,20)
        time.sleep(1)
        data_int = frame.daq.read_adc()
        self.adcValues[indice].Clear()
        self.adcValues[indice].AppendText(str(data_int))
            
    def getValuesEvent(self,event):
        npoints = self.editnpoints.GetValue()
        self.range = self.editrange.GetCurrentSelection()
        
        self.x = []
        self.y = []
        for i in range(int(npoints)):
            dacValue = self.valueEdit[i].GetValue()
            dacValueInt= int(dacValue*1000)
            adcValue = self.adcValues[i].GetLineText(0)
            adcValueInt = int(adcValue)
            self.y.append(dacValueInt)
            self.x.append(adcValueInt)
        
        print self.x
        print self.y
        r = numpy.polyfit(self.x,self.y,1)
        print r
        self.slope = int(r[0]*100000)
        self.slope = abs (self.slope)
        self.intercept = int(r[1])
        self.gainsEdit[self.range].Clear()
        self.gainsEdit[self.range].AppendText(str(self.slope))
        
        self.offsetEdit[self.range].Clear()
        self.offsetEdit[self.range].AppendText(str(self.intercept))
        
        self.saveCalibration()

    def updateDAC(self,event):
        
        dacValue = self.editDAC.GetValue()
        frame.daq.set_dac(dacValue)

    def saveCalibration(self):
        self.slope= []
        self.intercept = []
        for i in range(5):
            value = self.gainsEdit[i].GetLineText(0)
            self.slope.append(int(value))
            value = self.offsetEdit[i].GetLineText(0)
            self.intercept.append(int(value))
        print self.slope
        print self.intercept
        frame.daq.set_cal(self.slope,self.intercept)
        
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
        wx.Dialog.__init__(self, None, title="EasyDAQ",style=(wx.STAY_ON_TOP | wx.CAPTION)) 
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
    
    def okEvent(self,event):
        portN = self.edithear.GetCurrentSelection()
        if portN>=0:
            self.buttonOk.Show(False)
            self.edithear.Show(False)
            self.gauge.Show()
            daq = DAQ(self.sampleList[portN])
            try:
                daq.get_info()
                dlg = wx.MessageDialog(self,"DAQControl started","Continue", wx.OK | wx.ICON_QUESTION)
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
    frame=MainFrame(app.commPort)
    frame.Centre()
    frame.Show()
    app.MainLoop()
