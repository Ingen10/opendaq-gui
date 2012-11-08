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
                frame.p.canvas.Draw(drawLinePlot(self.data[0],self.data[1],self.data[2],self.data[3]))
            if self.stopping:
                self.data_packet=[]
                self.ch = []
                d.stream_stop(self.data_packet,self.ch,frame.DaqError)
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
                frame.p.canvas.Draw(drawLinePlot(self.data[0],self.data[1],self.data[2],self.data[3]))
                d.set_led(1,frame.DaqError)
                for i in range(4):
                    if frame.p.enableCheck[i].GetValue():
                        print "Destroying channel %d"%(i+1)
                        d.channel_destroy(i+1,frame.DaqError)
                self.stopping=0

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
        
        self.configure=[]
        self.color=[]
    
    
        self.dataLbl=[]
        self.datagraphSizer=[]
        dataSizer=[]  
       
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        datasSizer  =wx.BoxSizer(wx.VERTICAL)
        graphSizer = wx.BoxSizer(wx.VERTICAL)
        
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
           
            
        self.buttonPlay = wx.Button(self, label="Play")
        self.Bind(wx.EVT_BUTTON, self.PlayEvent,self.buttonPlay)
        self.buttonStop = wx.Button(self, label="Stop")
        self.Bind(wx.EVT_BUTTON, self.StopEvent,self.buttonStop)
        self.buttonStop.Enable(False)
        
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
            
            print self.externFlag    
            
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
                    print "External"
                else:
                    print "No external"
                    d.stream_create(i+1, self.rate[i],frame.DaqError)
                d.channel_setup(i+1,self.npoint[i],self.mode[i],frame.DaqError) #mode continuous
                d.channel_cfg(i+1, 0, self.ch1[i], self.ch2[i], self.range[i],self.samples[i],frame.DaqError) #analog input
                   
        self.buttonPlay.Enable(False)
        self.buttonStop.Enable(True)
        comunicationThread.restart()
        
    def StopEvent(self,event):
        self.buttonPlay.Enable(True)
        self.buttonStop.Enable(False)
        
        comunicationThread.stop()
        
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="EasyDAQ")
        
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
            time.sleep(0.7)
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
    print "frame" in locals()
    print "frame" in globals()
    app.MainLoop()
