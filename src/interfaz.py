'''
Created on 18/10/2012

@author: Adrian
'''

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
    markers = PolyMarker(data,legend='Square',colour='blue',marker='square')
    return PlotGraphics([line1,markers],"Panel Izq.","Channel","Value")

class ComThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running=1
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
        print d.adc_cfg(ch1,ch2,rangeV,20)
        self.delay=float(rate)
        self.delay/=1000
    def stop(self):
        self.running=0
        d.set_led(1)
    def restart(self):
        self.running=1
        self.data = []                   
        self.data_packet=[]
    def run(self):  
        self.running=1
        d.set_led(2)
        d.set_dac(680);
        
        self.data = []                   
        self.data_packet=[]
        while 1:
            while self.running:
                time.sleep(self.delay)
                data_int = d.read_adc()
                data_int/=8
                self.data_packet.append(data_int)
                self.data.append([])
                self.data[len(self.data)-1].append(float(len(self.data)))
                self.data[len(self.data)-1].append(float(data_int))
                frame.page1.canvas.Draw(drawLinePlot(self.data))

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
        grid.Add(self.editrange,pos=(0,3)) 
        

        self.lblrate = wx.StaticText(self, label="Rate(ms)")
        grid.Add(self.lblrate,pos=(1,2))      
        self.editrate = wx.Slider(self, -1, 100, 100, 3000, pos=(0,0),size=(100,50),style=wx.SL_HORIZONTAL |  wx.SL_LABELS ) 
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
        
        hSizer.Add(grid,0,wx.ALL)
        mainSizer.Add(hSizer, 0 , wx.ALL)
        mainSizer.Add(self.canvas,0,wx.ALL)
        self.SetSizerAndFit(mainSizer)
        
    def PlayEvent(self,event):
        self.ch1 = self.editch1.GetCurrentSelection()
        self.ch2 = self.editch2.GetCurrentSelection()
        self.range = self.editrange.GetCurrentSelection()
        self.rate = self.editrate.GetValue()
        
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
        
        if comunicationThread.is_alive():
            comunicationThread.restart()
        else:
            comunicationThread.start()
    def StopEvent(self,event):
        self.buttonPlay.Enable(True)
        self.buttonStop.Enable(False)
        
        comunicationThread.stop()
        
class PageTwo(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.hSizer  =wx.BoxSizer(wx.HORIZONTAL)
        
        self.editrate = wx.Slider(self, -1, 3000, -4080, 4080, pos=(0,200),size=(580,100),style=wx.SL_HORIZONTAL |  wx.SL_LABELS )
        self.Bind(wx.EVT_SCROLL_CHANGED,self.sliderChange,self.editrate) 
        self.hSizer.Add(self.editrate,0,wx.CENTER)
        self.SetSizerAndFit(self.hSizer)
    def sliderChange(self,event):
        self.value = self.editrate.GetValue()
        d.set_dac(self.value);

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
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="OpenDaq")
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        # Here we create a panel and a notebook on the panel
        p = wx.Panel(self)
        nb = wx.Notebook(p)
        
        # create the page windows as children of the notebook
        self.page1 = PageOne(nb)
        self.page2 = PageTwo(nb)
        self.page3 = PageThree(nb)

        
        # add the pages to the notebook with the label to show on the tab
        nb.AddPage(self.page1, "Analog Input")
        nb.AddPage(self.page2, "Analog Output")
        nb.AddPage(self.page3, "Digital I/O")
        
        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        p.SetSizer(sizer)

        sz=self.page1.GetSize()
        sz[1]+=50
        sz[0]+=10
        self.SetSize(sz)
        
    def OnClose(self,event):
        dlg = wx.MessageDialog(self,"Do you really want to close this application?","Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            comunicationThread.stop()
            self.Destroy()
            d.close()
    def ShowErrorParameters(self):
            dlg = wx.MessageDialog(self,"Verify parameters","Error!", wx.OK|wx.ICON_WARNING)
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
    d = DAQ("COM10")
    comunicationThread=ComThread()
    app = MyApp(False)
    frame=MainFrame()
    frame.Centre()
    frame.Show()
    app.MainLoop()
