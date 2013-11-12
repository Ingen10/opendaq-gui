#!/usr/bin/env python

# Copyright 2012
# Adrian Alvarez <alvarez@ingen10.com> and Juan Menendez <juanmb@ingen10.com>
#
# This file is part of opendaq.
#
# opendaq is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# opendaq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with opendaq.  If not, see <http://www.gnu.org/licenses/>.

import sys
import wx
import threading
import fractions
import time
from wx.lib.agw.floatspin import FloatSpin
import csv
import serial

import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure

from daq import DAQ

#-----------------------------------------------------------------------------
# Find available serial ports.
# INPUTS:
# -Num_ports: Number of ports scanned. Default 20
# -Verbose: verbose mode True / False. If turned on will
# print everything that is happening
# Returns:
# A list with all ports found. Each list item
# is a tuple with the number of the port and the device
#-----------------------------------------------------------------------------


def scan(num_ports=20, verbose=True):
    # -- List of serial devices. Empty at start
    serial_dev = []
    if verbose:
        print "Scan %d serial ports:" % num_ports
    # -- Scan num_port posible serial ports
    for i in range(num_ports):
        if verbose:
            sys.stdout.write("Port %d: " % i)
            sys.stdout.flush()
        try:
            # -- Open serial port
            # select which Operating system is current installed
            plt = sys.platform
            if plt == "linux2":
                port = "/dev/ttyUSB%d" % i
                s = serial.Serial(port)
            elif plt == "win32":
                s = serial.Serial(i)
            if verbose:
                print "OK --> %s" % s.portstr
            # -- If no errors, add port name to the list
            serial_dev.append((i, s.portstr))
            # -- Close port
            s.close()
        # -- Ignore possible errors
        except:
            if verbose:
                print "NO"
            pass
    # -- Return list of serial devices
    return serial_dev


class TimerThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = 1
        self.drawing = self.lastLength = self.currentLength = 0
        self.delay = 0.2

    def stop(self):
        self.drawing = 0

    def startDrawing(self):
        self.drawing = 1

    def stopThread(self):
        self.running = 0

    def run(self):
        while self.running:
            time.sleep(self.delay)
            if self.drawing:
                if(frame.p.toolbar.mode == "pan/zoom"):
                    continue
                if(frame.p.toolbar.mode == "zoom rect"):
                    continue
                frame.p.canvas.mpl_disconnect(frame.p.cidUpdate)
                try:
                    frame.p.axes.clear()
                    frame.p.axes.autoscale(False)
                    frame.p.axes.grid(color='gray', linestyle='dashed')
                    for i in range(4):
                        if(len(
                            comunicationThread.y[i]) ==
                                len(comunicationThread.x[i])):
                                    frame.p.axes.plot(
                                        comunicationThread.y[i],
                                        comunicationThread.x[i],
                                        color=frame.colors[i])
                    frame.p.canvas.draw()
                    frame.p.axes.autoscale(True)
                except:
                    print "Error trying to paint"
                frame.p.cidUpdate = frame.p.canvas.mpl_connect(
                    'motion_notify_event', frame.p.UpdateStatusBar)
                self.endTime = time.time()


class ComThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = 1
        self.x = [[], [], [], []]
        self.y = [[], [], [], []]
        self.data_packet = []
        self.delay = self.threadSleep = 1
        self.ch = []

    def stop(self):
        self.streaming = 0
        self.stopping = self.delay = self.threadSleep = 1

    def stopThread(self):
        self.running = 0

    def restart(self):
        self.initTime = time.time()
        self.x = [[], [], [], []]
        self.y = [[], [], [], []]
        self.data_packet = []
        frame.setVoltage(0.8)
        self.streaming = 1
        self.count = 0
        frame.daq.start()
        timeList = []
        for i in range(4):
            timeList.append(int(frame.p.rate[i]))
        self.threadSleep = min(timeList)/4
        for i in range(3):
            if (frame.p.enableCheck[i+1].GetValue()):
                value = int(frame.p.rate[i+1])
                if value < self.threadSleep:
                    self.threadSleep = value
        if self.threadSleep < 10:
            self.threadSleep = 0
        else:
            self.threadSleep /= 2000.0

    def run(self):
        self.running = 1
        self.stopping = self.streaming = 0
        self.data_packet = []
        while self.running:
            time.sleep(self.threadSleep)
            if self.streaming:
                self.data_packet = []
                self.ch = []
                ret = frame.daq.get_stream(self.data_packet, self.ch)
                if ret == 0:
                    continue
                if ret == 2:
                    # Write information comming from OpenDaq
                    self.debug = ''.join(map(chr, self.data_packet))
                    self.data_packet = []
                    while True:
                        ret = frame.daq.get_stream(self.data_packet, self.ch)
                        if ret == 0:
                            break
                        if ret == 2:
                            self.debug += ''.join(map(chr, self.data_packet))
                            self.data_packet = []
                        if ret == 3:
                            # Experiment stopped by Odaq
                            frame.stopChannel(self.ch[0])
                        if ret == 1:
                            break
                    if ret != 1:
                        continue
                if ret == 3:
                    frame.stopChannel(self.ch[0])
                self.count += 1
                self.currentTime = time.time()
                self.difTime = self.currentTime-self.initTime
                for i in range(len(self.data_packet)):
                    data_int = self.data_packet[i]
                    if frame.vHW == "s" and frame.p.ch2[self.ch[0]] != 0:
                        multiplier_array = (2, 4, 5, 8, 10, 16, 20)
                        data_int /= (
                            multiplier_array[frame.p.range[self.ch[0]]-1])
                    if frame.vHW == "m":
                        gain = -frame.gains[frame.p.range[self.ch[0]]+1]
                        offset = frame.offset[frame.p.range[self.ch[0]]+1]
                    if frame.vHW == "s":
                        index1 = frame.p.ch1[self.ch[0]]
                        if frame.p.ch2[self.ch[0]] != 0:
                            index1 += 8
                        gain = frame.gains[index1]
                        offset = frame.offset[index1]
                    data = self.transform_data(float(data_int * gain)) + offset
                    self.delay = frame.p.rate[self.ch[0]]/1000.0
                    self.time = self.delay * len(self.x[self.ch[0]])
                    if self.count > (1000 / frame.p.rate[self.ch[0]]):
                        if frame.p.externFlag[self.ch[0]] == 1:
                            self.y[self.ch[0]].append(self.difTime)
                        else:
                            self.y[self.ch[0]].append(self.time)
                        self.x[self.ch[0]].append(float(data))
            if self.stopping:
                self.data_packet = []
                self.ch = []
                frame.daq.flush()
                self.stopping = 0
                while True:
                    try:
                        frame.daq.stop()
                        break
                    except:
                        if self.stopping > 1:
                            frame.p.stoppingLabel.SetLabel(
                                "Stopping... Please, wait")
                        print "Error trying to stop. Retrying"
                        self.stopping += 1
                        time.sleep(0.2)
                        frame.daq.flush()
                        pass
                for i in range(len(self.data_packet)):
                    data_int = self.data_packet[i]
                    if frame.vHW == "m":
                        gain = -frame.gains[frame.p.range[self.ch[i]]+1]
                        offset = frame.offset[frame.p.range[self.ch[i]]+1]
                    if frame.vHW == "s":
                        index1 = frame.p.ch1[self.ch[i]]
                        if frame.p.ch2[self.ch[i]] != 0:
                            index1 += 8
                        gain = frame.gains[index1]
                        offset = frame.offset[index1]
                    data_int = (
                        self.transform_data(data_int * gain) +
                        frame.offset[frame.p.range[self.ch[i]]])
                    self.delay = frame.p.rate[self.ch[i]]/1000.0
                    self.time = self.delay * len(self.x[self.ch[i]])
                    self.x[self.ch[i]].append(float(data_int))
                    self.y[self.ch[i]].append(self.time)
                frame.p.axes.cla()
                frame.p.axes.grid(color='gray', linestyle='dashed')
                for i in range(4):
                    frame.p.axes.plot(
                        comunicationThread.y[i],
                        comunicationThread.x[i], color=frame.colors[i])
                frame.p.canvas.draw()
                frame.daq.flush()
                for i in range(4):
                    if frame.p.enableCheck[i].GetValue():
                        try:
                            frame.daq.destroy_channel(i+1)
                        except:
                            frame.daq.flush()
                            print "Error trying to destroy channel"
                            frame.daq.close()
                            frame.daq.open()
                frame.p.stoppingLabel.SetLabel("")
                self.stopping = 0
                frame.p.buttonPlay.Enable(True)

    def transform_data(self, data):
        if frame.vHW == "m":
            return data / 100000
        if frame.vHW == "s":
            return data / 10000


