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
import os
import wx
import threading
import time
from wx.lib.agw.floatspin import FloatSpin
import numpy
import serial
from serial.tools.list_ports import comports

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
    def __init__(self, com_port):
        wx.Frame.__init__(self, None, title="openDAQ")
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.daq = DAQ(com_port)
        self.daq.enable_crc(1)
        self.hw_ver = self.daq.hw_ver
        self.adc_gains = []
        self.adc_offset = []
        self.adc_gains, self.adc_offset = self.daq.get_cal()
        self.dac_gain = self.dac_offset = 0
        self.dac_gain, self.dac_offset = self.daq.get_dac_cal()
        # Here we create a panel and a notebook on the panel
        self.p = wx.Panel(self)
        self.nb = wx.Notebook(self.p)
        # create the page windows as children of the notebook
        self.page1 = AdcPage(self.nb, self.adc_gains, self.adc_offset, self)
        self.page1.SetBackgroundColour('#ece9d8')
        self.page2 = DacPage(self.nb, self.dac_gain, self.dac_offset, self)
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

    def on_close(self, event):
        dlg = wx.MessageDialog(
            self,
            "Do you really want to close this application?",
            "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()
            self.daq.close()

    def show_error_parameters(self):
        dlg = wx.MessageDialog(
            self, "Verify parameters", "Error!", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()


class AdcPage(wx.Panel):
    def __init__(self, parent, gains, offset, frame):
        wx.Panel.__init__(self, parent)
        self.frame = frame
        self.status = self.values = 0
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        values_sizer = wx.GridBagSizer(hgap=8, vgap=8)
        grid = wx.GridBagSizer(hgap=4, vgap=9)
        self.gains = gains
        self.offset = offset
        g_label = wx.StaticText(self, label="Slope")
        offset_label = wx.StaticText(self, label="Intercept")
        values_sizer.Add(g_label, pos=(0, 1))
        values_sizer.Add(offset_label, pos=(0, 2))
        self.gain_label = []
        self.gains_edit = []
        self.offset_edit = []
        if frame.hw_ver == "m":
            for i in range(5):
                self.gain_label.append(wx.StaticText(
                    self, label=" Gain %d" % (i+1)))
                self.gains_edit.append(wx.TextCtrl(
                    self, value=str(self.gains[i+1]), style=wx.TE_READONLY))
                self.offset_edit.append(wx.TextCtrl(
                    self, value=str(self.offset[i+1]), style=wx.TE_READONLY))
                values_sizer.Add(self.gain_label[i], pos=(i+1, 0))
                values_sizer.Add(self.gains_edit[i], pos=(i+1, 1))
                values_sizer.Add(self.offset_edit[i], pos=(i+1, 2))
        if frame.hw_ver == "s":
            for i in range(8):
                self.gain_label.append(wx.StaticText(
                    self, label="    A%d " % (i+1)))
                self.gains_edit.append(wx.TextCtrl(
                    self, value=str(self.gains[i+1]), style=wx.TE_READONLY))
                self.offset_edit.append(wx.TextCtrl(
                    self, value=str(self.offset[i+1]), style=wx.TE_READONLY))
                values_sizer.Add(self.gain_label[i], pos=(i+1, 0))
                values_sizer.Add(self.gains_edit[i], pos=(i+1, 1))
                values_sizer.Add(self.offset_edit[i], pos=(i+1, 2))
        self.value_edit = []
        self.adc_values = []
        self.buttons = []
        for i in range(5):
            self.value_edit.append(FloatSpin(
                self, value=0, min_val=-4.096, max_val=4.096,
                increment=0.001, digits=3))
            self.adc_values.append(wx.TextCtrl(
                self, value="--", style=wx.TE_READONLY))
            self.buttons.append(wx.Button(self, id=100+i, label="Update"))
            self.Bind(wx.EVT_BUTTON, self.update_event, self.buttons[i])
            grid.Add(self.value_edit[i], pos=(i+3, 0))
            grid.Add(self.adc_values[i], pos=(i+3, 1))
            grid.Add(self.buttons[i], pos=(i+3, 2))
            if i < 2:
                self.value_edit[i].Enable(True)
                self.adc_values[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.value_edit[i].Enable(False)
                self.adc_values[i].Enable(False)
        self.number_points_list = []
        for i in range(4):
            self.number_points_list.append("%d" % (i+2))
        self.number_points_label = wx.StaticText(
            self, label="Number of points")
        self.edit_number_points = wx.ComboBox(
            self, size=(95, -1), value="2", choices=self.number_points_list,
            style=wx.CB_READONLY)
        self.Bind(
            wx.EVT_COMBOBOX, self.number_points_change,
            self.edit_number_points)
        if frame.hw_ver == "m":
            self.sample_list = (
                "+-12 V", "+-4 V", "+-2 V", "+-0.4 V", "+-0.04 V")
        if frame.hw_ver == "s":
            self.sample_list = ("SE", "DE")
            self.sample_list2 = []
            for i in range(1, 9):
                self.sample_list2.append("A%d" % i)
        self.edit_range = wx.ComboBox(
            self, size=(95, -1), choices=self.sample_list,
            style=wx.CB_READONLY)
        self.edit_range.SetSelection(0)
        self.Bind(wx.EVT_COMBOBOX, self.range_change, self.edit_range)
        grid.Add(self.edit_range, pos=(1, 0))
        if frame.hw_ver == "s":
            self.selection = wx.ComboBox(
                self, size=(95, -1), choices=self.sample_list2,
                style=wx.CB_READONLY)
            self.selection.SetSelection(0)
            grid.Add(self.selection, pos=(1, 1))
        self.set_dac = wx.Button(self, label="Set DAC")
        self.edit_dac = FloatSpin(
            self, value=0, min_val=-4.096, max_val=4.096, increment=0.001,
            digits=3)
        self.Bind(wx.EVT_BUTTON, self.update_dac, self.set_dac)
        grid.Add(self.edit_dac, pos=(2, 0))
        grid.Add(self.set_dac, pos=(2, 1))
        self.update = wx.Button(self, label="Get values")
        self.Bind(wx.EVT_BUTTON, self.get_values_event, self.update)
        grid.Add(self.update, pos=(8, 0))
        self.export = wx.Button(self, label="Export...")
        self.Bind(wx.EVT_BUTTON, self.export_event, self.export)
        grid.Add(self.export, pos=(8, 1))
        grid.Add(self.number_points_label, pos=(0, 0))
        grid.Add(self.edit_number_points, pos=(0, 1))
        main_sizer.Add(grid, 0, wx.ALL, border=10)
        main_sizer.Add(values_sizer, 0, wx.ALL, border=10)
        self.SetSizerAndFit(main_sizer)

    def number_points_change(self, event):
        for i in range(5):
            if i < int(self.edit_number_points.GetValue()):
                self.value_edit[i].Enable(True)
                self.adc_values[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.value_edit[i].Enable(False)
                self.adc_values[i].Enable(False)

    def range_change(self, event):
        if self.edit_range.GetValue() == "SE":
            self.selection.Clear()
            for i in range(0, 8):
                self.gain_label[i].Label = "A%d" % (i+1)
                self.selection.Append("A%d" % (i+1))
                self.gains_edit[i].Clear()
                self.gains_edit[i].AppendText(str(self.frame.adc_gains[i+1]))
                self.offset_edit[i].Clear()
                self.offset_edit[i].AppendText(str(self.frame.adc_offset[i+1]))
            self.selection.SetSelection(0)
        if self.edit_range.GetValue() == "DE":
            self.selection.Clear()
            for i in range(1, 9):
                if i % 2:
                    word = "A%d" % i + "-A%d" % (i+1)
                else:
                    word = "A%d" % i + "-A%d" % (i-1)
                self.selection.Append(word)
                self.gain_label[i-1].Label = word
            self.selection.SetSelection(0)
            for i in range(8):
                self.gains_edit[i].Clear()
                self.gains_edit[i].AppendText(str(self.frame.adc_gains[i+9]))
                self.offset_edit[i].Clear()
                self.offset_edit[i].AppendText(str(self.frame.adc_offset[i+9]))

    def update_event(self, event):
        self.range = self.edit_range.GetCurrentSelection()
        if self.frame.hw_ver == "s":
            input = self.selection.GetCurrentSelection()+1
        button = event.GetEventObject()
        index1 = button.GetId()-100
        if self.frame.hw_ver == "m":
            self.frame.daq.conf_adc(8, 0, self.range, 20)
        if self.frame.hw_ver == "s":
            if self.range == 0:  # SE
                self.frame.daq.conf_adc(input)
            if self.range == 1:  # DE
                self.frame.daq.conf_adc(input, 1)
        time.sleep(0.5)
        data_int = self.frame.daq.read_adc()
        time.sleep(0.5)
        data_int = self.frame.daq.read_adc()  # Repeat for stabilizing
        self.adc_values[index1].Clear()
        self.adc_values[index1].AppendText(str(data_int))

    def get_values_event(self, event):
        self.range = self.edit_range.GetCurrentSelection()
        if self.frame.hw_ver == "s":
            sel = self.selection.GetCurrentSelection()
        self.x = []
        self.y = []
        for i in range(int(self.edit_number_points.GetValue())):
            self.y.append(int(self.value_edit[i].GetValue() * 1000))
            self.x.append(int(self.adc_values[i].GetLineText(0)))
        r = numpy.polyfit(self.x, self.y, 1)
        if self.frame.hw_ver == "m":
            self.slope = abs(int(r[0] * 100000))
        if self.frame.hw_ver == "s":
            self.slope = abs(int(r[0] * 10000))
        self.intercept = int(r[1])
        if self.frame.hw_ver == "m":
            self.gains_edit[self.range].Clear()
            self.gains_edit[self.range].AppendText(str(self.slope))
            self.offset_edit[self.range].Clear()
            self.offset_edit[self.range].AppendText(str(self.intercept))
            self.frame.adc_gains[self.range+1] = self.slope
            self.frame.adc_offset[self.range+1] = self.intercept
        if self.frame.hw_ver == "s":
            self.gains_edit[sel].Clear()
            self.gains_edit[sel].AppendText(str(self.slope))
            self.offset_edit[sel].Clear()
            self.offset_edit[sel].AppendText(str(self.intercept))
            if self.range == 0:  # SE
                self.frame.adc_gains[sel+1] = self.slope
                self.frame.adc_offset[sel+1] = self.intercept
            if self.range == 1:  # DE
                self.frame.adc_gains[sel+9] = self.slope
                self.frame.adc_offset[sel+9] = self.intercept
        self.frame.daq.gains = self.frame.adc_gains
        self.frame.daq.offsets = self.frame.adc_offset
        self.save_calibration()

    def update_dac(self, event):
        self.frame.daq.set_analog(self.edit_dac.GetValue())

    def save_calibration(self):
        self.slope = []
        self.intercept = []
        if self.frame.hw_ver == "m":
            for i in range(5):
                self.slope.append(int(self.gains_edit[i].GetLineText(0)))
                self.intercept.append(int(self.offset_edit[i].GetLineText(0)))
            self.flag = "M"
        if self.frame.hw_ver == "s":
            if self.edit_range.Value == "SE":
                self.flag = "SE"
                for i in range(8):
                    self.slope.append(int(self.gains_edit[i].GetLineText(0)))
                    self.intercept.append(
                        int(self.offset_edit[i].GetLineText(0)))
            if self.edit_range.Value == "DE":
                self.flag = "DE"
                for i in range(8):
                    self.slope.append(int(self.gains_edit[i].GetLineText(0)))
                    self.intercept.append(
                        int(self.offset_edit[i].GetLineText(0)))
        self.frame.daq.set_cal(self.slope, self.intercept, self.flag)

    def export_event(self, event):
        dlg = wx.TextEntryDialog(
            self, 'openDAQ ID:', 'ID', style=wx.OK | wx.CANCEL)
        res = dlg.ShowModal()
        id = dlg.GetValue()
        dlg.Destroy()
        if res == wx.ID_CANCEL:
            return
        self.directory_name = ''
        dlg = wx.FileDialog(
            self, "Choose a file", self.directory_name, "", "*.txt", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.file_name = dlg.GetFilename()
            self.directory_name = dlg.GetDirectory()
            self.export_calibration(
                self.directory_name+"/"+self.file_name, id)
        dlg.Destroy()

    def export_calibration(self, file, id):
        output_file = open(file, 'w')
        model = self.frame.hw_ver.upper()
        output_file.write(
            "CALIBRATION REPORT OPENDAQ-" + model + ": " + id + "\n\n")
        output_file.write("DAC CALIBRATION\n")
        output_file.write(
            "Slope: " + str(self.frame.dac_gain) + "    Intercept: " +
            str(self.frame.dac_offset) + "\n\n")
        output_file.write("ADC CALIBRATION\n")
        if self.frame.hw_ver == "s":
            for i in range(1, 9):
                output_file.write("A%d:\n" % i)
                output_file.write(
                    "Slope: " + str(self.frame.adc_gains[i]) + "    "
                    "Intercept: " +
                    str(self.frame.adc_offset[i]) + "\n")
            output_file.write("\n")
            for i in range(9, 17):
                if i % 2:
                    output = "A" + str(i-8) + "-A" + str(i-7) + ":\n"
                else:
                    output = "A" + str(i-8) + "-A" + str(i-9) + ":\n"
                output_file.write(output)
                output_file.write(
                    "Slope: " + str(self.frame.adc_gains[i]) + "    "
                    "Intercept: " +
                    str(self.frame.adc_offset[i]) + "\n")
        if self.frame.hw_ver == "m":
            for i in range(1, 6):
                output_file.write("Gain%d:\n" % i)
                output_file.write(
                    "Slope: " + str(self.frame.adc_gains[i]) + "    "
                    "Intercept: " +
                    str(self.frame.adc_offset[i]) + "\n")
        dlg = (wx.MessageDialog(
            self, "Report saved", "Report saved", wx.OK | wx.ICON_QUESTION))
        dlg.ShowModal()
        dlg.Destroy()


class DacPage(wx.Panel):
    def __init__(self, parent, gains, offset, frame):
        wx.Panel.__init__(self, parent)
        self.frame = frame
        self.status = self.values = 0
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        values_sizer = wx.GridBagSizer(hgap=8, vgap=8)
        grid = wx.GridBagSizer(hgap=4, vgap=9)
        self.real_dac = numpy.zeros(5)
        self.read_dac = numpy.zeros(5)
        self.gain = gains
        self.offset = offset
        g_label = wx.StaticText(self, label="Slope")
        offset_label = wx.StaticText(self, label="Intercept")
        values_sizer.Add(g_label, pos=(0, 1))
        values_sizer.Add(offset_label, pos=(0, 2))
        self.gain_label = wx.StaticText(self, label=" Gain ")
        self.gains_edit = wx.TextCtrl(
            self, value=str(self.gain), style=wx.TE_READONLY)
        self.offset_edit = wx.TextCtrl(
            self, value=str(self.offset), style=wx.TE_READONLY)
        self.check_dac = wx.Button(self, label="Check DAC")
        if frame.hw_ver == "m":
            self.edit_check = FloatSpin(
                self, value=0, min_val=-4.096, max_val=4.095, increment=0.001,
                digits=3)
        else:
            self.edit_check = FloatSpin(
                self, value=0, min_val=0, max_val=4.095, increment=0.001,
                digits=3)
        self.Bind(wx.EVT_BUTTON, self.check_dac_event, self.check_dac)
        values_sizer.Add(self.gain_label, pos=(1, 0))
        values_sizer.Add(self.gains_edit, pos=(1, 1))
        values_sizer.Add(self.offset_edit, pos=(1, 2))
        values_sizer.Add(self.check_dac, pos=(3, 0))
        values_sizer.Add(self.edit_check, pos=(3, 1))
        self.value_edit = []
        self.adc_values = []
        self.buttons = []
        for i in range(5):
            self.value_edit.append(FloatSpin(
                self, value=0, min_val=-4.096, max_val=4.096,
                increment=0.001, digits=3))
            self.buttons.append(wx.Button(self, id=100+i, label="Fix"))
            self.Bind(wx.EVT_BUTTON, self.update_event, self.buttons[i])
            grid.Add(self.value_edit[i], pos=(i+3, 0))
            grid.Add(self.buttons[i], pos=(i+3, 1))
            if i < 2:
                self.value_edit[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.value_edit[i].Enable(False)
        self.number_points_list = []
        for i in range(4):
            self.number_points_list.append("%d" % (i+2))
        self.number_points_label = wx.StaticText(
            self, label="Number of points")
        self.edit_number_points = wx.ComboBox(
            self, size=(95, -1), value="2", choices=self.number_points_list,
            style=wx.CB_READONLY)
        self.Bind(
            wx.EVT_COMBOBOX, self.number_points_change,
            self.edit_number_points)
        self.set_dac = wx.Button(self, label="Set DAC")
        self.edit_dac = FloatSpin(
            self, value=0, min_val=-4.096, max_val=4.096, increment=0.001,
            digits=3)
        self.Bind(wx.EVT_BUTTON, self.update_dac, self.set_dac)
        grid.Add(self.edit_dac, pos=(1, 0))
        grid.Add(self.set_dac, pos=(1, 1))
        self.update = wx.Button(self, label="Get values")
        self.Bind(wx.EVT_BUTTON, self.get_values_event, self.update)
        grid.Add(self.update, pos=(8, 0))
        self.reset = wx.Button(self, label="Reset")
        self.Bind(wx.EVT_BUTTON, self.reset_event, self.reset)
        grid.Add(self.reset, pos=(8, 1))
        grid.Add(self.number_points_label, pos=(0, 0))
        grid.Add(self.edit_number_points, pos=(0, 1))
        main_sizer.Add(grid, 0, wx.ALL, border=10)
        main_sizer.Add(values_sizer, 0, wx.ALL, border=10)
        self.SetSizerAndFit(main_sizer)

    def number_points_change(self, event):
        for i in range(5):
            if i < int(self.edit_number_points.GetValue()):
                self.value_edit[i].Enable(True)
                self.buttons[i].Enable(True)
            else:
                self.buttons[i].Enable(False)
                self.value_edit[i].Enable(False)

    def update_event(self, event):
        index1 = event.GetEventObject().GetId()-100
        self.real_dac[index1] = self.edit_dac.GetValue()
        self.read_dac[index1] = self.value_edit[index1].GetValue()
        self.value_edit[index1].Enable(False)
        self.buttons[index1].Enable(False)

    def get_values_event(self, event):
        self.x = []
        self.y = []
        for i in range(int(self.edit_number_points.GetValue())):
            self.y.append(self.real_dac[i] * 1000)
            self.x.append(self.read_dac[i] * 1000)
        r = numpy.polyfit(self.x, self.y, 1)
        self.slope = abs(int(r[0] * 1000))
        self.intercept = int(round(r[1], 0))
        self.gains_edit.Clear()
        self.gains_edit.AppendText(str(self.slope))
        self.offset_edit.Clear()
        self.offset_edit.AppendText(str(self.intercept))
        self.frame.adc_gains[0] = self.slope
        self.frame.adc_offset[0] = self.intercept
        self.frame.dac_gain = self.slope
        self.frame.dac_offset = self.intercept
        self.frame.daq.dac_gain = self.slope
        self.frame.daq.dac_offset = self.intercept
        self.save_calibration()

    def reset_event(self, event):
        for i in range(int(self.edit_number_points.GetValue())):
            self.buttons[i].Enable(True)
            self.value_edit[i].Enable(True)
        self.real_dac = numpy.zeros(5)
        self.read_dac = numpy.zeros(5)

    def check_dac_event(self, event):
        self.frame.daq.set_analog(self.edit_check.GetValue())

    def update_dac(self, event):
        self.frame.daq.set_dac((self.edit_dac.GetValue() * 1000 + 4096) * 2)

    def save_calibration(self):
        self.frame.daq.dac_gain = self.slope
        self.frame.daq.dac_offset = self.intercept
        self.frame.daq.set_dac_cal(self.slope, self.intercept)


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
        self.horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        self.gauge = wx.Gauge(self, range=100, size=(100, 15))
        self.horizontal_sizer.Add(self.gauge, wx.EXPAND)
        avaiable_ports = list(comports())
        self.sample_list = []
        if len(avaiable_ports) != 0:
            for nombre in avaiable_ports:
                self.sample_list.append(nombre[0])
        self.label_hear = wx.StaticText(self, label="Select Serial Port")
        self.edit_hear = wx.ComboBox(
            self, size=(95, -1), choices=self.sample_list,
            style=wx.CB_READONLY)
        self.edit_hear.SetSelection(0)
        self.horizontal_sizer.Add(self.label_hear, wx.EXPAND)
        self.horizontal_sizer.Add(self.edit_hear, wx.EXPAND)
        self.button_ok = wx.Button(self, label="OK")
        self.Bind(wx.EVT_BUTTON, self.ok_event, self.button_ok)
        self.button_cancel = wx.Button(self, label="Cancel", pos=(115, 22))
        self.Bind(wx.EVT_BUTTON, self.cancel_event, self.button_cancel)
        self.vertical_sizer.Add(self.horizontal_sizer, wx.EXPAND)
        self.vertical_sizer.Add(self.button_ok, wx.EXPAND)
        self.gauge.Show(False)
        self.SetSizer(self.vertical_sizer)
        self.SetAutoLayout(1)
        self.vertical_sizer.Fit(self)

    def ok_event(self, event):
        port_number = self.edit_hear.GetCurrentSelection()
        if port_number >= 0:
            self.button_ok.Show(False)
            self.edit_hear.Show(False)
            self.button_cancel.Show(False)
            self.gauge.Show()
            try:
                daq = DAQ(self.sample_list[port_number])
            except:
                dlg = wx.MessageDialog(
                    self, "Port in use. Select another port", "Error",
                    wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()
                os.execl(sys.executable, sys.executable, * sys.argv)  # Restart
            try:
                daq.get_info()
                dlg = wx.MessageDialog(
                    self, "openDAQ calibration started", "Continue",
                    wx.OK | wx.ICON_QUESTION)
                dlg.ShowModal()
                dlg.Destroy()
                self.port = self.sample_list[port_number]
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

    def cancel_event(self, event):
        self.port = 0
        self.EndModal(0)


class MyApp(wx.App):
    def OnInit(self):
        dial = InitDlg()
        ret = dial.ShowModal()
        dial.Destroy()
        self.com_port = dial.port
        self.connected = ret
        return True


def main():
    app = MyApp(False)
    if app.com_port != 0:
        frame = MainFrame(app.com_port)
        frame.Centre()
        frame.Show()
        app.MainLoop()


if __name__ == "__main__":
    main()
