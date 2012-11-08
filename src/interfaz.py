'''
Created on 01/03/2012

@author: Adrian
'''

import os
import sys
import wx
from DAQ import *
import threading
import time
from wx.lib.plot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker


#-----------------------------------------------------------------------------
# Buscar puertos series disposibles. 
# ENTRADAS:
#   -num_ports : Numero de puertos a escanear. Por defecto 20
#   -verbose   : Modo verboso True/False. Si esta activado se va 
#                imprimiendo todo lo que va ocurriendo
# DEVUELVE: 
#    Una lista con todos los puertos encontrados. Cada elemento de la lista
#    es una tupla con el numero del puerto y el del dispositivo 
#-----------------------------------------------------------------------------
def scan(num_ports = 20, verbose=True):
   
    #-- Lista de los dispositivos serie. Inicialmente vacia
    dispositivos_serie = []
    
    if verbose:
        print "Escanenado %d puertos serie:" % num_ports
    
    #-- Escanear num_port posibles puertos serie
    for i in range(num_ports):
    
        if verbose:
            sys.stdout.write("puerto %d: " % i)
            sys.stdout.flush()
    
        try:
      
            #-- Abrir puerto serie
            s = serial.Serial(i)
            
            if verbose: print "OK --> %s" % s.portstr
            
            #-- Si no hay errores, anadir el numero y nombre a la lista
            dispositivos_serie.append( (i, s.portstr))
            
            #-- Cerrar puerto
            s.close()
            
        #-- Si hay un error se ignora      
        except:
            if verbose: print "NO"
            pass
    #-- Devolver la lista de los dispositivos serie encontrados    
    return dispositivos_serie


def drawLinePlot(data):
    line1 = PolyLine(data,legend='Wide Line',colour='green',width=1)
    return PlotGraphics([line1],"ADC","Time (s)","Value")

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
                self.data_packet.append(data_int)
                self.data.append([])
                self.data[len(self.data)-1].append(float(len(self.data)*self.delay))
                self.data[len(self.data)-1].append(float(data_int))
                frame.page1.canvas.Draw(drawLinePlot(self.data))

class TimerThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running=1
        self.delay=1
        self.counterFlag=0
        self.captureFlag=0
    def stop(self):
        self.counterFlag=0
        self.captureFlag=0
    def startCounter(self):
        self.counterFlag=1
        self.captureFlag=0
    def startCapture(self):
        self.counterFlag=0
        self.captureFlag=1
    def stopThread(self):
        self.running=0
    def run(self):  
        self.running=1
        while self.running:
            time.sleep(self.delay)
            if self.counterFlag:
                frame.page4.counterValue.Clear()
                cnt= d.get_counter(0,frame.DaqError)
                print cnt
                frame.page4.counterValue.AppendText(str(cnt))
                print "Counter"
            if self.captureFlag:
                frame.page4.captureValue.Clear()
                selection = frame.page4.rb.GetSelection()
                cnt= d.get_capture(selection,frame.DaqError)
                frame.page4.captureValue.AppendText(str(cnt))
                print "Capture"
                print selection
                print cnt
                                
class PageOne(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
       
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=5, vgap=5)
        hSizer  =wx.BoxSizer(wx.HORIZONTAL)
        
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
        grid.Add(self.lblrange,pos=(0,2))
        self.editrange = wx.ComboBox(self, size=(95,-1),choices=self.sampleList, style=wx.CB_DROPDOWN)
        self.editrange.SetSelection(0)
        grid.Add(self.editrange,pos=(0,3)) 
        

        self.lblrate = wx.StaticText(self, label="Rate(ms)")
        grid.Add(self.lblrate,pos=(1,2))      
        self.editrate=(wx.TextCtrl(self,style=wx.TE_CENTRE))
        self.editrate.AppendText("100")
        grid.Add(self.editrate,pos=(1,3)) 
        
        self.buttonPlay = wx.Button(self, label="Play")
        self.Bind(wx.EVT_BUTTON, self.PlayEvent,self.buttonPlay)
        self.buttonStop = wx.Button(self, label="Stop")
        self.Bind(wx.EVT_BUTTON, self.StopEvent,self.buttonStop)
        self.buttonStop.Enable(False)
        
        grid.Add(self.buttonPlay,pos=(0,4))
        grid.Add(self.buttonStop,pos=(1,4))
        
        self.canvas = PlotCanvas(self)
        self.canvas.SetInitialSize(size=(600,600))
        self.canvas.SetEnableZoom(True)
        
        
        hSizer.Add(grid,0,wx.ALL)
        mainSizer.Add(hSizer, 0 , wx.ALL)
        mainSizer.Add(self.canvas,0,wx.ALL)
        self.SetSizerAndFit(mainSizer)
        
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
        
