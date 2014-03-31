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
import time
from wx.lib.agw.floatspin import FloatSpin
import numpy
import serial

from opendaq import DAQ

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


def scan(num_ports=20, verbose=True):
    #-- List of serial devices. Initially empty
    serial_devices = []
    if verbose:
        print "Scanning %d serial ports:" % num_ports
    #-- Scan num_port possible serial ports
    for i in range(num_ports):
        if verbose:
            sys.stdout.write("port %d: " % i)
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
            serial_devices.append((i, s.portstr))
            # -- Close port
            s.close()
        #-- Ignore possible errors
        except:
            if verbose:
                print "NO"
            pass
    #-- Return list of found serial devices
    return serial_devices


class MainFrame(wx.Frame):
    def __init__(self, commPort):
        wx.Frame.__init__(self, None, title="openDAQ")
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.daq = DAQ(commPort)
        self.daq.enable_crc(1)
        self.vHW = self.daq.hw_ver
        self.adcgains = []
        self.adcoffset = []
        self.adcgains, self.adcoffset = self.daq.get_cal()
        self.dacgain = self.dacoffset = 0
        self.dacgain, self.dacoffset = self.daq.get_dac_cal()
        # Here we create a panel and a notebook on the panel
        self.p = wx.Panel(self)
        self.nb = wx.Notebook(self.p)
        # create the page windows as children of the notebook
        self.page1 = AdcPage(self.nb, self.adcgains, self.adcoffset, self)
        self.page1.SetBackgroundColour('#ece9d8')
        self.page2 = DacPage(self.nb, self.dacgain, self.dacoffset, self)
        self.page2.SetBackgroundColour('#ece9d8')
        # add the pages to the notebook with the label to show on the tab
        self.nb.AddPage(self.page1, "ADC")
        self.nb.AddPage(self.page2, "DAC")
        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.p.SetSizer(sizer)
        sz = self.page1.GetSize()
        sz[1] += 80
        sz[0] += 10
        self.SetSize(sz)

    def OnClose(self, event):
        dlg = wx.MessageDialog(
            self,
            "Do you really want to close this application?",
            "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()
            frame.daq.close()

    def ShowErrorParameters(self):
        dlg = wx.MessageDialog(
            self, "Verify parameters", "Error!", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()


class AdcPage(wx.Panel):
    def __init__(self, parent, gains, offset, frame):
        wx.Panel.__init__(self, parent)
        self.status = self.values = 0
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        valuesSizer = wx.GridBagSizer(hgap=8, vgap=8)
        grid = wx.GridBagSizer(hgap=4, vgap=9)
        self.gains = gains
        self.offset = offset
        gLabel = wx.StaticText(self, label="Slope")
        offsetLabel = wx.StaticText(self, label="Intercept")
        valuesSizer.Add(gLabel, pos=(0, 1))
        valuesSizer.Add(offsetLabel, pos=(0, 2))
        self.gainLabel = []
        self.gainsEdit = []
        self.offsetEdit = []
        if frame.vHW == "m":
            for i in range(5):
                self.gainLabel.append(wx.StaticText(
                    self, label=" Gain %d" % (i+1)))
                self.gainsEdit.append(wx.TextCtrl(
                    self, value=str(self.gains[i+1]), style=wx.TE_READONLY))
                self.offsetEdit.append(wx.TextCtrl(
                    self, value=str(self.offset[i+1]), style=wx.TE_READONLY))
                valuesSizer.Add(self.gainLabel[i], pos=(i+1, 0))
                valuesSizer.Add(self.gainsEdit[i], pos=(i+1, 1))
                valuesSizer.Add(self.offsetEdit[i], pos=(i+1, 2))
        if frame.vHW == "s":
            for i in range(8):
                self.gainLabel.append(wx.StaticText(
                    self, label="    A%d " % (i+1)))
                self.gainsEdit.append(wx.TextCtrl(
                    self, value=str(self.gains[i+1]), style=wx.TE_READONLY))
                self.offsetEdit.append(wx.TextCtrl(
                    self, value=str(self.offset[i+1]), style=wx.TE_READONLY))
                valuesSizer.Add(self.gainLabel[i], pos=(i+1, 0))
                valuesSizer.Add(self.gainsEdit[i], pos=(i+1, 1))
                valuesSizer.Add(self.offsetEdit[i], pos=(i+1, 2))
        self.valueEdit = []
        self.adcValues = []
        self.buttons = []
        for i in range(5):
            self.valueEdit.append(FloatSpin(
                self, value=0, min_val=-4.096, max_val=4.096,
                increment=0.001, digits=3))
            self.adcValues.append(wx.TextCtrl(
                self, value="--", style=wx.TE_READONLY))
            self.buttons.append(wx.Button(self, id=100+i, label="Update"))
            self.Bind(wx.EVT_BUTTON, self.updateEvent, self.buttons[i])
            grid.Add(self.valueEdit[i], pos=(i+3, 0))
            grid.Add(self.adcValues[i], pos=(i+3, 1))
            grid.Add(self.buttons[i], pos=(i+3, 2))
            if i < 2:
                self.valueEdit[i].Enable(True)
                self.adcValues[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.valueEdit[i].Enable(False)
                self.adcValues[i].Enable(False)
        self.nPointsList = []
        for i in range(4):
            self.nPointsList.append("%d" % (i+2))
        self.npointsLabel = wx.StaticText(self, label="Number of points")
        self.editnpoints = wx.ComboBox(
            self, size=(95, -1), value="2", choices=self.nPointsList,
            style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.nPointsChange, self.editnpoints)
        if frame.vHW == "m":
            self.sampleList = (
                "+-12 V", "+-4 V", "+-2 V", "+-0.4 V", "+-0.04 V")
        if frame.vHW == "s":
            self.sampleList = ("SE", "DE")
            self.sampleList2 = []
            for i in range(1, 9):
                self.sampleList2.append("A%d" % i)
        self.editrange = wx.ComboBox(
            self, size=(95, -1), choices=self.sampleList, style=wx.CB_READONLY)
        self.editrange.SetSelection(0)
        self.Bind(wx.EVT_COMBOBOX, self.rangeChange, self.editrange)
        grid.Add(self.editrange, pos=(1, 0))
        if frame.vHW == "s":
            self.selection = wx.ComboBox(
                self, size=(95, -1), choices=self.sampleList2,
                style=wx.CB_READONLY)
            self.selection.SetSelection(0)
            grid.Add(self.selection, pos=(1, 1))
        self.setDAC = wx.Button(self, label="Set DAC")
        self.editDAC = FloatSpin(
            self, value=0, min_val=-4.096, max_val=4.096, increment=0.001,
            digits=3)
        self.Bind(wx.EVT_BUTTON, self.updateDAC, self.setDAC)
        grid.Add(self.editDAC, pos=(2, 0))
        grid.Add(self.setDAC, pos=(2, 1))
        self.update = wx.Button(self, label="Get values")
        self.Bind(wx.EVT_BUTTON, self.getValuesEvent, self.update)
        grid.Add(self.update, pos=(8, 0))
        self.export = wx.Button(self, label="Export...")
        self.Bind(wx.EVT_BUTTON, self.exportEvent, self.export)
        grid.Add(self.export, pos=(8, 1))
        grid.Add(self.npointsLabel, pos=(0, 0))
        grid.Add(self.editnpoints, pos=(0, 1))
        mainSizer.Add(grid, 0, wx.ALL, border=10)
        mainSizer.Add(valuesSizer, 0, wx.ALL, border=10)
        self.SetSizerAndFit(mainSizer)

    def nPointsChange(self, event):
        for i in range(5):
            if i < int(self.editnpoints.GetValue()):
                self.valueEdit[i].Enable(True)
                self.adcValues[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.valueEdit[i].Enable(False)
                self.adcValues[i].Enable(False)

    def rangeChange(self, event):
        if self.editrange.GetValue() == "SE":
            self.selection.Clear()
            for i in range(0, 8):
                self.gainLabel[i].Label = "A%d" % (i+1)
                self.selection.Append("A%d" % (i+1))
                self.gainsEdit[i].Clear()
                self.gainsEdit[i].AppendText(str(frame.adcgains[i+1]))
                self.offsetEdit[i].Clear()
                self.offsetEdit[i].AppendText(str(frame.adcoffset[i+1]))
            self.selection.SetSelection(0)
        if self.editrange.GetValue() == "DE":
            self.selection.Clear()
            for i in range(1, 9):
                if i % 2:
                    word = "A%d" % i + "-A%d" % (i+1)
                else:
                    word = "A%d" % i + "-A%d" % (i-1)
                self.selection.Append(word)
                self.gainLabel[i-1].Label = word
            self.selection.SetSelection(0)
            for i in range(8):
                self.gainsEdit[i].Clear()
                self.gainsEdit[i].AppendText(str(frame.adcgains[i+9]))
                self.offsetEdit[i].Clear()
                self.offsetEdit[i].AppendText(str(frame.adcoffset[i+9]))

    def updateEvent(self, event):
        self.range = self.editrange.GetCurrentSelection()
        if frame.vHW == "s":
            input = self.selection.GetCurrentSelection()+1
        button = event.GetEventObject()
        index1 = button.GetId()-100
        if frame.vHW == "m":
            frame.daq.conf_adc(8, 0, self.range, 20)
        if frame.vHW == "s":
            if self.range == 0:  # SE
                frame.daq.conf_adc(input)
            if self.range == 1:  # DE
                frame.daq.conf_adc(input, 1)
        time.sleep(0.5)
        data_int = frame.daq.read_adc()
        time.sleep(0.5)
        data_int = frame.daq.read_adc()  # Repeat for stabilizing
        self.adcValues[index1].Clear()
        self.adcValues[index1].AppendText(str(data_int))

    def getValuesEvent(self, event):
        self.range = self.editrange.GetCurrentSelection()
        if frame.vHW == "s":
            sel = self.selection.GetCurrentSelection()
        self.x = []
        self.y = []
        for i in range(int(self.editnpoints.GetValue())):
            self.y.append(int(self.valueEdit[i].GetValue() * 1000))
            self.x.append(int(self.adcValues[i].GetLineText(0)))
        r = numpy.polyfit(self.x, self.y, 1)
        if frame.vHW == "m":
            self.slope = abs(int(r[0] * 100000))
        if frame.vHW == "s":
            self.slope = abs(int(r[0] * 10000))
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
            if self.range == 0:  # SE
                frame.adcgains[sel+1] = self.slope
                frame.adcoffset[sel+1] = self.intercept
            if self.range == 1:  # DE
                frame.adcgains[sel+9] = self.slope
                frame.adcoffset[sel+9] = self.intercept
        daq.gains = frame.adcgains
        daq.offsets = frame.adcoffset
        self.saveCalibration()

    def updateDAC(self, event):
        frame.daq.set_analog(self.editDAC.GetValue())

    def saveCalibration(self):
        self.slope = []
        self.intercept = []
        if frame.vHW == "m":
            for i in range(5):
                self.slope.append(int(self.gainsEdit[i].GetLineText(0)))
                self.intercept.append(int(self.offsetEdit[i].GetLineText(0)))
            self.flag = "M"
        if frame.vHW == "s":
            if self.editrange.Value == "SE":
                self.flag = "SE"
                for i in range(8):
                    self.slope.append(int(self.gainsEdit[i].GetLineText(0)))
                    self.intercept.append(
                        int(self.offsetEdit[i].GetLineText(0)))
            if self.editrange.Value == "DE":
                self.flag = "DE"
                for i in range(8):
                    self.slope.append(int(self.gainsEdit[i].GetLineText(0)))
                    self.intercept.append(
                        int(self.offsetEdit[i].GetLineText(0)))
        frame.daq.set_cal(self.slope, self.intercept, self.flag)

    def exportEvent(self, event):
        dlg = wx.TextEntryDialog(
            self, 'openDAQ ID:', 'ID', style=wx.OK | wx.CANCEL)
        res = dlg.ShowModal()
        id = dlg.GetValue()
        dlg.Destroy()
        if res == wx.ID_CANCEL:
            return
        self.dirname = ''
        dlg = wx.FileDialog(
            self, "Choose a file", self.dirname, "", "*.txt", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            self.exportCalibration(
                self.dirname+"/"+self.filename, id)
        dlg.Destroy()

    def exportCalibration(self, file, id):
        outputfile = open(file, 'w')
        model = frame.vHW.upper()
        outputfile.write(
            "CALIBRATION REPORT OPENDAQ-" + model + ": " + id + "\n\n")
        outputfile.write("DAC CALIBRATION\n")
        outputfile.write(
            "Slope: " + str(frame.dacgain) + "    Intercept: " +
            str(frame.dacoffset) + "\n\n")
        outputfile.write("ADC CALIBRATION\n")
        if frame.vHW == "s":
            for i in range(1, 9):
                outputfile.write("A%d:\n" % i)
                outputfile.write(
                    "Slope: " + str(frame.adcgains[i]) + "    Intercept: " +
                    str(frame.adcoffset[i]) + "\n")
            outputfile.write("\n")
            for i in range(9, 17):
                if i % 2:
                    output = "A" + str(i-8) + "-A" + str(i-7) + ":\n"
                else:
                    output = "A" + str(i-8) + "-A" + str(i-9) + ":\n"
                outputfile.write(output)
                outputfile.write(
                    "Slope: " + str(frame.adcgains[i]) + "    Intercept: " +
                    str(frame.adcoffset[i]) + "\n")
        if frame.vHW == "m":
            for i in range(1, 6):
                outputfile.write("Gain%d:\n" % i)
                outputfile.write(
                    "Slope: " + str(frame.adcgains[i]) + "    Intercept: " +
                    str(frame.adcoffset[i]) + "\n")
        dlg = (wx.MessageDialog(
            self, "Report saved", "Report saved", wx.OK | wx.ICON_QUESTION))
        dlg.ShowModal()
        dlg.Destroy()


class DacPage(wx.Panel):
    def __init__(self, parent, gains, offset, frame):
        wx.Panel.__init__(self, parent)
        self.status = self.values = 0
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        valuesSizer = wx.GridBagSizer(hgap=8, vgap=8)
        grid = wx.GridBagSizer(hgap=4, vgap=9)
        self.realDAC = numpy.zeros(5)
        self.readDAC = numpy.zeros(5)
        self.gain = gains
        self.offset = offset
        gLabel = wx.StaticText(self, label="Slope")
        offsetLabel = wx.StaticText(self, label="Intercept")
        valuesSizer.Add(gLabel, pos=(0, 1))
        valuesSizer.Add(offsetLabel, pos=(0, 2))
        self.gainLabel = wx.StaticText(self, label=" Gain ")
        self.gainsEdit = wx.TextCtrl(
            self, value=str(self.gain), style=wx.TE_READONLY)
        self.offsetEdit = wx.TextCtrl(
            self, value=str(self.offset), style=wx.TE_READONLY)
        self.checkDAC = wx.Button(self, label="Check DAC")
        if frame.vHW == "m":
            self.editCheck = FloatSpin(
                self, value=0, min_val=-4.096, max_val=4.095, increment=0.001,
                digits=3)
        else:
            self.editCheck = FloatSpin(
                self, value=0, min_val=0, max_val=4.095, increment=0.001,
                digits=3)
        self.Bind(wx.EVT_BUTTON, self.checkDacEvent, self.checkDAC)
        valuesSizer.Add(self.gainLabel, pos=(1, 0))
        valuesSizer.Add(self.gainsEdit, pos=(1, 1))
        valuesSizer.Add(self.offsetEdit, pos=(1, 2))
        valuesSizer.Add(self.checkDAC, pos=(3, 0))
        valuesSizer.Add(self.editCheck, pos=(3, 1))
        self.valueEdit = []
        self.adcValues = []
        self.buttons = []
        for i in range(5):
            self.valueEdit.append(FloatSpin(
                self, value=0, min_val=-4.096, max_val=4.096,
                increment=0.001, digits=3))
            self.buttons.append(wx.Button(self, id=100+i, label="Fix"))
            self.Bind(wx.EVT_BUTTON, self.updateEvent, self.buttons[i])
            grid.Add(self.valueEdit[i], pos=(i+3, 0))
            grid.Add(self.buttons[i], pos=(i+3, 1))
            if i < 2:
                self.valueEdit[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.valueEdit[i].Enable(False)
        self.nPointsList = []
        for i in range(4):
            self.nPointsList.append("%d" % (i+2))
        self.npointsLabel = wx.StaticText(self, label="Number of points")
        self.editnpoints = wx.ComboBox(
            self, size=(95, -1), value="2", choices=self.nPointsList,
            style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.nPointsChange, self.editnpoints)
        self.setDAC = wx.Button(self, label="Set DAC")
        self.editDAC = FloatSpin(
            self, value=0, min_val=-4.096, max_val=4.096, increment=0.001,
            digits=3)
        self.Bind(wx.EVT_BUTTON, self.updateDAC, self.setDAC)
        grid.Add(self.editDAC, pos=(1, 0))
        grid.Add(self.setDAC, pos=(1, 1))
        self.update = wx.Button(self, label="Get values")
        self.Bind(wx.EVT_BUTTON, self.getValuesEvent, self.update)
        grid.Add(self.update, pos=(8, 0))
        self.reset = wx.Button(self, label="Reset")
        self.Bind(wx.EVT_BUTTON, self.resetEvent, self.reset)
        grid.Add(self.reset, pos=(8, 1))
        grid.Add(self.npointsLabel, pos=(0, 0))
        grid.Add(self.editnpoints, pos=(0, 1))
        mainSizer.Add(grid, 0, wx.ALL, border=10)
        mainSizer.Add(valuesSizer, 0, wx.ALL, border=10)
        self.SetSizerAndFit(mainSizer)

    def nPointsChange(self, event):
        for i in range(5):
            if i < int(self.editnpoints.GetValue()):
                self.valueEdit[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.valueEdit[i].Enable(False)

    def updateEvent(self, event):
        index1 = event.GetEventObject().GetId()-100
        self.realDAC[index1] = self.editDAC.GetValue()
        self.readDAC[index1] = self.valueEdit[index1].GetValue()
        self.valueEdit[index1].Enable(False)
        self.buttons[index1].Enable(False)

    def getValuesEvent(self, event):
        self.x = []
        self.y = []
        for i in range(int(self.editnpoints.GetValue())):
            self.y.append(self.realDAC[i] * 1000)
            self.x.append(self.readDAC[i] * 1000)
        r = numpy.polyfit(self.x, self.y, 1)
        self.slope = abs(int(r[0] * 1000))
        self.intercept = int(round(r[1], 0))
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

    def resetEvent(self, event):
        for i in range(int(self.editnpoints.GetValue())):
            self.buttons[i].Enable(True)
            self.valueEdit[i].Enable(True)
        self.realDAC = numpy.zeros(5)
        self.readDAC = numpy.zeros(5)

    def checkDacEvent(self, event):
        frame.daq.set_analog(self.editCheck.GetValue())

    def updateDAC(self, event):
        frame.daq.set_dac((self.editDAC.GetValue() * 1000 + 4096) * 2)

    def saveCalibration(self):
        frame.daq.set_DAC_cal(self.slope, self.intercept)


class InitThread (threading.Thread):
    def __init__(self, dial):
        threading.Thread.__init__(self)
        self.dial = dial

    def run(self):
        for i in range(10):
            self.dial.gauge.SetValue(pos=i * 10)
            time.sleep(0.7)
        self.dial.Close()


class InitDlg(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(
            self, None, title="DAQControl",
            style=(wx.STAY_ON_TOP | wx.CAPTION))
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
                    self, "openDAQ calibration started", "Continue",
                    wx.OK | wx.ICON_QUESTION)
                dlg.ShowModal()
                dlg.Destroy()
                self.port = self.sampleList[portN]
                self.EndModal(1)
            except:
                dlg = wx.MessageDialog(
                    self, "DAQControl not found", "Exit",
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


class MyApp(wx.App):
    def OnInit(self):
        dial = InitDlg()
        ret = dial.ShowModal()
        dial.Destroy()
        self.commPort = dial.port
        self.connected = ret
        return True

if __name__ == "__main__":
    app = MyApp(False)
    if app.commPort != 0:
        frame = MainFrame(app.commPort)
        frame.Centre()
        frame.Show()
        app.MainLoop()
