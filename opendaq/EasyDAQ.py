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
from wx.lib.pubsub import Publisher
import csv
import serial

import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure

from opendaq import DAQ

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
        self.drawing = self.last_length = self.current_length = 0
        self.delay = 0.2

    def stop(self):
        self.drawing = 0

    def start_drawing(self):
        self.drawing = 1

    def stop_thread(self):
        self.running = 0

    def run(self):
        while self.running:
            time.sleep(self.delay)
            if self.drawing:
                wx.CallAfter(Publisher().sendMessage, "refresh")
                self.end_time = time.time()


class ComThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = 1
        self.x = [[], [], [], []]
        self.y = [[], [], [], []]
        self.data_packet = []
        self.delay = self.thread_sleep = 1
        self.ch = []

    def stop(self):
        self.streaming = 0
        self.stopping = self.delay = self.thread_sleep = 1

    def stop_thread(self):
        self.running = 0

    def restart(self):
        self.init_time = time.time()
        self.x = [[], [], [], []]
        self.y = [[], [], [], []]
        self.data_packet = []
        frame.set_voltage(0.8)
        self.streaming = 1
        self.count = 0
        frame.daq.start()
        time_list = []
        for i in range(4):
            time_list.append(int(frame.p.rate[i]))
        self.thread_sleep = min(time_list)/4
        for i in range(3):
            if (frame.p.enable_check[i+1].GetValue()):
                value = int(frame.p.rate[i+1])
                if value < self.thread_sleep:
                    self.thread_sleep = value
        if self.thread_sleep < 10:
            self.thread_sleep = 0
        else:
            self.thread_sleep /= 2000.0

    def run(self):
        self.running = 1
        self.stopping = self.streaming = 0
        self.data_packet = []
        while self.running:
            time.sleep(self.thread_sleep)
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
                            frame.stop_channel(self.ch[0])
                        if ret == 1:
                            break
                    if ret != 1:
                        continue
                if ret == 3:
                    frame.stop_channel(self.ch[0])
                self.count += 1
                self.current_time = time.time()
                self.dif_time = self.current_time-self.init_time
                for i in range(len(self.data_packet)):
                    data_int = self.data_packet[i]
                    if frame.hw_ver == "s" and frame.p.ch_2[self.ch[0]] != 0:
                        multiplier_array = (1, 2, 4, 5, 8, 10, 16, 20)
                        data_int /= (
                            multiplier_array[frame.p.range[self.ch[0]]])
                    if frame.hw_ver == "m":
                        gain = -frame.gains[frame.p.range[self.ch[0]]+1]
                        offset = frame.offset[frame.p.range[self.ch[0]]+1]
                    if frame.hw_ver == "s":
                        index_1 = frame.p.ch_1[self.ch[0]]
                        if frame.p.ch_2[self.ch[0]] != 0:
                            index_1 += 8
                        gain = frame.gains[index_1]
                        offset = frame.offset[index_1]
                    data = self.transform_data(float(data_int * gain)) + offset
                    self.delay = frame.p.rate[self.ch[0]]/1000.0
                    print "RATE2", self.delay
                    self.time = self.delay * len(self.x[self.ch[0]])
                    if frame.p.extern_flag[self.ch[0]] == 1:
                        self.y[self.ch[0]].append(self.dif_time)
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
                            frame.p.stopping_label.SetLabel(
                                "Stopping... Please, wait")
                        print "Error trying to stop. Retrying"
                        self.stopping += 1
                        time.sleep(0.2)
                        frame.daq.flush()
                        pass
                for i in range(len(self.data_packet)):
                    data_int = self.data_packet[i]
                    if frame.hw_ver == "m":
                        gain = -frame.gains[frame.p.range[self.ch[i]]+1]
                        offset = frame.offset[frame.p.range[self.ch[i]]+1]
                    if frame.hw_ver == "s":
                        index_1 = frame.p.ch_1[self.ch[i]]
                        if frame.p.ch_2[self.ch[i]] != 0:
                            index_1 += 8
                        gain = frame.gains[index_1]
                        offset = frame.offset[index_1]
                    data_int = (
                        self.transform_data(data_int * gain) +
                        frame.offset[frame.p.range[self.ch[i]]])
                    self.delay = frame.p.rate[self.ch[i]]/1000.0
                    self.time = self.delay * len(self.x[self.ch[i]])
                    self.x[self.ch[i]].append(float(data_int))
                    self.y[self.ch[i]].append(self.time)
                wx.CallAfter(Publisher().sendMessage, "stop")
                self.stopping = 0

    def transform_data(self, data):
        if frame.hw_ver == "m":
            return data / 100000
        if frame.hw_ver == "s":
            return data / 10000