class PageTwo(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.hSizer  =wx.BoxSizer(wx.VERTICAL)
        self.buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.valueText = wx.TextCtrl(self,style=wx.TE_CENTRE)
        self.setValue = wx.Button(self, label="Set")
        self.Bind(wx.EVT_BUTTON,self.updateValue,self.setValue)
        
        self.editrate = wx.Slider(self, -1, 3000, -4080, 4080, pos=(0,200),size=(580,100),style=wx.SL_HORIZONTAL |  wx.SL_LABELS )
        self.Bind(wx.EVT_SCROLL_CHANGED,self.sliderChange,self.editrate) 
        
        self.buttonsSizer.Add(self.valueText,0,wx.ALL,border=10)
        self.buttonsSizer.Add(self.setValue,0,wx.ALL,border=10)
        
        self.hSizer.Add(self.buttonsSizer,0,wx.ALIGN_CENTER,border=10)
        self.hSizer.Add(self.editrate,0,wx.ALIGN_CENTER,border=10)
        
        self.mainSizer.Add(self.hSizer,0,wx.CENTRE)
        
        self.editrate.SetValue(0)
        self.valueText.AppendText("0")
        
        self.SetSizerAndFit(self.mainSizer)
    def sliderChange(self,event):
        self.value = self.editrate.GetValue()
        d.set_dac(self.value,frame.DaqError);
        self.valueText.Clear()
        self.valueText.AppendText(str(self.value))
    def updateValue(self,event):
        str=self.valueText.GetLineText(0)
        if str.isdigit():    
            self.value= int(str)
            self.editrate.SetValue(self.value)
            d.set_dac(self.value,frame.DaqError);
        else:
            dlg = wx.MessageDialog(self,"Not a valid value","Error!", wx.OK|wx.ICON_WARNING)
            result = dlg.ShowModal()
            dlg.Destroy()   

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
        grid = wx.GridBagSizer(hgap=4, vgap=9)
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
            self.buttons.append(wx.BitmapButton(self, id=indice+i,bitmap=self.imageRed,pos=(10, 20), size = (self.imageRed.GetWidth()+5, self.imageRed.GetHeight()+5)))
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
       
        mainSizer.Add(grid,0,wx.ALL)
        mainSizer.Add(self.buttonUpdate,0,wx.ALL)
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
        frame.page4.stopCounterEvent()
        frame.page4.stopPwmEvent()
        frame.page4.stopCaptureEvent()
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
        
        mainSizer = wx.BoxSizer(wx.HORIZONTAL) 
        pwmSizer = wx.BoxSizer(wx.VERTICAL) 
        captureSizer = wx.BoxSizer(wx.VERTICAL) 
        counterSizer = wx.BoxSizer(wx.VERTICAL) 
         
        self.periodLabel = wx.StaticText(self, label="Period(us):")
        self.dutyLabel = wx.StaticText(self, label="Duty(%):")
        
        self.periodEdit = wx.TextCtrl(self,style=wx.TE_CENTRE)
        self.dutyEdit = wx.Slider(self, -1, 0, 0, 100, pos=(0,0),size=(100,50),style=wx.SL_HORIZONTAL |  wx.SL_LABELS )
        
        self.setPWM = wx.Button(self,label="Set PWM")
        self.Bind(wx.EVT_BUTTON,self.setPWMEvent,self.setPWM)
        self.stopPwm = wx.Button(self,label="Stop PWM")
        self.Bind(wx.EVT_BUTTON,self.stopPwmEvent,self.stopPwm)
        
        self.counterValue = wx.TextCtrl(self,style=wx.TE_READONLY)
        
        
        pwmSizer.Add(self.periodLabel,0,wx.ALL)
        pwmSizer.Add(self.periodEdit,0,wx.ALL)
        pwmSizer.Add(self.dutyLabel,0,wx.ALL)
        pwmSizer.Add(self.dutyEdit,0,wx.ALL)
        pwmSizer.Add(self.setPWM,0,wx.ALL)
        pwmSizer.Add(self.stopPwm,0,wx.ALL)
        
        
        self.setCounter = wx.Button(self,label="Start counter")
        self.Bind(wx.EVT_BUTTON,self.startCounter,self.setCounter)
        self.stopCounter = wx.Button(self,label="Stop counter")
        self.stopCounter.Enable(False)
        self.Bind(wx.EVT_BUTTON,self.stopCounterEvent,self.stopCounter)
        
        counterSizer.Add(self.setCounter,0,wx.ALL)
        counterSizer.Add(self.counterValue,0,wx.ALL)
        counterSizer.Add(self.stopCounter,0,wx.ALL)
  
        self.captureValue = wx.TextCtrl(self,style=wx.TE_READONLY)
        self.setCapture = wx.Button(self,label="Start capture")
        self.Bind(wx.EVT_BUTTON,self.startCapture,self.setCapture)
        self.stopCapture = wx.Button(self,label="Stop capture")
        self.stopCapture.Enable(False)
        self.Bind(wx.EVT_BUTTON,self.stopCaptureEvent,self.stopCapture)
        
        radioList=[]
        radioList.append("Low pulse")
        radioList.append("High pulse")
        radioList.append("Whole pulse")
        self.rb = wx.RadioBox(self, label="Select width:",  choices=radioList, majorDimension=3,style=wx.RA_SPECIFY_COLS)
        
        captureSizer.Add(self.setCapture,0,wx.CENTRE)
        captureSizer.Add(self.captureValue,0,wx.CENTRE)
        captureSizer.Add(self.stopCapture,0,wx.CENTRE)  
        captureSizer.Add(self.rb,0,wx.CENTRE)  
        
        self.pwmgraphSizer.Add(pwmSizer,0,wx.ALL)
        self.capturegraphSizer.Add(captureSizer,0,wx.ALL)
        self.countergraphSizer.Add(counterSizer,0,wx.ALL)
        mainSizer.Add(self.pwmgraphSizer,0,wx.ALL)
        mainSizer.Add(self.capturegraphSizer,0,wx.ALL)
        mainSizer.Add(self.countergraphSizer,0,wx.ALL)
        self.SetSizerAndFit(mainSizer)
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
        self.setCapture.Enable(True)
        self.stopCapture.Enable(False)
        self.stopCounter.Enable(True)
        
        self.captureValue.Clear()
        
        timerThread.startCounter()
    def startCapture(self,event):
        d.capture_init(2000)
        self.setCapture.Enable(False)
        self.stopCapture.Enable(True)
        self.setCounter.Enable(True)
        self.stopCounter.Enable(False)
        
        self.counterValue.Clear()
        
        timerThread.startCapture()
    def stopCaptureEvent(self,event):
        d.capture_stop()
        self.setCounter.Enable(True)
        self.setCapture.Enable(True)
        self.stopCapture.Enable(False)
        self.stopCounter.Enable(False)
        timerThread.stop()
        
        self.counterValue.Clear()
        self.captureValue.Clear()
        
    def stopPwmEvent(self,event):
        d.capture_stop()
        self.setCounter.Enable(True)
        self.setCapture.Enable(True)
        self.stopCapture.Enable(False)
        self.stopCounter.Enable(False)
        
        d.pwm_stop(frame.DaqError)
    def stopCounterEvent(self,event):
        d.capture_stop()
        self.setCounter.Enable(True)
        self.setCapture.Enable(True)
        self.stopCapture.Enable(False)
        self.stopCounter.Enable(False)
        timerThread.stop()
        
        self.counterValue.Clear()
        self.captureValue.Clear()
        
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="OpenDaq")
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        # Here we create a panel and a notebook on the panel
        self.p = wx.Panel(self)
        self.nb = wx.Notebook(self.p)
        
        # create the page windows as children of the notebook
        self.page1 = PageOne(self.nb)
        self.page2 = PageTwo(self.nb)
        self.page3 = PageThree(self.nb)
        self.page4 = PageFour(self.nb)

        
        # add the pages to the notebook with the label to show on the tab
        self.nb.AddPage(self.page1, "Analog Input")
        self.nb.AddPage(self.page2, "Analog Output")
        self.nb.AddPage(self.page3, "Digital I/O")
        self.nb.AddPage(self.page4, "Capture-Counter-PWM")
        
        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.p.SetSizer(sizer)
        self.sizer = sizer

        self.data=[]
        self.page1.canvas.Draw(drawLinePlot(self.data))

        sz=self.page1.GetSize()
        sz[1]+=50
        sz[0]+=10
        self.SetSize(sz)
        
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
        result = dlg.ShowModal()
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
            time.sleep(0.7)
        self.dial.Close()


class InitDlg(wx.Dialog): 
    def __init__(self): 
        wx.Dialog.__init__(self, None, title="OpenDaq",style=(wx.STAY_ON_TOP | wx.CAPTION)) 
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
        dlg = wx.MessageDialog(self,"OpenDaq started","Continue", wx.OK | wx.ICON_QUESTION)
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
    timerThread=TimerThread()
    timerThread.start()
    app = MyApp(False)
    frame=MainFrame()
    frame.Centre()
    frame.Show()
    app.MainLoop()