class StreamDialog(wx.Dialog):
    def __init__(self, parent):
        # Call wxDialog's __init__ method
        wx.Dialog.__init__(self, parent, -1, 'Config', size=(200, 200))
        boxSizer = wx.GridBagSizer(hgap=5, vgap=5)
        mainLayout = wx.BoxSizer(wx.VERTICAL)
        hSizer = wx.GridBagSizer(hgap=5, vgap=5)
        self.csvFlag = self.burstModeFlag = 0
        self.dataLbl = []
        self.datagraphSizer = []
        dataSizer = []
        self.enable = []
        self.periodoLabel = wx.StaticText(self, label="Period (ms)")
        self.periodoEdit = FloatSpin(
            self, value=frame.p.periodStreamOut, min_val=1, max_val=65535,
            increment=100, digits=3)
        self.offsetLabel = wx.StaticText(self, label="Offset")
        self.offsetEdit = FloatSpin(
            self, value=frame.p.offsetStreamOut/1000, min_val=-4.0,
            max_val=4.0, increment=0.1, digits=3)
        self.amplitudeLabel = wx.StaticText(self, label="Amplitude")
        self.amplitudeEdit = FloatSpin(
            self, value=frame.p.amplitudeStreamOut/1000, min_val=0.001,
            max_val=4.0, increment=0.1, digits=3)
        # Sine
        box = wx.StaticBox(self, -1, 'Sine')
        self.dataLbl.append(box)
        self.datagraphSizer.append(
            wx.StaticBoxSizer(self.dataLbl[0], wx.HORIZONTAL))
        dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.datagraphSizer[0].Add(dataSizer[0], 0, wx.ALL)
        # Square
        box = wx.StaticBox(self, -1, 'Square')
        self.dataLbl.append(box)
        self.datagraphSizer.append(
            wx.StaticBoxSizer(self.dataLbl[1], wx.HORIZONTAL))
        dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.tOnLabel = wx.StaticText(self, label="Time On")
        self.tOnEdit = FloatSpin(
            self, value=frame.p.tOnStreamOut, min_val=1, max_val=65535,
            increment=100, digits=3)
        self.datagraphSizer[1].Add(dataSizer[1], 0, wx.ALL)
        # SawTooth
        box = wx.StaticBox(self, -1, 'Sawtooth')
        self.dataLbl.append(box)
        self.datagraphSizer.append(
            wx.StaticBoxSizer(self.dataLbl[2], wx.HORIZONTAL))
        dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.datagraphSizer[2].Add(dataSizer[2], 0, wx.ALL)
        # Triangle
        box = wx.StaticBox(self, -1, 'Triangle')
        self.dataLbl.append(box)
        self.datagraphSizer.append(
            wx.StaticBoxSizer(self.dataLbl[3], wx.HORIZONTAL))
        dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.tRiseLabel = wx.StaticText(self, label="Rise time")
        self.tRiseEdit = FloatSpin(
            self, value=frame.p.tRiseStreamOut, min_val=1, max_val=65535,
            increment=100, digits=3)
        self.datagraphSizer[3].Add(dataSizer[3], 0, wx.ALL)
        # Fixed potential
        box = wx.StaticBox(self, -1, 'Fixed potential')
        self.dataLbl.append(box)
        self.datagraphSizer.append(
            wx.StaticBoxSizer(self.dataLbl[4], wx.HORIZONTAL))
        dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.datagraphSizer[4].Add(dataSizer[4], 0, wx.ALL)
        hSizer.Add(self.periodoLabel, pos=(0, 0))
        hSizer.Add(self.periodoEdit, pos=(0, 1))
        hSizer.Add(self.offsetLabel, pos=(0, 2))
        hSizer.Add(self.offsetEdit, pos=(0, 3))
        hSizer.Add(self.amplitudeLabel, pos=(0, 4))
        hSizer.Add(self.amplitudeEdit, pos=(0, 5))
        for i in range(5):
            self.enable.append(wx.CheckBox(self, label='Enable', id=200+i))
            if(frame.p.waveForm == i):
                self.enable[i].SetValue(1)
            if(frame.p.waveForm == 4):
                self.amplitudeEdit.Enable(False)
            dataSizer[i].Add(self.enable[i], 0, wx.ALL, border=10)
            self.Bind(wx.EVT_CHECKBOX, self.enableEvent, self.enable[i])
        dataSizer[1].Add(self.tOnLabel, 0, wx.ALL, border=10)
        dataSizer[1].Add(self.tOnEdit, 0, wx.ALL, border=10)
        dataSizer[3].Add(self.tRiseLabel, 0, wx.ALL, border=10)
        dataSizer[3].Add(self.tRiseEdit, 0, wx.ALL, border=10)
        boxSizer.Add(self.datagraphSizer[0], pos=(0, 0))
        boxSizer.Add(self.datagraphSizer[1], pos=(0, 1))
        boxSizer.Add(self.datagraphSizer[2], pos=(1, 0))
        boxSizer.Add(self.datagraphSizer[3], pos=(1, 1))
        boxSizer.Add(self.datagraphSizer[4], pos=(0, 2))
        self.burstMode = wx.CheckBox(self, label='Period (us)')
        self.Bind(wx.EVT_CHECKBOX, self.burstModeEvent, self.burstMode)
        self.periodoBurstEdit = FloatSpin(
            self, value=frame.p.periodStreamOut * 100, min_val=100,
            max_val=65535, increment=10, digits=0)
        self.periodoBurstEdit.Enable(False)
        hSizer.Add(self.burstMode, pos=(1, 0))
        hSizer.Add(self.periodoBurstEdit, pos=(1, 1))
        self.submit = wx.Button(self, label="Submit")
        self.csv = wx.Button(self, label="Import CSV")
        self.Bind(wx.EVT_BUTTON, self.importEvent, self.csv)
        self.Bind(wx.EVT_BUTTON, self.submitEvent, self.submit)
        hSizer.Add(self.submit, pos=(2, 5))
        hSizer.Add(self.csv, pos=(2, 0))
        mainLayout.Add(boxSizer, 0, wx.ALL, border=10)
        mainLayout.Add(hSizer, 0, wx.ALL, border=10)
        self.SetSizerAndFit(mainLayout)

    def burstModeEvent(self, event):
        if self.burstMode.GetValue() is True:
            self.periodoBurstEdit.Enable(True)
            self.periodoEdit.Enable(False)
        else:
            self.periodoBurstEdit.Enable(False)
            self.periodoEdit.Enable(True)

    def importEvent(self, event):
        self.dirname = ''
        dlg = wx.FileDialog(
            self, "Choose a file", self.dirname, "", "*.odq", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            with open(self.dirname+"\\"+self.filename, 'rb') as csvfile:
                reader = csv.reader(csvfile)
                self.csvBuffer = []
                try:
                    for index, row in enumerate(reader):
                        for i in range(len(row)):
                            self.csvBuffer.append(int(row[i]))
                except:
                    dlg = wx.MessageDialog(
                        self, "Error importing CSV", "Error",
                        wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
        # Calibration
        for i in range(len(self.csvBuffer)):
            self.csvBuffer[i] = calibration(int(round(self.csvBuffer[i])))
        dlg.Destroy()
        self.csvFlag = 1
        for i in range(4):
            self.enable[i].SetValue(0)
            self.enable[i].Enable(False)
        self.tOnEdit.Enable(False)
        self.tRiseEdit.Enable(False)
        self.amplitudeEdit.Enable(False)
        self.offsetEdit.Enable(False)

    def submitEvent(self, event):
        self.burstModeFlag = self.burstMode.GetValue()
        # Check values
        if self.csvFlag:
            self.period = self.periodoEdit.GetValue()
            self.EndModal(wx.ID_OK)
            return 0
        self.signal = -1
        for i in range(5):
            if(self.enable[i].IsChecked()):
                self.signal = i
                frame.p.waveForm = i
        self.amplitude = self.amplitudeEdit.GetValue() * 1000
        self.offset = self.offsetEdit.GetValue() * 1000
        self.ton = self.tOnEdit.GetValue()
        self.tRise = self.tRiseEdit.GetValue()
        if self.burstMode.GetValue():
            self.period = self.periodoBurstEdit.GetValue() / 100
        else:
            self.period = self.periodoEdit.GetValue()
        if self.signal < 0:
            dlg = wx.MessageDialog(
                self, "At least one signal should be selected", "Error!",
                wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            return 0
        if self.amplitude + abs(self.offset) > 4000:
            dlg = wx.MessageDialog(
                self, "Maximun value can not be greater than 4000", "Error!",
                wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            return 0
        if self.ton + 1 >= self.period and self.enable[1].IsChecked():
            dlg = wx.MessageDialog(
                self, "Time on can not be greater than period", "Error!",
                wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            return 0
        if self.tRise + 1 >= self.period and self.enable[3].IsChecked():
            dlg = wx.MessageDialog(
                self, "Time rise can not be greater than period", "Error!",
                wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            return 0
        self.EndModal(wx.ID_OK)

    def enableEvent(self, event):
        index1 = event.GetEventObject().GetId()-200
        if(self.enable[index1].IsChecked()):
            for i in range(5):
                if i != index1:
                    self.enable[i].SetValue(0)
        if(self.enable[4].IsChecked()):
            self.amplitudeEdit.Enable(False)
        else:
            self.amplitudeEdit.Enable(True)


class ConfigDialog (wx.Dialog):
    def __init__(self, parent, index1):
        # Call wxDialog's __init__ method
        wx.Dialog.__init__(self, parent, -1, 'Config', size=(200, 200))
        dataSizer = wx.GridBagSizer(hgap=5, vgap=5)
        mainLayout = wx.BoxSizer(wx.HORIZONTAL)
        self.sampleList = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8")
        self.lblch1 = wx.StaticText(self, label="Ch+")
        dataSizer.Add(self.lblch1, pos=(0, 0))
        self.editch1 = wx.ComboBox(
            self, size=(95, -1), choices=self.sampleList, style=wx.CB_READONLY)
        selection = frame.p.ch1[index1] - 1
        self.editch1.SetSelection(selection)
        dataSizer.Add(self.editch1, pos=(0, 1))
        self.Bind(wx.EVT_COMBOBOX, self.editch1Change, self.editch1)
        if frame.vHW == "m":
            self.sampleList = ("AGND", "VREF", "A5", "A6", "A7", "A8")
        if frame.vHW == "s":
            self.sampleList = ("AGND", "A2")
        self.lblch2 = wx.StaticText(self, label="Ch-")
        dataSizer.Add(self.lblch2, pos=(1, 0))
        self.editch2 = wx.ComboBox(
            self, size=(95, -1), choices=self.sampleList, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.editch2Change, self.editch2)
        selection = frame.p.ch2[index1]
        if selection == 25:
            selection = 1
        else:
            if selection != 0:
                selection -= 3
        self.editch2.SetSelection(selection)
        dataSizer.Add(self.editch2, pos=(1, 1))
        if frame.vHW == "m":
            self.sampleList = (
                "+-12 V", "+-4 V", "+-2 V", "+-0.4 V", "+-0.04 V")
            self.lblrange = wx.StaticText(self, label="Range")
        if frame.vHW == "s":
            self.sampleList = (
                "x1", "x2", "x4", "x5", "x8", "x10", "x16", "x20")
            self.lblrange = wx.StaticText(self, label="Multiplier")
        dataSizer.Add(self.lblrange, pos=(2, 0))
        self.editrange = wx.ComboBox(
            self, size=(95, -1), choices=self.sampleList, style=wx.CB_READONLY)
        self.editrange.SetSelection(frame.p.range[index1])
        dataSizer.Add(self.editrange, pos=(2, 1))
        if frame.vHW == "s":
            self.editrange.SetValue("x1")
            self.editrange.Enable(False)
            self.lblrange.Enable(False)
        self.lblrate = wx.StaticText(self, label="Rate(ms)")
        dataSizer.Add(self.lblrate, pos=(0, 3))
        self.editrate = wx.TextCtrl(self, style=wx.TE_CENTRE)
        self.editrate.AppendText(str(frame.p.rate[index1]))
        dataSizer.Add(self.editrate, pos=(0, 4))
        self.enableExtern = wx.CheckBox(self, label="Enable extern")
        self.Bind(wx.EVT_CHECKBOX, self.externModeEvent, self.enableExtern)
        self.enableExtern.SetValue(False)
        dataSizer.Add(self.enableExtern, pos=(0, 5))
        self.lblsamples = wx.StaticText(self, label="Samples per point")
        dataSizer.Add(self.lblsamples, pos=(1, 3))
        self.editsamples = wx.TextCtrl(self, style=wx.TE_CENTRE)
        self.editsamples.AppendText(str(frame.p.samples[index1]))
        dataSizer.Add(self.editsamples, pos=(1, 4))
        self.sampleList = (
            "Continuous", "Single run: 20", "Single run:40", "Single run: 100")
        self.lblmode = wx.StaticText(self, label="Mode")
        dataSizer.Add(self.lblmode, pos=(2, 3))
        self.editmode = wx.ComboBox(
            self, size=(95, -1), choices=self.sampleList, style=wx.CB_READONLY)
        self.editmode.SetSelection(frame.p.mode[index1])
        dataSizer.Add(self.editmode, pos=(2, 4))
        self.okButton = wx.Button(self, label="Confirm")
        self.Bind(wx.EVT_BUTTON, self.confirmEvent, self.okButton)
        dataSizer.Add(self.okButton, pos=(3, 5))
        mainLayout.Add(dataSizer, 1, wx.EXPAND | wx.ALL, 20)
        self.SetSizerAndFit(mainLayout)
        self.editch1Change(0)

    def externModeEvent(self, event):
        self.editrate.Enable(not self.enableExtern.GetValue())

    def confirmEvent(self, event):
        if self.editrate.GetLineText(0).isdigit():
            self.rate = int(self.editrate.GetLineText(0))
            if self.rate < 1 or self.rate > 65535:
                dlg = wx.MessageDialog(
                    self, "Time can not be neither greater than 65535 nor \
                    lower than 1", "Error!", wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()
                return 0
        else:
            dlg = wx.MessageDialog(
                self, "Not a valid time", "Error!", wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            return
        string = self.editsamples.GetLineText(0)
        if string.isdigit():
            self.samples = int(self.editsamples.GetLineText(0))
            if self.samples < 1 or self.samples > 255:
                dlg = wx.MessageDialog(
                    self, "Samples can not be neither greater than 255 nor \
                    lower than 1", "Error!", wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()
                return 0
        else:
            dlg = wx.MessageDialog(
                self, "Not a valid time", "Error!", wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            return 0
        self.EndModal(wx.ID_OK)

    def editch2Change(self, event):
        if frame.vHW == "m":
            return
        value = self.editch2.GetValue()
        if value == "AGND":
            self.editrange.SetValue("x1")
            self.editrange.Enable(False)
            self.lblrange.Enable(False)
        else:
            self.editrange.Enable(True)
            self.lblrange.Enable(True)

    def editch1Change(self, event):
        if frame.vHW == "m":
            return
        value = self.editch1.GetValue()
        self.editch2.Clear()
        self.editch2.Append("AGND")
        if (int(value[1]) % 2) == 0:
            self.editch2.Append("A" + str(int(value[1])-1))
        else:
            self.editch2.Append("A" + str(int(value[1])+1))
        self.editch2.SetSelection(0)
        self.editrange.SetSelection(0)
        self.editrange.Enable(False)
        self.lblrange.Enable(False)


class MyCustomToolbar(NavigationToolbar2Wx):
    ON_CUSTOM_LEFT = wx.NewId()
    ON_CUSTOM_RIGHT = wx.NewId()

    def __init__(self, plotCanvas):
        # Create the default toolbar
        NavigationToolbar2Wx.__init__(self, plotCanvas)
        # Remove the unwanted button
        delete_array = (8, 7, 2, 1)
        for i in delete_array:
            self.DeleteToolByPos(i)


class InterfazPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.frame = parent
        self.enableCheck = []
        # Configuration save
        self.ch1 = [1, 1, 1, 1]
        self.ch2 = [0, 0, 0, 0]
        if self.frame.vHW == "m":
            self.range = [1, 1, 1, 1]
        if self.frame.vHW == "s":
            self.range = [0, 0, 0, 0]
        self.rate = [100, 100, 100, 100]
        self.samples = [20, 20, 20, 20]
        self.mode = [0, 0, 0, 0]
        self.npoint = [0, 0, 0, 0]
        self.externFlag = [0, 0, 0, 0]
        self.burstModeStreamOut = self.waveForm = 0
        self.amplitudeStreamOut = self.offsetStreamOut = 1000
        self.tOnStreamOut = self.tRiseStreamOut = 5
        self.periodStreamOut = 15
        self.configure = []
        self.color = []
        self.dataLbl = []
        self.datagraphSizer = []
        dataSizer = []
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        datasSizer = wx.BoxSizer(wx.VERTICAL)
        graphSizer = wx.BoxSizer(wx.VERTICAL)
        plotSizer = wx.BoxSizer(wx.VERTICAL)
        hSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        for i in range(4):
            box = wx.StaticBox(self, -1, 'Experiment %d' % (i+1))
            self.dataLbl.append(box)
            self.datagraphSizer.append(
                wx.StaticBoxSizer(self.dataLbl[i], wx.HORIZONTAL))
            dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))
            self.enableCheck.append(wx.CheckBox(self, label="Enable"))
            self.enableCheck[i].SetValue(False)
            dataSizer[i].Add(self.enableCheck[i], 0, wx.ALL, border=10)
            self.configure.append(wx.Button(self, id=i+100, label="Configure"))
            self.Bind(wx.EVT_BUTTON, self.configureEvent, self.configure[i])
            dataSizer[i].Add(self.configure[i], 0, wx.ALL, border=10)
            self.color.append(wx.StaticText(self, label="..........."))
            if i < 3:
                color = (255 * (i == 0), 255 * (i == 1), 255 * (i == 2))
            else:
                color = (0, 0, 0)
            self.color[i].SetForegroundColour(color)  # Set text color
            self.color[i].SetBackgroundColour(color)  # Set text back color
            dataSizer[i].Add(self.color[i], 0, wx.ALL, border=10)
            self.datagraphSizer[i].Add(dataSizer[i], 0, wx.ALL)
            datasSizer.Add(self.datagraphSizer[i], 0, wx.ALL, border=10)
        # Stream out panel
        box = wx.StaticBox(self, -1, 'Waveform generator')
        self.dataLbl.append(box)
        self.datagraphSizer.append(
            wx.StaticBoxSizer(self.dataLbl[4], wx.HORIZONTAL))
        dataSizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.enableCheck.append(wx.CheckBox(self, label="Enable"))
        self.Bind(wx.EVT_CHECKBOX, self.streamEnable, self.enableCheck[4])
        self.enableCheck[4].SetValue(False)
        dataSizer[4].Add(self.enableCheck[4], 0, wx.ALL, border=10)
        self.configure.append(wx.Button(self, id=400, label="Configure"))
        self.Bind(wx.EVT_BUTTON, self.configureStream, self.configure[4])
        dataSizer[4].Add(self.configure[4], 0, wx.ALL, border=10)
        self.datagraphSizer[4].Add(dataSizer[4], 0, wx.ALL)
        datasSizer.Add(self.datagraphSizer[4], 0, wx.ALL, border=10)
        # Export
        box = wx.StaticBox(self, -1, 'Export graphics')
        self.exportLbl = box
        self.exportSizer = wx.StaticBoxSizer(self.exportLbl, wx.HORIZONTAL)
        self.png = wx.Button(self, label="As PNG file...")
        self.Bind(wx.EVT_BUTTON, self.saveAsPNGEvent, self.png)
        self.csv = wx.Button(self, label="As CSV file...")
        self.Bind(wx.EVT_BUTTON, self.saveAsCSVEvent, self.csv)
        hSizer2.Add(self.png, 0, wx.ALL)
        hSizer2.Add(self.csv, 0, wx.ALL)
        self.exportSizer.Add(hSizer2, 0, wx.ALL)
        self.buttonPlay = wx.Button(self, label="Play")
        self.Bind(wx.EVT_BUTTON, self.PlayEvent, self.buttonPlay)
        self.buttonStop = wx.Button(self, label="Stop")
        self.Bind(wx.EVT_BUTTON, self.StopEvent, self.buttonStop)
        self.buttonStop.Enable(False)
        self.stoppingLabel = wx.StaticText(self, label="")
        datasSizer.Add(self.exportSizer, 0, wx.ALL, border=10)
        graphSizer.Add(datasSizer, 0, wx.ALL)
        graphSizer.Add(self.buttonPlay, 0, wx.CENTRE, border=5)
        graphSizer.Add(self.buttonStop, 0, wx.CENTRE, border=5)
        graphSizer.Add(self.stoppingLabel, 0, wx.CENTRE, border=5)
        self.figure = Figure(facecolor='#ece9d8')
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.axes.set_xlabel("Time (s)", fontsize=12)
        self.axes.set_ylabel("Voltage (mV)", fontsize=12)
        self.axes.autoscale(False)
        self.canvas.SetInitialSize(size=(600, 600))
        self.add_toolbar()
        self.cidUpdate = self.canvas.mpl_connect(
            'motion_notify_event', self.UpdateStatusBar)
        plotSizer.Add(self.toolbar, 0, wx.CENTER)
        plotSizer.Add(self.canvas, 0, wx.ALL)
        mainSizer.Add(graphSizer, 0, wx.ALL)
        mainSizer.Add(plotSizer, 0, wx.ALL)
        self.SetSizerAndFit(mainSizer)

    def UpdateStatusBar(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            frame.statusBar.SetStatusText(
                ("x= " + "%.4g" % x + "  y=" + "%.4g" % y), 1)

    def add_toolbar(self):
        self.toolbar = MyCustomToolbar(self.canvas)
        self.toolbar.Realize()
        # On Windows platform, default window size is incorrect, so set
        # toolbar width to figure width.
        tw, th = self.toolbar.GetSizeTuple()
        fw, fh = self.canvas.GetSizeTuple()
        # By adding toolbar in sizer, we are able to put it at the bottom
        # of the frame - so appearance is closer to GTK version.
        # As noted above, doesn't work for Mac.
        self.toolbar.SetSize(wx.Size(fw, th))
        # self.mainSizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()

    def saveAsPNGEvent(self, event):
        self.dirname = ''
        dlg = wx.FileDialog(
            self, "Choose a file", self.dirname, "", "*.png", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            self.figure.savefig(self.dirname+"\\"+self.filename)
        dlg.Destroy()

    def saveAsCSVEvent(self, event):
        self.dirname = ''
        dlg = wx.FileDialog(
            self, "Choose a file", self.dirname, "", "*.odq", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            for j in range(4):
                if self.enableCheck[j].IsChecked():
                    with open(
                        self.dirname + "\\" + str(j) + self.filename,
                            'wb') as csvfile:
                                spamwriter = csv.writer(
                                    csvfile, quoting=csv.QUOTE_MINIMAL)
                                for i in range(len(comunicationThread.x[j])):
                                    spamwriter.writerow(
                                        [comunicationThread.x[j][i],
                                            comunicationThread.y[j][i]])
        dlg.Destroy()

    def configureStream(self, event):
        dlg = StreamDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            self.burstModeStreamOut = dlg.burstModeFlag
            if dlg.csvFlag:
                self.buffer = dlg.csvBuffer[:140]
                self.interval = int(dlg.period/(len(self.buffer)))
            else:
                self.periodStreamOut = dlg.period
                self.amplitudeStreamOut = dlg.amplitude
                self.offsetStreamOut = dlg.offset
                self.signalStreamOut = dlg.signal
                self.tRiseStreamOut = dlg.tRise
                self.tOnStreamOut = dlg.ton
                self.signalCreate()
        dlg.Destroy()
        self.streamEnable(0)

    def streamEnable(self, event):
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

    def configureEvent(self, event):
        wx.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        index1 = event.GetEventObject().GetId()-100
        dlg = ConfigDialog(self, index1)
        if dlg.ShowModal() == wx.ID_OK:
            self.ch1[index1] = dlg.editch1.GetCurrentSelection()
            self.ch2[index1] = dlg.editch2.GetCurrentSelection()
            self.range[index1] = dlg.editrange.GetCurrentSelection()
            self.ch1[index1] += 1
            if self.ch2[index1] == 1:
                self.ch2[index1] = 25
            elif self.ch2[index1] > 1:
                self.ch2[index1] += 3
            if dlg.enableExtern.GetValue() is True:
                self.rate[index1] = int(dlg.editrate.GetLineText(0))
                self.externFlag[index1] = 1
            else:
                self.rate[index1] = int(dlg.editrate.GetLineText(0))
                self.externFlag[index1] = 0
            self.samples[index1] = int(dlg.editsamples.GetLineText(0))
            self.mode[index1] = dlg.editmode.GetCurrentSelection()
            if self.mode[index1] == 0:
                self.npoint[index1] = self.mode[index1] = 0
            else:
                self.npoint[index1] = 20 * self.mode[index1]
                self.mode[index1] = 1
            dlg.Destroy()

    def PlayEvent(self, event):
        self.channel = []
        for i in range(4):
            if self.enableCheck[i].GetValue():
                frame.channelState[i] = 1
                self.channel.append(
                    [self.ch1[i], self.ch2[i], self.rate[i], self.range[i]])
                if self.rate[i] < 10:
                    self.npoint[i] = 30000
                    self.mode[i] = 1
                if self.externFlag[i] == 1:
                    frame.daq.create_external(i+1, 0)
                else:
                    frame.daq.create_stream(i+1, self.rate[i])
                frame.daq.setup_channel(
                    i+1, self.npoint[i], self.mode[i])  # Mode continuous
                frame.daq.conf_channel(
                    i+1, 0, self.ch1[i], self.ch2[i], self.range[i],
                    self.samples[i])  # Analog input
        if self.enableCheck[4].GetValue():
            if self.burstModeStreamOut:
                frame.daq.create_burst(self.interval * 100)
                frame.daq.setup_channel(
                    1, len(self.buffer), 0)  # Mode continuous
                frame.daq.conf_channel(1, 1, 0, 0, 0, 0)  # Analog output
            else:
                frame.daq.create_stream(4, self.interval)
                frame.daq.setup_channel(
                    4, len(self.buffer), 0)  # Mode continuous
                frame.daq.conf_channel(4, 1, 0, 0, 0, 0)  # Analog output
            # Cut signal buffer into x length buffers
            xLength = 20
            nBuffers = len(self.buffer) / xLength
            for i in range(nBuffers):
                self.init = i * xLength
                self.end = self.init+xLength
                self.interBuffer = self.buffer[self.init:self.end]
                frame.daq.load_signal(self.interBuffer, self.init)
            self.init = nBuffers * xLength
            self.interBuffer = self.buffer[self.init:]
            if len(self.interBuffer) > 0:
                frame.daq.load_signal(self.interBuffer, self.init)
        self.buttonPlay.Enable(False)
        self.buttonStop.Enable(True)
        timerThread.startDrawing()
        comunicationThread.restart()

    def StopEvent(self, event):
        self.buttonStop.Enable(False)
        comunicationThread.stop()
        timerThread.stop()

    def signalCreate(self):
        if self.signalStreamOut == 0:
            # Sine
            if self.periodStreamOut < 140:
                self.interval = 1
            else:
                self.interval = int(self.periodStreamOut/140)
                self.interval += 1
            self.t = np.arange(0, self.periodStreamOut, self.interval)
            self.buffer = np.sin(2 * np.pi / self.periodStreamOut * self.t) * (
                self.amplitudeStreamOut)
            for i in range(len(self.buffer)):
                self.buffer[i] = self.buffer[i]+self.offsetStreamOut
        if self.signalStreamOut == 1:
            # Square
            self.buffer = []
            self.interval = fractions.gcd(
                self.periodStreamOut, self.tOnStreamOut)
            self.pointsOn = int(self.tOnStreamOut / self.interval)
            self.points = int(self.periodStreamOut / self.interval)
            for i in range(self.pointsOn):
                self.buffer.append(
                    self.amplitudeStreamOut+self.offsetStreamOut)
            for i in range(self.points-self.pointsOn):
                self.buffer.append(self.offsetStreamOut)
        if self.signalStreamOut == 2:
            # Sawtooth
            if self.periodStreamOut < 140:
                self.interval = 1
                self.points = int(self.periodStreamOut)
                self.increment = int(
                    self.amplitudeStreamOut/self.periodStreamOut)
            else:
                self.interval = int(self.periodStreamOut/140)
                self.interval += 1
                self.points = int(self.periodStreamOut/self.interval)
                self.increment = int(self.amplitudeStreamOut/self.points)
            self.init = int(self.offsetStreamOut)
            self.buffer = []
            for i in range(self.points):
                self.value = self.init
                self.value += (self.increment * i)
                self.buffer.append(self.value)
        if self.signalStreamOut == 3:
            # Triangle
            if self.periodStreamOut < 140:
                self.interval = 1
                self.points = int(self.tRiseStreamOut)
                self.increment = int(
                    self.amplitudeStreamOut/self.tRiseStreamOut)
            else:
                self.relation = int(self.periodStreamOut/self.tRiseStreamOut)
                self.points = int(140/self.relation)  # Ideal n points
                self.interval = int(self.tRiseStreamOut/self.points)
                self.interval += 1
                self.points = int(self.tRiseStreamOut/self.interval)
                self.increment = int(self.amplitudeStreamOut/self.points)
            self.init = int(self.offsetStreamOut)
            self.buffer = []
            for i in range(self.points):
                self.value = self.init
                self.value += (self.increment * i)
                self.buffer.append(self.value)
            if self.periodStreamOut < 140:
                self.points = int(self.periodStreamOut-self.tRiseStreamOut)
                self.increment = int(
                    self.amplitudeStreamOut /
                    (self.periodStreamOut-self.tRiseStreamOut))
            else:
                self.time = int(self.periodStreamOut-self.tRiseStreamOut)
                self.points = 140-self.points  # Ideal n points
                self.interval = int(self.time / self.points)
                self.interval += 1
                self.points = int(self.time / self.interval)
                self.increment = int(self.amplitudeStreamOut / self.points)
            self.init = int(self.offsetStreamOut + self.amplitudeStreamOut)
            for i in range(self.points):
                self.value = self.init - (self.increment * i)
                self.buffer.append(self.value)
        if self.signalStreamOut == 4:
            # Continuous
            self.buffer = []
            self.interval = self.periodStreamOut
            self.buffer.append(self.offsetStreamOut)
        # Calibration
        for i in range(len(self.buffer)):
            dacValue = self.buffer[i]
            info = self.frame.daq.get_info()
            if info[1] < 110:
                self.buffer[i] = dacValue
            else:
                self.buffer[i] = calibration(int(round(dacValue)))
        if len(self.buffer) >= 140:
            self.buffer = self.buffer[:140]


class MainFrame(wx.Frame):
    def __init__(self, commPort):
        wx.Frame.__init__(
            self, None, title="EasyDAQ", style=wx.DEFAULT_FRAME_STYLE &
            ~(wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        self.colors = 'r', 'g', 'b', 'k'
        self.daq = DAQ(commPort)
        self.vHW = self.daq.get_vHW()
        icon = wx.Icon("../resources/icon64.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetFieldsCount(2)
        info = self.daq.get_info()
        vHW = "[M]" if info[0] == 1 else "[S]"
        vFW = (
            str(info[1] / 100) + "." + str((info[1] / 10) % 10) + "." +
            str(info[1] % 10))
        self.statusBar.SetStatusText("H:%s V:%s" % (vHW, vFW), 0)
        self.channelState = [0, 0, 0, 0]
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.errorDic = {'size': 0}
        self.errorInfo = {'Failure data size': 0}
        # Here we create a panel
        self.p = InterfazPanel(self)
        sz = self.p.GetSize()
        sz[1] += 50
        sz[0] += 10
        self.SetSize(sz)
        self.daq.enable_crc(1)
        self.gains = []
        self.offset = []
        self.gains, self.offset = self.daq.get_cal()

    def setVoltage(self, voltage):
        self.daq.set_analog(voltage)

    def OnClose(self, event):
        dlg = wx.MessageDialog(
            self, "Do you really want to close this application?",
            "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            comunicationThread.stopThread()
            timerThread.stopThread()
            self.daq.close()
            self.Destroy()

    def ShowErrorParameters(self):
        dlg = wx.MessageDialog(
            self, "Verify parameters", "Error!", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()

    def stopChannel(self, number):
        self.channelState[number] = suma = 0
        for i in range(3):
            suma += self.channelState[i]
        if suma == 0:
            self.p.buttonPlay.Enable(True)
            self.p.buttonStop.Enable(False)
            comunicationThread.stop()
            timerThread.stop()


class InitDlg(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(
            self, None, title="EasyDAQ", style=(wx.STAY_ON_TOP | wx.CAPTION))
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        self.gauge = wx.Gauge(self, range=100, size=(100, 15))
        self.hsizer.Add(self.gauge, wx.EXPAND)
        avaiable_ports = scan(num_ports=255, verbose=False)
        self.sampleList = []
        if len(avaiable_ports) != 0:
            for n, nombre in avaiable_ports:
                self.sampleList.append(nombre)
        self.lblhear = wx.StaticText(self, label="Select Serial Port")
        self.edithear = wx.ComboBox(
            self, size=(95, -1), choices=self.sampleList, style=wx.CB_READONLY)
        self.edithear.SetSelection(0)
        self.hsizer.Add(self.lblhear, wx.EXPAND)
        self.hsizer.Add(self.edithear, wx.EXPAND)
        self.buttonOk = wx.Button(self, label="OK")
        self.Bind(wx.EVT_BUTTON, self.okEvent, self.buttonOk)
        self.buttonCancel = wx.Button(self, label="Cancel", pos=(115, 22))
        self.Bind(wx.EVT_BUTTON, self.cancelEvent, self.buttonCancel)
        self.vsizer.Add(self.hsizer, wx.EXPAND)
        self.vsizer.Add(self.buttonOk, wx.EXPAND)
        self.gauge.Show(False)
        self.SetSizer(self.vsizer)
        self.SetAutoLayout(1)
        self.vsizer.Fit(self)

    def okEvent(self, event):
        portN = self.edithear.GetCurrentSelection()
        if portN >= 0:
            self.buttonOk.Show(False)
            self.edithear.Show(False)
            self.buttonCancel.Show(False)
            self.gauge.Show()
            daq = DAQ(self.sampleList[portN])
            try:
                daq.get_info()
                dlg = wx.MessageDialog(
                    self, "EasyDAQ started", "Continue",
                    wx.OK | wx.ICON_QUESTION)
                dlg.ShowModal()
                dlg.Destroy()
                self.port = self.sampleList[portN]
                self.EndModal(1)
            except:
                dlg = wx.MessageDialog(
                    self, "EasyDAQ not found", "Exit",
                    wx.OK | wx.ICON_QUESTION)
                dlg.ShowModal()
                dlg.Destroy()
                self.port = 0
                self.EndModal(0)
        else:
            dlg = wx.MessageDialog(
                self, "Not a valid port", "Retry", wx.OK | wx.ICON_QUESTION)
            dlg.ShowModal()
            dlg.Destroy()

    def cancelEvent(self, event):
        self.port = 0
        self.EndModal(0)


def calibration(value):
    if not -4096 <= value < 4096:
        raise ValueError('DAQ voltage out of range')
    value *= frame.daq.dacGain
    if frame.vHW == "s":
        value *= 2
    data = (value / 1000.0 + frame.daq.dacOffset + 4096) * 2
    if frame.vHW == "s" and data < 0:
        data = 0
    return data


class MyApp(wx.App):
    def OnInit(self):
        dial = InitDlg()
        ret = dial.ShowModal()
        dial.Destroy()
        self.commPort = dial.port
        self.connected = ret
        return True

if __name__ == "__main__":
    comunicationThread = ComThread()
    comunicationThread.start()
    timerThread = TimerThread()
    timerThread.start()
    app = MyApp(False)
    if app.connected:
        frame = MainFrame(app.commPort)
        frame.Centre()
        frame.Show()
        app.MainLoop()
    else:
        comunicationThread.stopThread()
        timerThread.stopThread()