class StreamDialog(wx.Dialog):
    def __init__(self, parent):
        # Call wxDialog's __init__ method
        wx.Dialog.__init__(self, parent, -1, 'Config', size=(200, 200))
        box_sizer = wx.GridBagSizer(hgap=5, vgap=5)
        main_layout = wx.BoxSizer(wx.VERTICAL)
        horizontal_sizer = wx.GridBagSizer(hgap=5, vgap=5)
        self.csv_flag = self.burst_mode_flag = 0
        self.data_label = []
        self.data_grap_horizontal_sizer = []
        data_sizer = []
        self.enable = []
        self.periodo_label = wx.StaticText(self, label="Period (ms)")
        self.periodo_edit = FloatSpin(
            self, value=frame.p.period_stream_out, min_val=1, max_val=65535,
            increment=100, digits=3)
        self.offset_label = wx.StaticText(self, label="Offset")
        self.offset_edit = FloatSpin(
            self, value=frame.p.offset_stream_out/1000, min_val=-4.0,
            max_val=4.0, increment=0.1, digits=3)
        self.amplitude_label = wx.StaticText(self, label="Amplitude")
        self.amplitude_edit = FloatSpin(
            self, value=frame.p.amplitude_stream_out/1000, min_val=0.001,
            max_val=4.0, increment=0.1, digits=3)
        # Sine
        box = wx.StaticBox(self, -1, 'Sine')
        self.data_label.append(box)
        self.data_grap_horizontal_sizer.append(
            wx.StaticBoxSizer(self.data_label[0], wx.HORIZONTAL))
        data_sizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.data_grap_horizontal_sizer[0].Add(data_sizer[0], 0, wx.ALL)
        # Square
        box = wx.StaticBox(self, -1, 'Square')
        self.data_label.append(box)
        self.data_grap_horizontal_sizer.append(
            wx.StaticBoxSizer(self.data_label[1], wx.HORIZONTAL))
        data_sizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.time_on_label = wx.StaticText(self, label="Time On")
        self.time_on_edit = FloatSpin(
            self, value=frame.p.time_on_stream_out, min_val=1, max_val=65535,
            increment=100, digits=3)
        self.data_grap_horizontal_sizer[1].Add(data_sizer[1], 0, wx.ALL)
        # SawTooth
        box = wx.StaticBox(self, -1, 'Sawtooth')
        self.data_label.append(box)
        self.data_grap_horizontal_sizer.append(
            wx.StaticBoxSizer(self.data_label[2], wx.HORIZONTAL))
        data_sizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.data_grap_horizontal_sizer[2].Add(data_sizer[2], 0, wx.ALL)
        # Triangle
        box = wx.StaticBox(self, -1, 'Triangle')
        self.data_label.append(box)
        self.data_grap_horizontal_sizer.append(
            wx.StaticBoxSizer(self.data_label[3], wx.HORIZONTAL))
        data_sizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.rise_time_label = wx.StaticText(self, label="Rise time")
        self.rise_time_edit = FloatSpin(
            self, value=frame.p.rise_time_stream_out, min_val=1, max_val=65535,
            increment=100, digits=3)
        self.data_grap_horizontal_sizer[3].Add(data_sizer[3], 0, wx.ALL)
        # Fixed potential
        box = wx.StaticBox(self, -1, 'Fixed potential')
        self.data_label.append(box)
        self.data_grap_horizontal_sizer.append(
            wx.StaticBoxSizer(self.data_label[4], wx.HORIZONTAL))
        data_sizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.data_grap_horizontal_sizer[4].Add(data_sizer[4], 0, wx.ALL)
        horizontal_sizer.Add(self.periodo_label, pos=(0, 0))
        horizontal_sizer.Add(self.periodo_edit, pos=(0, 1))
        horizontal_sizer.Add(self.offset_label, pos=(0, 2))
        horizontal_sizer.Add(self.offset_edit, pos=(0, 3))
        horizontal_sizer.Add(self.amplitude_label, pos=(0, 4))
        horizontal_sizer.Add(self.amplitude_edit, pos=(0, 5))
        for i in range(5):
            self.enable.append(wx.CheckBox(self, label='Enable', id=200+i))
            if(frame.p.waveform == i):
                self.enable[i].SetValue(1)
            if(frame.p.waveform == 4):
                self.amplitude_edit.Enable(False)
            data_sizer[i].Add(self.enable[i], 0, wx.ALL, border=10)
            self.Bind(wx.EVT_CHECKBOX, self.enable_event, self.enable[i])
        data_sizer[1].Add(self.time_on_label, 0, wx.ALL, border=10)
        data_sizer[1].Add(self.time_on_edit, 0, wx.ALL, border=10)
        data_sizer[3].Add(self.rise_time_label, 0, wx.ALL, border=10)
        data_sizer[3].Add(self.rise_time_edit, 0, wx.ALL, border=10)
        box_sizer.Add(self.data_grap_horizontal_sizer[0], pos=(0, 0))
        box_sizer.Add(self.data_grap_horizontal_sizer[1], pos=(0, 1))
        box_sizer.Add(self.data_grap_horizontal_sizer[2], pos=(1, 0))
        box_sizer.Add(self.data_grap_horizontal_sizer[3], pos=(1, 1))
        box_sizer.Add(self.data_grap_horizontal_sizer[4], pos=(0, 2))
        self.burst_mode = wx.CheckBox(self, label='Period (us)')
        self.Bind(wx.EVT_CHECKBOX, self.burst_mode_event, self.burst_mode)
        self.periodo_burst_edit = FloatSpin(
            self, value=frame.p.period_stream_out * 100, min_val=100,
            max_val=65535, increment=10, digits=0)
        self.periodo_burst_edit.Enable(False)
        horizontal_sizer.Add(self.burst_mode, pos=(1, 0))
        horizontal_sizer.Add(self.periodo_burst_edit, pos=(1, 1))
        self.submit = wx.Button(self, label="Submit")
        self.csv = wx.Button(self, label="Import CSV")
        self.Bind(wx.EVT_BUTTON, self.import_event, self.csv)
        self.Bind(wx.EVT_BUTTON, self.submit_event, self.submit)
        horizontal_sizer.Add(self.submit, pos=(2, 5))
        horizontal_sizer.Add(self.csv, pos=(2, 0))
        main_layout.Add(box_sizer, 0, wx.ALL, border=10)
        main_layout.Add(horizontal_sizer, 0, wx.ALL, border=10)
        self.SetSizerAndFit(main_layout)

    def burst_mode_event(self, event):
        if self.burst_mode.GetValue() is True:
            self.periodo_burst_edit.Enable(True)
            self.periodo_edit.Enable(False)
        else:
            self.periodo_burst_edit.Enable(False)
            self.periodo_edit.Enable(True)

    def import_event(self, event):
        self.directory_name = ''
        dlg = wx.FileDialog(
            self, "Choose a file", self.directory_name, "", "*.odq", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.file_name = dlg.GetFilename()
            self.directory_name = dlg.GetDirectory()
            with open(self.directory_name+"\\"+self.file_name, 'rb') as file:
                reader = csv.reader(file)
                self.csv_buffer = []
                try:
                    for index, row in enumerate(reader):
                        for i in range(len(row)):
                            self.csv_buffer.append(int(row[i]))
                except:
                    dlg = wx.MessageDialog(
                        self, "Error importing CSV", "Error",
                        wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
        # Calibration
        for i in range(len(self.csv_buffer)):
            self.csv_buffer[i] = calibration(int(round(self.csv_buffer[i])))
        dlg.Destroy()
        self.csv_flag = 1
        for i in range(4):
            self.enable[i].SetValue(0)
            self.enable[i].Enable(False)
        self.time_on_edit.Enable(False)
        self.rise_time_edit.Enable(False)
        self.amplitude_edit.Enable(False)
        self.offset_edit.Enable(False)

    def submit_event(self, event):
        if frame.daq.measuring:
            dlg = wx.MessageDialog(
                self, "openDAQ is measuring. Stop first.", "Stop first",
                wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        self.burst_mode_flag = self.burst_mode.GetValue()
        # Check values
        if self.csv_flag:
            self.period = self.periodo_edit.GetValue()
            self.EndModal(wx.ID_OK)
            return 0
        self.signal = -1
        for i in range(5):
            if(self.enable[i].IsChecked()):
                self.signal = i
                frame.p.waveform = i
        self.amplitude = self.amplitude_edit.GetValue() * 1000
        self.offset = self.offset_edit.GetValue() * 1000
        self.ton = self.time_on_edit.GetValue()
        self.time_rise = self.rise_time_edit.GetValue()
        if self.burst_mode.GetValue():
            self.period = self.periodo_burst_edit.GetValue() / 100
        else:
            self.period = self.periodo_edit.GetValue()
        if self.signal < 0:
            dlg = wx.MessageDialog(
                self, "At least one signal should be selected", "Error!",
                wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            return 0

        # waveform = 1 -> square
        cond_1 = (
            frame.p.waveform == 1 and (self.amplitude + self.offset > 4000 or (
                self.offset < -4000)))

        cond_2 = (
            frame.p.waveform != 1 and self.amplitude + abs(self.offset) > 4000)

        if cond_1 or cond_2:
                dlg = wx.MessageDialog(
                    self, "Amplitude or offset value out of range", "Error!",
                    wx.OK | wx.ICON_WARNING)

                dlg.ShowModal()
                dlg.Destroy()
                return 0
        if self.ton >= self.period and self.enable[1].IsChecked():
            dlg = wx.MessageDialog(
                self, "Time on can not be greater than period", "Error!",
                wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            return 0
        if self.time_rise >= self.period and self.enable[3].IsChecked():
            dlg = wx.MessageDialog(
                self, "Time rise can not be greater than period", "Error!",
                wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            return 0
        self.EndModal(wx.ID_OK)

    def enable_event(self, event):
        index_1 = event.GetEventObject().GetId()-200
        if(self.enable[index_1].IsChecked()):
            for i in range(5):
                if i != index_1:
                    self.enable[i].SetValue(0)
        if(self.enable[4].IsChecked()):
            self.amplitude_edit.Enable(False)
        else:
            self.amplitude_edit.Enable(True)


class ConfigDialog (wx.Dialog):
    def __init__(self, parent, index_1):
        # Call wxDialog's __init__ method
        wx.Dialog.__init__(self, parent, -1, 'Config', size=(200, 200))
        data_sizer = wx.GridBagSizer(hgap=5, vgap=5)
        main_layout = wx.BoxSizer(wx.HORIZONTAL)
        self.sample_list = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8")
        self.label_ch_1 = wx.StaticText(self, label="Ch+")
        data_sizer.Add(self.label_ch_1, pos=(0, 0))
        self.edit_ch_1 = wx.ComboBox(
            self, size=(95, -1), choices=self.sample_list,
            style=wx.CB_READONLY)
        selection = frame.p.ch_1[index_1] - 1
        self.edit_ch_1.SetSelection(selection)
        data_sizer.Add(self.edit_ch_1, pos=(0, 1))
        self.Bind(wx.EVT_COMBOBOX, self.edit_ch_1_change, self.edit_ch_1)
        if frame.hw_ver == "m":
            self.sample_list = ("AGND", "VREF", "A5", "A6", "A7", "A8")
        if frame.hw_ver == "s":
            self.sample_list = ("AGND", "A2")
        self.label_ch_2 = wx.StaticText(self, label="Ch-")
        data_sizer.Add(self.label_ch_2, pos=(1, 0))
        self.edit_ch_2 = wx.ComboBox(
            self, size=(95, -1), choices=self.sample_list,
            style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.edit_ch_2_change, self.edit_ch_2)
        selection = frame.p.ch_2[index_1]
        if frame.hw_ver == "m":
            if selection == 25:
                selection = 1
            else:
                if selection != 0:
                    selection -= 3
            self.edit_ch_2.SetSelection(selection)
        data_sizer.Add(self.edit_ch_2, pos=(1, 1))
        if frame.hw_ver == "m":
            self.sample_list = (
                "+-12 V", "+-4 V", "+-2 V", "+-0.4 V", "+-0.04 V")
            self.label_range = wx.StaticText(self, label="Range")
        if frame.hw_ver == "s":
            self.sample_list = (
                "x1", "x2", "x4", "x5", "x8", "x10", "x16", "x20")
            self.label_range = wx.StaticText(self, label="Multiplier")
        data_sizer.Add(self.label_range, pos=(2, 0))
        self.edit_range = wx.ComboBox(
            self, size=(95, -1), choices=self.sample_list,
            style=wx.CB_READONLY)
        self.edit_range.SetSelection(frame.p.range[index_1])
        data_sizer.Add(self.edit_range, pos=(2, 1))

        self.label_rate = wx.StaticText(self, label="Rate(ms)")
        data_sizer.Add(self.label_rate, pos=(0, 3))
        self.edit_rate = wx.TextCtrl(self, style=wx.TE_CENTRE)
        self.edit_rate.AppendText(str(frame.p.rate[index_1]))
        data_sizer.Add(self.edit_rate, pos=(0, 4))
        self.enable_extern = wx.CheckBox(self, label="Enable extern")
        self.Bind(wx.EVT_CHECKBOX, self.extern_mode_event, self.enable_extern)
        self.enable_extern.SetValue(False)
        data_sizer.Add(self.enable_extern, pos=(0, 5))
        self.label_samples = wx.StaticText(self, label="Samples per point")
        data_sizer.Add(self.label_samples, pos=(1, 3))
        self.edit_samples = wx.TextCtrl(self, style=wx.TE_CENTRE)
        self.edit_samples.AppendText(str(frame.p.samples[index_1]))
        data_sizer.Add(self.edit_samples, pos=(1, 4))
        self.sample_list = (
            "Continuous", "Single run: 20", "Single run: 40",
            "Single run: 100")
        self.label_mode = wx.StaticText(self, label="Mode")
        data_sizer.Add(self.label_mode, pos=(2, 3))
        self.edit_mode = wx.ComboBox(
            self, size=(95, -1), choices=self.sample_list,
            style=wx.CB_READONLY)
        self.edit_mode.SetSelection(frame.p.mode[index_1])
        data_sizer.Add(self.edit_mode, pos=(2, 4))
        self.ok_button = wx.Button(self, label="Confirm")
        self.Bind(wx.EVT_BUTTON, self.confirm_event, self.ok_button)
        data_sizer.Add(self.ok_button, pos=(3, 5))
        main_layout.Add(data_sizer, 1, wx.EXPAND | wx.ALL, 20)
        self.SetSizerAndFit(main_layout)
        self.edit_ch_1_change(0)
        if frame.hw_ver == "s":
            if selection != 0:
                selection = 1
            self.edit_ch_2.SetSelection(selection)
            if selection != 0:
                self.edit_range.SetSelection(frame.p.range[index_1])
                self.edit_range.Enable(True)
                self.label_range.Enable(True)

    def extern_mode_event(self, event):
        self.edit_rate.Enable(not self.enable_extern.GetValue())

    def confirm_event(self, event):
        if self.edit_rate.GetLineText(0).isdigit():
            self.rate = int(self.edit_rate.GetLineText(0))
            print "RATE1", self.rate
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
        string = self.edit_samples.GetLineText(0)
        if string.isdigit():
            self.samples = int(self.edit_samples.GetLineText(0))
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

    def edit_ch_2_change(self, event):
        if frame.hw_ver == "m":
            return
        value = self.edit_ch_2.GetValue()
        if value == "AGND":
            self.edit_range.SetValue("x1")
            self.edit_range.Enable(False)
            self.label_range.Enable(False)
        else:
            self.edit_range.Enable(True)
            self.label_range.Enable(True)

    def edit_ch_1_change(self, event):
        if frame.hw_ver == "m":
            return
        value = self.edit_ch_1.GetValue()
        self.edit_ch_2.Clear()
        self.edit_ch_2.Append("AGND")
        if (int(value[1]) % 2) == 0:
            self.edit_ch_2.Append("A" + str(int(value[1])-1))
        else:
            self.edit_ch_2.Append("A" + str(int(value[1])+1))
        self.edit_ch_2.SetSelection(0)
        self.edit_range.SetSelection(0)
        self.edit_range.Enable(False)
        self.label_range.Enable(False)


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
        self.enable_check = []
        # Configuration save
        self.ch_1 = [1, 1, 1, 1]
        self.ch_2 = [0, 0, 0, 0]
        if self.frame.hw_ver == "m":
            self.range = [1, 1, 1, 1]
        if self.frame.hw_ver == "s":
            self.range = [0, 0, 0, 0]
        self.rate = [100, 100, 100, 100]
        self.samples = [20, 20, 20, 20]
        self.mode = [0, 0, 0, 0]
        self.num_point = [0, 0, 0, 0]
        self.extern_flag = [0, 0, 0, 0]
        self.burst_mode_stream_out = self.waveform = 0
        self.amplitude_stream_out = self.offset_stream_out = 1000
        self.time_on_stream_out = self.rise_time_stream_out = 5
        self.period_stream_out = 15
        self.configure = []
        self.color = []
        self.data_label = []
        self.data_grap_horizontal_sizer = []
        data_sizer = []
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        datas_sizer = wx.BoxSizer(wx.VERTICAL)
        grap_horizontal_sizer = wx.BoxSizer(wx.VERTICAL)
        plot_sizer = wx.BoxSizer(wx.VERTICAL)
        horizontal_sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        for i in range(4):
            box = wx.StaticBox(self, -1, 'Experiment %d' % (i+1))
            self.data_label.append(box)
            self.data_grap_horizontal_sizer.append(
                wx.StaticBoxSizer(self.data_label[i], wx.HORIZONTAL))
            data_sizer.append(wx.BoxSizer(wx.HORIZONTAL))
            self.enable_check.append(wx.CheckBox(self, label="Enable"))
            self.enable_check[i].SetValue(False)
            data_sizer[i].Add(self.enable_check[i], 0, wx.ALL, border=10)
            self.configure.append(wx.Button(self, id=i+100, label="Configure"))
            self.Bind(wx.EVT_BUTTON, self.configure_event, self.configure[i])
            data_sizer[i].Add(self.configure[i], 0, wx.ALL, border=10)
            self.color.append(wx.StaticText(self, label="..........."))
            if i < 3:
                color = (255 * (i == 0), 255 * (i == 1), 255 * (i == 2))
            else:
                color = (0, 0, 0)
            self.color[i].SetForegroundColour(color)  # Set text color
            self.color[i].SetBackgroundColour(color)  # Set text back color
            data_sizer[i].Add(self.color[i], 0, wx.ALL, border=10)
            self.data_grap_horizontal_sizer[i].Add(data_sizer[i], 0, wx.ALL)
            datas_sizer.Add(
                self.data_grap_horizontal_sizer[i], 0, wx.ALL, border=10)
        # Stream out panel
        box = wx.StaticBox(self, -1, 'Waveform generator')
        self.data_label.append(box)
        self.data_grap_horizontal_sizer.append(
            wx.StaticBoxSizer(self.data_label[4], wx.HORIZONTAL))
        data_sizer.append(wx.BoxSizer(wx.HORIZONTAL))
        self.enable_check.append(wx.CheckBox(self, label="Enable"))
        self.Bind(wx.EVT_CHECKBOX, self.stream_enable, self.enable_check[4])
        self.enable_check[4].SetValue(False)
        data_sizer[4].Add(self.enable_check[4], 0, wx.ALL, border=10)
        self.configure.append(wx.Button(self, id=400, label="Configure"))
        self.Bind(wx.EVT_BUTTON, self.configure_stream, self.configure[4])
        data_sizer[4].Add(self.configure[4], 0, wx.ALL, border=10)
        self.data_grap_horizontal_sizer[4].Add(data_sizer[4], 0, wx.ALL)
        datas_sizer.Add(
            self.data_grap_horizontal_sizer[4], 0, wx.ALL, border=10)
        # Export
        box = wx.StaticBox(self, -1, 'Export graphics')
        self.export_label = box
        self.export_sizer = wx.StaticBoxSizer(self.export_label, wx.HORIZONTAL)
        self.png = wx.Button(self, label="As PNG file...")
        self.Bind(wx.EVT_BUTTON, self.save_as_png_event, self.png)
        self.csv = wx.Button(self, label="As CSV file...")
        self.Bind(wx.EVT_BUTTON, self.save_as_csv_event, self.csv)
        horizontal_sizer_2.Add(self.png, 0, wx.ALL)
        horizontal_sizer_2.Add(self.csv, 0, wx.ALL)
        self.export_sizer.Add(horizontal_sizer_2, 0, wx.ALL)
        self.button_play = wx.Button(self, label="Play")
        self.Bind(wx.EVT_BUTTON, self.play_event, self.button_play)
        self.button_stop = wx.Button(self, label="Stop")
        self.Bind(wx.EVT_BUTTON, self.stop_event, self.button_stop)
        self.button_stop.Enable(False)
        self.stopping_label = wx.StaticText(self, label="")
        datas_sizer.Add(self.export_sizer, 0, wx.ALL, border=10)
        grap_horizontal_sizer.Add(datas_sizer, 0, wx.ALL)
        grap_horizontal_sizer.Add(self.button_play, 0, wx.CENTRE, border=5)
        grap_horizontal_sizer.Add(self.button_stop, 0, wx.CENTRE, border=5)
        grap_horizontal_sizer.Add(self.stopping_label, 0, wx.CENTRE, border=5)
        self.figure = Figure(facecolor='#ece9d8')
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.axes.set_xlabel("Time (s)", fontsize=12)
        self.axes.set_ylabel("Voltage (mV)", fontsize=12)
        self.axes.autoscale(False)
        self.canvas.SetInitialSize(size=(600, 600))
        self.add_toolbar()
        self.cid_update = self.canvas.mpl_connect(
            'motion_notify_event', self.update_status_bar)
        plot_sizer.Add(self.toolbar, 0, wx.CENTER)
        plot_sizer.Add(self.canvas, 0, wx.ALL)
        main_sizer.Add(grap_horizontal_sizer, 0, wx.ALL)
        main_sizer.Add(plot_sizer, 0, wx.ALL)
        self.SetSizerAndFit(main_sizer)

        #Create publisher receiver
        Publisher().subscribe(self.refresh, "refresh")
        Publisher().subscribe(self.stop, "stop")

    def refresh(self, msg):
        if(self.toolbar.mode == "pan/zoom"):
            return
        if(self.toolbar.mode == "zoom rect"):
            return
        self.canvas.mpl_disconnect(frame.p.cid_update)
        try:
            self.axes.clear()
            self.axes.autoscale(False)
            self.axes.grid(color='gray', linestyle='dashed')
            for i in range(4):
                if(len(
                    comunication_thread.y[i]) ==
                        len(comunication_thread.x[i])):
                            self.axes.plot(
                                comunication_thread.y[i],
                                comunication_thread.x[i],
                                color=frame.colors[i])
            self.canvas.draw()
            self.axes.autoscale(True)
        except:
            print "Error trying to paint"
        self.cid_update = self.canvas.mpl_connect(
            'motion_notify_event', self.update_status_bar)

    def stop(self, event):
        frame.p.axes.cla()
        frame.p.axes.grid(color='gray', linestyle='dashed')
        for i in range(4):
            frame.p.axes.plot(
                comunication_thread.y[i],
                comunication_thread.x[i], color=frame.colors[i])
        frame.p.canvas.draw()
        frame.daq.flush()
        for i in range(4):
            if frame.p.enable_check[i].GetValue():
                try:
                    frame.daq.destroy_channel(i+1)
                except:
                    frame.daq.flush()
                    print "Error trying to destroy channel"
                    frame.daq.close()
                    frame.daq.open()
        frame.p.stopping_label.SetLabel("")
        frame.p.button_play.Enable(True)

    def update_status_bar(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            frame.status_bar.SetStatusText(
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
        # self.main_sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()

    def save_as_png_event(self, event):
        self.directory_name = ''
        dlg = wx.FileDialog(
            self, "Choose a file", self.directory_name, "", "*.png", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.file_name = dlg.GetFilename()
            self.directory_name = dlg.GetDirectory()
            self.figure.savefig(self.directory_name+"\\"+self.file_name)
        dlg.Destroy()

    def save_as_csv_event(self, event):
        self.directory_name = ''
        dlg = wx.FileDialog(
            self, "Choose a file", self.directory_name, "", "*.odq", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.file_name = dlg.GetFilename()
            self.directory_name = dlg.GetDirectory()
            for j in range(4):
                if self.enable_check[j].IsChecked():
                    with open(
                        self.directory_name + "\\" + str(j) + self.file_name,
                            'wb') as file:
                                spamwriter = csv.writer(
                                    file, quoting=csv.QUOTE_MINIMAL)
                                for i in range(len(comunication_thread.x[j])):
                                    spamwriter.writerow(
                                        [comunication_thread.x[j][i],
                                            comunication_thread.y[j][i]])
        dlg.Destroy()

    def configure_stream(self, event):
        dlg = StreamDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            self.burst_mode_stream_out = dlg.burst_mode_flag
            if dlg.csv_flag:
                self.buffer = dlg.csv_buffer[:140]
                self.interval = int(dlg.period/(len(self.buffer)))
            else:
                self.period_stream_out = dlg.period
                self.amplitude_stream_out = dlg.amplitude
                self.offset_stream_out = dlg.offset
                self.signal_stream_out = dlg.signal
                self.rise_time_stream_out = dlg.time_rise
                self.time_on_stream_out = dlg.ton
                self.signal_create()
        dlg.Destroy()
        self.stream_enable(0)

    def stream_enable(self, event):
        if self.enable_check[4].IsChecked():
            if self.burst_mode_stream_out:
                for i in range(3):
                    self.enable_check[i].SetValue(0)
                    self.enable_check[i].Enable(False)
            self.enable_check[3].SetValue(0)
            self.enable_check[3].Enable(False)
        else:
            for i in range(4):
                    self.enable_check[i].SetValue(0)
                    self.enable_check[i].Enable(True)

    def configure_event(self, event):
        wx.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        index_1 = event.GetEventObject().GetId()-100
        dlg = ConfigDialog(self, index_1)
        if dlg.ShowModal() == wx.ID_OK:
            self.ch_1[index_1] = dlg.edit_ch_1.GetCurrentSelection()
            self.ch_2[index_1] = dlg.edit_ch_2.GetCurrentSelection()
            self.range[index_1] = dlg.edit_range.GetCurrentSelection()
            self.ch_1[index_1] += 1
            if frame.hw_ver == "m":
                if self.ch_2[index_1] == 1:
                    self.ch_2[index_1] = 25
                elif self.ch_2[index_1] > 1:
                    self.ch_2[index_1] += 3
            if frame.hw_ver == "s":
                if self.ch_2[index_1] > 0:
                    value = self.ch_1[index_1]
                    if value % 2:
                        self.ch_2[index_1] = value + 1
                    else:
                        self.ch_2[index_1] = value - 1
            if dlg.enable_extern.GetValue() is True:
                self.rate[index_1] = int(dlg.edit_rate.GetLineText(0))
                self.extern_flag[index_1] = 1
            else:
                self.rate[index_1] = int(dlg.edit_rate.GetLineText(0))
                self.extern_flag[index_1] = 0
            self.samples[index_1] = int(dlg.edit_samples.GetLineText(0))
            self.mode[index_1] = dlg.edit_mode.GetCurrentSelection()
            if self.mode[index_1] == 0:
                self.num_point[index_1] = self.mode[index_1] = 0
            else:
                self.num_point[index_1] = 20 * self.mode[index_1]
                if self.mode[index_1] == 3:
                    self.num_point[index_1] = 100
                self.mode[index_1] = 1
            dlg.Destroy()

    def play_event(self, event):
        self.channel = []
        for i in range(4):
            if self.enable_check[i].GetValue():
                frame.channel_state[i] = 1
                self.channel.append(
                    [self.ch_1[i], self.ch_2[i], self.rate[i], self.range[i]])
                if self.rate[i] < 10:
                    self.num_point[i] = 30000
                    self.mode[i] = 1
                if self.extern_flag[i] == 1:
                    frame.daq.create_external(i+1, 0)
                else:
                    frame.daq.create_stream(i+1, self.rate[i])
                frame.daq.setup_channel(
                    i+1, self.num_point[i], self.mode[i])
                frame.daq.conf_channel(
                    i+1, 0, self.ch_1[i], self.ch_2[i], self.range[i],
                    self.samples[i])  # Analog input
        if self.enable_check[4].GetValue():
            if self.burst_mode_stream_out:
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
            x_length = 20
            num_buffers = len(self.buffer) / x_length
            for i in range(num_buffers):
                self.init = i * x_length
                self.end = self.init + x_length
                self.inter_buffer = self.buffer[self.init:self.end]
                frame.daq.load_signal(self.inter_buffer, self.init)
            self.init = num_buffers * x_length
            self.inter_buffer = self.buffer[self.init:]
            if len(self.inter_buffer) > 0:
                frame.daq.load_signal(self.inter_buffer, self.init)
        self.button_play.Enable(False)
        self.button_stop.Enable(True)
        timer_thread.start_drawing()
        comunication_thread.restart()

    def stop_event(self, event):
        self.button_stop.Enable(False)
        comunication_thread.stop()
        timer_thread.stop()

    def signal_create(self):
        if self.signal_stream_out == 0:
            # Sine
            if self.period_stream_out < 140:
                self.interval = 1
            else:
                self.interval = int(self.period_stream_out/140)
                self.interval += 1
            self.t = np.arange(0, self.period_stream_out, self.interval)
            self.buffer = np.sin(
                2 * np.pi / self.period_stream_out * self.t) * (
                self.amplitude_stream_out)
            for i in range(len(self.buffer)):
                self.buffer[i] = self.buffer[i]+self.offset_stream_out
        if self.signal_stream_out == 1:
            # Square
            self.buffer = []
            self.interval = fractions.gcd(
                self.period_stream_out, self.time_on_stream_out)
            self.points_on = int(self.time_on_stream_out / self.interval)
            self.points = int(self.period_stream_out / self.interval)
            for i in range(self.points_on):
                self.buffer.append(
                    self.amplitude_stream_out+self.offset_stream_out)
            for i in range(self.points-self.points_on):
                self.buffer.append(self.offset_stream_out)
        if self.signal_stream_out == 2:
            # Sawtooth
            if self.period_stream_out < 140:
                self.interval = 1
                self.points = int(self.period_stream_out)
                self.increment = int(
                    self.amplitude_stream_out/self.period_stream_out)
            else:
                self.interval = int(self.period_stream_out/140)
                self.interval += 1
                self.points = int(self.period_stream_out/self.interval)
                self.increment = int(self.amplitude_stream_out/self.points)
            self.init = int(self.offset_stream_out)
            self.buffer = []
            for i in range(self.points):
                self.value = self.init
                self.value += (self.increment * i)
                self.buffer.append(self.value)
        if self.signal_stream_out == 3:
            # Triangle
            if self.period_stream_out < 140:
                self.interval = 1
                self.points = int(self.rise_time_stream_out)
                self.increment = int(
                    self.amplitude_stream_out/self.rise_time_stream_out)
            else:
                self.relation = int(
                    self.period_stream_out/self.rise_time_stream_out)
                self.points = int(140/self.relation)  # Ideal n points
                self.interval = int(self.rise_time_stream_out/self.points)
                self.interval += 1
                self.points = int(self.rise_time_stream_out/self.interval)
                self.increment = int(self.amplitude_stream_out/self.points)
            self.init = int(self.offset_stream_out)
            self.buffer = []
            for i in range(self.points):
                self.value = self.init
                self.value += (self.increment * i)
                self.buffer.append(self.value)
            if self.period_stream_out < 140:
                self.points = int(
                    self.period_stream_out-self.rise_time_stream_out)
                self.increment = int(
                    self.amplitude_stream_out /
                    (self.period_stream_out-self.rise_time_stream_out))
            else:
                self.time = int(
                    self.period_stream_out-self.rise_time_stream_out)
                self.points = 140-self.points  # Ideal n points
                self.interval = int(self.time / self.points)
                self.interval += 1
                self.points = int(self.time / self.interval)
                self.increment = int(self.amplitude_stream_out / self.points)
            self.init = int(self.offset_stream_out + self.amplitude_stream_out)
            for i in range(self.points):
                self.value = self.init - (self.increment * i)
                self.buffer.append(self.value)
        if self.signal_stream_out == 4:
            # Continuous
            self.buffer = []
            self.interval = self.period_stream_out
            self.buffer.append(self.offset_stream_out)
        # Calibration
        for i in range(len(self.buffer)):
            dac_value = self.buffer[i]
            info = self.frame.daq.get_info()
            if info[1] < 110:
                self.buffer[i] = dac_value
            else:
                self.buffer[i] = calibration(int(round(dac_value)))
        if len(self.buffer) >= 140:
            self.buffer = self.buffer[:140]


class MainFrame(wx.Frame):
    def __init__(self, com_port):
        wx.Frame.__init__(
            self, None, title="EasyDAQ", style=wx.DEFAULT_FRAME_STYLE &
            ~(wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        self.colors = 'r', 'g', 'b', 'k'
        self.daq = DAQ(com_port)
        self.hw_ver = self.daq.hw_ver
        icon = wx.Icon("../resources/icon64.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetFieldsCount(2)
        info = self.daq.get_info()
        hw_ver = "[M]" if info[0] == 1 else "[S]"
        fw_ver = (
            str(info[1] / 100) + "." + str((info[1] / 10) % 10) + "." +
            str(info[1] % 10))
        self.status_bar.SetStatusText("H:%s V:%s" % (hw_ver, fw_ver), 0)
        self.channel_state = [0, 0, 0, 0]
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.error_dic = {'size': 0}
        self.error_info = {'Failure data size': 0}
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

    def set_voltage(self, voltage):
        self.daq.set_analog(voltage)

    def on_close(self, event):
        dlg = wx.MessageDialog(
            self, "Do you really want to close this application?",
            "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            comunication_thread.stop_thread()
            timer_thread.stop_thread()
            self.daq.close()
            self.Destroy()

    def show_error_parameters(self):
        dlg = wx.MessageDialog(
            self, "Verify parameters", "Error!", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()

    def stop_channel(self, number):
        self.channel_state[number] = suma = 0
        for i in range(3):
            suma += self.channel_state[i]
        if suma == 0:
            self.p.button_play.Enable(True)
            self.p.button_stop.Enable(False)
            comunication_thread.stop()
            timer_thread.stop()


class InitDlg(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(
            self, None, title="EasyDAQ", style=(wx.STAY_ON_TOP | wx.CAPTION))
        self.horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        self.gauge = wx.Gauge(self, range=100, size=(100, 15))
        self.horizontal_sizer.Add(self.gauge, wx.EXPAND)
        avaiable_ports = scan(num_ports=255, verbose=False)
        self.sample_list = []
        if len(avaiable_ports) != 0:
            for n, nombre in avaiable_ports:
                self.sample_list.append(nombre)
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
            daq = DAQ(self.sample_list[port_number])
            try:
                daq.get_info()
                dlg = wx.MessageDialog(
                    self, "EasyDAQ started", "Continue",
                    wx.OK | wx.ICON_QUESTION)
                dlg.ShowModal()
                dlg.Destroy()
                self.port = self.sample_list[port_number]
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

    def cancel_event(self, event):
        self.port = 0
        self.EndModal(0)


def calibration(value):
    if not -4096 <= value < 4096:
        raise ValueError('DAQ voltage out of range')
    value *= frame.daq.dac_gain
    if frame.hw_ver == "s":
        value *= 2
    data = (value / 1000.0 + frame.daq.dac_offset + 4096) * 2
    if frame.hw_ver == "s" and data < 0:
        data = 0
    return data


class MyApp(wx.App):
    def OnInit(self):
        dial = InitDlg()
        ret = dial.ShowModal()
        dial.Destroy()
        self.com_port = dial.port
        self.connected = ret
        return True

if __name__ == "__main__":
    comunication_thread = ComThread()
    comunication_thread.start()
    timer_thread = TimerThread()
    timer_thread.start()
    app = MyApp(False)
    if app.connected:
        frame = MainFrame(app.com_port)
        frame.Centre()
        frame.Show()
        app.MainLoop()
    else:
        comunication_thread.stop_thread()
        timer_thread.stop_thread()
