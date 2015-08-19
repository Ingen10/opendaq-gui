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
import serial
from serial.tools.list_ports import comports
from wx.lib.agw.floatspin import FloatSpin
from wx.lib.pubsub import setuparg1
from wx.lib.pubsub import pub

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
import csv

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
            #select which Operating System is current installed
            plt = sys.platform
            if plt == "linux2":
                port = "/dev/ttyUSB%d" % i
                s = serial.Serial(port)
            elif plt == "win32":
                s = serial.Serial(i)
            if verbose:
                print "OK --> %s" % s.portstr
            #-- If no errors, add port name to the list
            serial_dev.append((i, s.portstr))
            #-- Close port
            s.close()
        #-- Ignore possible errors
        except:
            if verbose:
                print "NO"
            pass
    #-- Return list of serial devices
    return serial_dev


class ComThread (threading.Thread):
    def __init__(self, frame):
        self.frame = frame
        threading.Thread.__init__(self)
        self.running = self.running_thread = 1
        self.x = []
        self.y = []
        self.data_packet = []
        self.delay = 0.001

    def config(self, ch_1, ch_2, rangeV, rate):
        self.frame.daq.conf_adc(ch_1+1, ch_2, rangeV, 20)
        self.delay = rate / 1000.0

    def stop(self):
        self.running = 0
        self.frame.daq.set_led(1)

    def stop_thread(self):
        self.running_thread = 0

    def restart(self):
        self.running = 1
        self.x = []
        self.y = []
        self.data_packet = []

    def run(self):
        self.running = 1
        self.x = []
        self.y = []
        self.data_packet = []
        while self.running_thread:
            time.sleep(1)
            time_to_repaint = 0
            time_to_capture = self.delay
            while self.running:
                time.sleep(0.1)
                time_to_repaint += 0.1
                time_to_capture += 0.1

                if time_to_capture >= self.delay:
                    time_to_capture = 0
                    data = self.frame.daq.read_analog()
                    if self.frame.page_1.hw_ver == 2:
                        page_1 = self.frame.page_1
                        data /= (
                            page_1.multiplier_list[self.frame.page_1.range])
                    self.frame.page_1.data_packet.append(data)
                    self.frame.page_1.x.append(float(data))
                    self.frame.page_1.y.append(
                        float((len(self.frame.page_1.x)-1) * (
                            self.frame.page_1.rate / 1000)))

                if time_to_repaint >= 0.2:
                    time_to_repaint = 0
                    wx.CallAfter(pub.sendMessage, "newdata", data)


class TimerThread (threading.Thread):
    def __init__(self, frame):
        self.frame = frame
        threading.Thread.__init__(self)
        self.running = 1
        self.delay = 0.25
        self.counter_flag = self.capture_flag = self.encoder_flag = 0

    def stop(self):
        self.counter_flag = self.capture_flag = self.encoder_flag = 0

    def start_counter(self):
        self.counter_flag = 1
        self.capture_flag = self.encoder_flag = 0

    def start_capture(self):
        self.counter_flag = self.encoder_flag = 0
        self.capture_flag = 1

    def start_encoder(self):
        self.counter_flag = self.capture_flag = 0
        self.encoder_flag = 1

    def stop_thread(self):
        self.running = 0

    def run(self):
        self.running = 1
        while self.running:
            time.sleep(self.delay)

            if self.counter_flag:
                counter = self.frame.daq.get_counter(0)
                wx.CallAfter(pub.sendMessage, "counter_value", counter)
            if self.capture_flag:
                mode, capture = (
                    self.frame.daq.get_capture(
                        self.frame.page_4.rb.GetSelection()))
                wx.CallAfter(pub.sendMessage, "capture_value", capture)
            if self.encoder_flag:
                encoder = self.frame.daq.get_encoder()[0]
                wx.CallAfter(pub.sendMessage, "encoder_value", encoder)


class MyCustomToolbar(NavigationToolbar2Wx):
    ON_CUSTOM_LEFT = wx.NewId()
    ON_CUSTOM_RIGHT = wx.NewId()

    def __init__(self, plot_canvas):
        # create the default toolbar
        NavigationToolbar2Wx.__init__(self, plot_canvas)
        # remove the unwanted button
        delete_array = (8, 7, 2, 1)
        for i in delete_array:
            self.DeleteToolByPos(i)


class PageOne(wx.Panel):
    def __init__(self, parent, hw_ver, frame):
        self.frame = frame
        self.multiplier_list = [1, 2, 4, 5, 8, 10, 16, 20]
        wx.Panel.__init__(self, parent)
        self.hw_ver = hw_ver
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        grid = wx.GridBagSizer(hgap=5, vgap=5)
        grid_2 = wx.GridBagSizer(hgap=5, vgap=5)
        horizontal_sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        horizontal_sizer = wx.BoxSizer(wx.VERTICAL)
        plot_sizer = wx.BoxSizer(wx.VERTICAL)
        self.input_label = wx.StaticBox(self, -1, 'Analog input')
        self.input_sizer = wx.StaticBoxSizer(self.input_label, wx.HORIZONTAL)
        self.sample_list = []
        for i in range(1, 9):
            self.sample_list.append("A" + str(i))
        self.label_ch_1 = wx.StaticText(self, label="Ch+")
        grid.Add(self.label_ch_1, pos=(0, 0))
        self.edit_ch_1 = wx.ComboBox(
            self, size=(95, -1), choices=self.sample_list,
            style=wx.CB_READONLY)
        self.edit_ch_1.SetSelection(0)
        grid.Add(self.edit_ch_1, pos=(0, 1))
        if self.hw_ver == 1:
            self.sample_list = ("AGND", "VREF", "A5", "A6", "A7", "A8")
        else:
            if self.hw_ver == 2:
                self.sample_list = ("AGND", "A2")
        self.label_ch_2 = wx.StaticText(self, label="Ch-")
        grid.Add(self.label_ch_2, pos=(1, 0))
        self.edit_ch_2 = wx.ComboBox(
            self, size=(95, -1), choices=self.sample_list,
            style=wx.CB_READONLY)
        self.edit_ch_2.SetSelection(0)
        grid.Add(self.edit_ch_2, pos=(1, 1))
        self.Bind(wx.EVT_COMBOBOX, self.edit_ch_1_change, self.edit_ch_1)
        self.Bind(wx.EVT_COMBOBOX, self.edit_ch_2_change, self.edit_ch_2)
        if self.hw_ver == 1:
            self.sample_list = (
                "+-12 V", "+-4 V", "+-2 V", "+-0.4 V", "+-0.04 V")
            self.label_range = wx.StaticText(self, label="Range")
        else:
            if self.hw_ver == 2:
                self.sample_list = (
                    "x1", "x2", "x4", "x5", "x8", "x10", "x16", "x20")
                self.label_range = wx.StaticText(self, label="Multiplier")
        grid.Add(self.label_range, pos=(2, 0))
        self.edit_range = wx.ComboBox(
            self, size=(95, -1), choices=self.sample_list,
            style=wx.CB_READONLY)
        self.edit_range.SetSelection(0)
        grid.Add(self.edit_range, pos=(2, 1))
        if self.hw_ver == 2:
            self.edit_range.Enable(False)

        self.label_rate = wx.StaticText(self, label="Rate(s)")
        grid.Add(self.label_rate, pos=(3, 0))
        self.edit_rate = (FloatSpin(
            self, value=1, min_val=0.1, max_val=65.535, increment=0.1,
            digits=1))
        grid.Add(self.edit_rate, pos=(3, 1))
        self.button_play = wx.Button(self, label="Play", size=(95, 25))
        self.Bind(wx.EVT_BUTTON, self.play_event, self.button_play)
        self.button_stop = wx.Button(self, label="Stop", size=(95, 25))
        self.Bind(wx.EVT_BUTTON, self.stop_event, self.button_stop)
        self.button_stop.Enable(False)
        grid.Add(self.button_play, pos=(4, 0))
        grid.Add(self.button_stop, pos=(4, 1))
        self.label_value = wx.StaticText(self, label="Last value (V)")
        grid.Add(self.label_value, pos=(5, 0))
        self.input_value = wx.TextCtrl(
            self, style=wx.TE_READONLY, size=(95, 25))
        grid.Add(self.input_value, pos=(5, 1))
        self.input_sizer.Add(grid, 0, wx.ALL, border=10)
        self.output_label = wx.StaticBox(self, -1, 'Analog output')
        self.output_sizer = wx.StaticBoxSizer(self.output_label, wx.HORIZONTAL)
        if hw_ver == 1:
            self.edit_value = FloatSpin(
                self, value=0, min_val=-4.0, max_val=4.0, increment=0.1,
                digits=3)
        elif hw_ver == 2:
            self.edit_value = FloatSpin(
                self, value=0, min_val=0, max_val=4.0, increment=0.1,
                digits=3)
        self.Bind(
            wx.lib.agw.floatspin.EVT_FLOATSPIN, self.slider_change,
            self.edit_value)
        self.lblDAC = wx.StaticText(self, label="DAC value (V)")
        grid_2.Add(self.lblDAC, pos=(0, 0))
        grid_2.Add(self.edit_value, pos=(0, 3))
        self.output_sizer.Add(grid_2, 0, wx.ALL, border=10)
        self.export_label = wx.StaticBox(self, -1, 'Export')
        self.export_sizer = wx.StaticBoxSizer(self.export_label, wx.HORIZONTAL)
        self.png = wx.Button(self, label="As PNG file...", size=(98, 25))
        self.Bind(wx.EVT_BUTTON, self.save_as_png_event, self.png)
        self.csv = wx.Button(self, label="As CSV file...", size=(98, 25))
        self.Bind(wx.EVT_BUTTON, self.save_as_csv_event, self.csv)
        horizontal_sizer_2.Add(self.png, 0, wx.ALL)
        horizontal_sizer_2.Add(self.csv, 0, wx.ALL)
        self.export_sizer.Add(horizontal_sizer_2, 0, wx.ALL, border=10)
        self.figure = Figure(facecolor='#ece9d8')
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.axes.set_xlabel("Time (s)", fontsize=12)
        self.axes.set_ylabel("Voltage (mV)", fontsize=12)
        self.canvas.SetInitialSize(size=(600, 600))
        self.add_toolbar()

        self.cidUpdate = self.canvas.mpl_connect(
            'motion_notify_event', self.UpdateStatusBar)
        plot_sizer.Add(self.toolbar, 0, wx.CENTER)
        plot_sizer.Add(self.canvas, 0, wx.ALL)
        horizontal_sizer.Add(self.input_sizer, 0, wx.CENTRE)
        horizontal_sizer.Add(self.output_sizer, 0, wx.EXPAND)
        horizontal_sizer.Add(self.export_sizer, 0, wx.EXPAND)
        main_sizer.Add(horizontal_sizer, 0, wx.ALL, border=10)
        main_sizer.Add(plot_sizer, 0, wx.ALL)
        self.SetSizerAndFit(main_sizer)

        self.data_packet = []
        self.x = []
        self.y = []

        # Create a publisher receiver
        pub.subscribe(self.new_data, "newdata")
        pub.subscribe(self.clear_canvas, "clearcanvas")

    def new_data(self, msg):
        data = msg.data
        if isinstance(msg.data, float):
                self.input_value.Clear()
                self.input_value.AppendText(str(data))
                if(self.toolbar.mode == "pan/zoom"):
                    return
                if(self.toolbar.mode == "zoom rect"):
                    return
                self.canvas.mpl_disconnect(self.frame.page_1.cidUpdate)
                self.axes.cla()
                self.axes.grid(color='gray', linestyle='dashed')
                self.axes.plot(self.y, self.x)
                self.canvas.draw()
                self.cidUpdate = self.frame.page_1.canvas.mpl_connect(
                    'motion_notify_event', self.frame.page_1.UpdateStatusBar)

    def clear_canvas(self, msg):
        self.input_value.Clear()
        self.axes.cla()
        self.axes.grid(color='gray', linestyle='dashed')
        self.axes.plot(self.y, self.x)
        self.canvas.draw()

    def UpdateStatusBar(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            self.frame.status_bar.SetStatusText(
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
        #self.main_sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
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
            with open(self.directory_name+"\\"+self.file_name, 'wb') as file:
                spamwriter = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
                for i in range(len(self.frame.comunication_thread.data)):
                    spamwriter.writerow(
                        [self.frame.comunication_thread.x[i],
                            self.frame.comunication_thread.y[i]])
        dlg.Destroy()

    def zoom_up(self, event):
        pass

    def play_event(self, event):
        self.data_packet = []
        self.x = []
        self.y = []
        self.ch_1 = self.edit_ch_1.GetCurrentSelection()
        self.ch_2 = self.edit_ch_2.GetCurrentSelection()
        self.range = self.edit_range.GetCurrentSelection()
        self.rate = self.edit_rate.GetValue() * 1000
        self.edit_rate.SetValue(self.edit_rate.GetValue())
        self.edit_value.SetValue(self.edit_value.GetValue())
        if self.ch_1 == -1:
            self.frame.show_error_parameters()
            return
        if self.ch_2 == -1:
            self.frame.show_error_parameters()
            return
        if self.range == -1:
            self.frame.show_error_parameters()
            return
        if self.hw_ver == 2 and self.ch_2 == 1:
            self.ch_2 = self.edit_ch_2.GetValue()
            self.ch_2 = self.ch_2[1]
        if self.hw_ver == 1:
            if self.ch_2 == 1:
                self.ch_2 = 25
            elif self.ch_2 > 1:
                self.ch_2 += 3
        self.frame.comunication_thread.config(
            self.ch_1, int(self.ch_2), self.range, self.rate)
        self.button_play.Enable(False)
        self.button_stop.Enable(True)
        self.edit_ch_1.Enable(False)
        self.edit_ch_2.Enable(False)
        self.edit_range.Enable(False)
        self.edit_rate.Enable(False)
        self.frame.daq.set_led(3)
        wx.CallAfter(pub.sendMessage, "clearcanvas", None)
        if self.frame.comunication_thread.is_alive():
            self.frame.comunication_thread.restart()
        else:
            self.frame.comunication_thread.start()
            self.frame.comunication_thread.stop()
            self.play_event(0)

    def stop_event(self, event):
        self.button_play.Enable(True)
        self.button_stop.Enable(False)
        self.edit_ch_1.Enable(True)
        self.edit_ch_2.Enable(True)
        self.edit_rate.Enable(True)
        if (
            self.hw_ver == 1
                or (self.hw_ver == 2 and self.edit_ch_2.GetValue() != "AGND")):
                    self.edit_range.Enable(True)

        self.frame.daq.set_led(1)
        self.frame.comunication_thread.stop()

    def slider_change(self, event):
        dac_value = self.edit_value.GetValue()
        self.frame.daq.set_analog(dac_value)

    def edit_ch_1_change(self, event):
        if self.hw_ver == 1:
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

    def edit_ch_2_change(self, event):
        if self.hw_ver == 1:
            return
        if self.edit_ch_2.GetValue() == "AGND":
            self.edit_range.Enable(False)
            self.edit_range.SetSelection(0)
        else:
            self.edit_range.Enable(True)


class PageThree(wx.Panel):
    def __init__(self, parent, frame):
        self.frame = frame
        wx.Panel.__init__(self, parent)
        index_1 = 100
        self.rb = []
        self.label = []
        self.buttons = []
        self.output = []
        self.value = []
        self.status = self.values = 0
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=20, vgap=20)
        if hasattr(sys, "frozen"):
            executable = sys.executable
        else:
            executable = __file__
        red_image_path = \
            os.path.join(os.path.dirname(executable), 'resources', 'red.jpg')
        bm = wx.Image(red_image_path, wx.BITMAP_TYPE_ANY)
        bm.Rescale(40, 40)
        self.image_red = bm.ConvertToBitmap()
        green_image_path = \
            os.path.join(os.path.dirname(executable), 'resources', 'green.jpg')
        bm = wx.Image(green_image_path, wx.BITMAP_TYPE_ANY)
        bm.Rescale(40, 40)
        self.image_green = bm.ConvertToBitmap()
        switchon_image_path = os.path.join(
            os.path.dirname(executable), 'resources', 'switchon.jpg')
        bm = wx.Image(switchon_image_path, wx.BITMAP_TYPE_ANY)
        bm.Rescale(40, 40)
        self.image_switch_on = bm.ConvertToBitmap()
        switchoff_image_path = os.path.join(
            os.path.dirname(executable), 'resources', 'switchoff.jpg')
        bm = wx.Image(switchoff_image_path, wx.BITMAP_TYPE_ANY)
        bm.Rescale(40, 40)
        self.image_switch_off = bm.ConvertToBitmap()
        for i in range(6):
            radio_list = []
            radio_list.append("Input")
            radio_list.append("Output")
            self.label.append(wx.StaticText(self, label="D%d" % (i+1)))
            self.rb.append(wx.RadioBox(
                self, label="Select input or output?",  choices=radio_list,
                majorDimension=2, style=wx.RA_SPECIFY_COLS))
            size_ = (
                self.image_green.GetWidth()+5, self.image_green.GetHeight()+5)
            self.buttons.append(wx.BitmapButton(
                self, id=index_1+i, bitmap=self.image_green, pos=(10, 20),
                size=size_))
            self.output.append(False)
            self.value.append(False)
            self.Bind(wx.EVT_BUTTON, self.output_change, self.buttons[i])
            self.Bind(wx.EVT_RADIOBOX, self.update_event, self.rb[i])
            grid.Add(self.label[i], pos=(i, 0))
            grid.Add(self.rb[i], pos=(i, 1))
            grid.Add(self.buttons[i], pos=(i, 2))
        self.button_update = wx.Button(self, label="Update", pos=(80, 420))
        self.Bind(wx.EVT_BUTTON, self.update_event, self.button_update)
        main_sizer.Add(grid, 0, wx.ALL, border=20)
        self.SetSizerAndFit(main_sizer)

    def deactivate_digital(self, number):
        self.label[number-1].Enable(False)
        self.rb[number-1].Enable(False)
        self.buttons[number-1].Enable(False)

    def activate_digital(self, number):
        self.label[number-1].Enable(True)
        self.rb[number-1].Enable(True)
        self.buttons[number-1].Enable(True)

    def update_event(self, event):
        self.status = 0
        for i in range(6):
            if self.rb[i].GetSelection():
                self.output[i] = True
                self.status = self.status | (1 << i)
            else:
                self.output[i] = False
        self.frame.daq.set_port_dir(self.status)
        value_input = self.frame.daq.set_port(self.values)
        for i in range(6):
            if value_input & (1 << i):
                if self.output[i] is False:
                    self.buttons[i].SetBitmapLabel(self.image_green)
                else:
                    self.buttons[i].SetBitmapLabel(self.image_switch_on)
            else:
                if self.output[i] is False:
                    self.buttons[i].SetBitmapLabel(self.image_red)
                else:
                    self.buttons[i].SetBitmapLabel(self.image_switch_off)
        self.frame.page_4.stop_counter_event(self)
        self.frame.page_4.stop_pwm_event(self)
        self.frame.page_4.stop_capture_event(self)
        self.frame.timer_thread.stop()

    def output_change(self, event):
        button = event.GetEventObject()
        index_1 = button.GetId()-100
        if self.output[index_1]:
            if self.value[index_1]:
                self.value[index_1] = False
                button.SetBitmapLabel(self.image_switch_off)
                self.values = self.values & ~(1 << index_1)
            else:
                self.value[index_1] = True
                button.SetBitmapLabel(self.image_switch_on)
                self.values = self.values | (1 << index_1)
        self.frame.daq.set_port(self.values)


class PageFour(wx.Panel):
    def __init__(self, parent, frame):
        self.frame = frame
        wx.Panel.__init__(self, parent)
        self.page_1 = self.frame.page_1
        self.pwm_label = wx.StaticBox(self, -1, 'PWM:')
        self.pwm_grap_horizontal_sizer = wx.StaticBoxSizer(
            self.pwm_label, wx.VERTICAL)
        self.capture_label = wx.StaticBox(self, -1, 'Capture (us):')
        self.capture_grap_horizontal_sizer = wx.StaticBoxSizer(
            self.capture_label, wx.VERTICAL)
        self.counter_label = wx.StaticBox(self, -1, 'Counter:')
        self.counter_grap_horizontal_sizer = wx.StaticBoxSizer(
            self.counter_label, wx.VERTICAL)
        self.encoder_label = wx.StaticBox(
            self, -1, 'Encoder', size=(240, 140))
        self.encoder_grap_horizontal_sizer = wx.StaticBoxSizer(
            self.encoder_label, wx.VERTICAL)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=20, vgap=20)
        pwm_sizer = wx.BoxSizer(wx.VERTICAL)
        capture_sizer = wx.BoxSizer(wx.VERTICAL)
        counter_sizer = wx.BoxSizer(wx.VERTICAL)
        encoder_sizer = wx.GridBagSizer(hgap=20, vgap=20)
        self.period_label = wx.StaticText(self, label="Period (us):")
        self.duty_label = wx.StaticText(self, label="Duty (%):")
        self.period_edit = (FloatSpin(
            self, value=1000, min_val=1, max_val=65535, increment=1,
            digits=0))
        self.duty_edit = wx.Slider(
            self, -1, 0, 0, 100, pos=(0, 0), size=(100, 50),
            style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.set_pwm = wx.Button(self, label="Set PWM")
        self.Bind(wx.EVT_BUTTON, self.set_pwm_event, self.set_pwm)
        self.stop_pwm = wx.Button(self, label="Stop PWM")
        self.Bind(wx.EVT_BUTTON, self.stop_pwm_event, self.stop_pwm)
        self.stop_pwm.Enable(False)
        self.reset_pwm = wx.Button(self, label="Reset PWM")
        self.Bind(wx.EVT_BUTTON, self.reset_pwm_event, self.reset_pwm)
        self.reset_pwm.Enable(False)
        self.get_counter = wx.TextCtrl(self, style=wx.TE_READONLY)
        pwm_sizer.Add(self.period_label, 0, wx.ALL, border=5)
        pwm_sizer.Add(self.period_edit, 0, wx.ALL, border=5)
        pwm_sizer.Add(self.duty_label, 0, wx.ALL, border=5)
        pwm_sizer.Add(self.duty_edit, 0, wx.ALL, border=5)
        pwm_sizer.Add(self.set_pwm, 0, wx.ALL, border=5)
        pwm_sizer.Add(self.stop_pwm, 0, wx.ALL, border=5)
        pwm_sizer.Add(self.reset_pwm, 0, wx.ALL, border=5)
        self.set_counter = wx.Button(self, label="Start counter")
        self.Bind(wx.EVT_BUTTON, self.start_counter, self.set_counter)
        self.stop_counter = wx.Button(self, label="Stop counter")
        self.stop_counter.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.stop_counter_event, self.stop_counter)
        counter_sizer.Add(self.get_counter, 0, wx.ALL, border=5)
        counter_sizer.Add(self.set_counter, 0, wx.ALL, border=5)
        counter_sizer.Add(self.stop_counter, 0, wx.ALL, border=5)
        self.get_capture = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.set_capture = wx.Button(self, label="Start capture")
        self.Bind(wx.EVT_BUTTON, self.start_capture, self.set_capture)
        self.stop_capture = wx.Button(self, label="Stop capture")
        self.stop_capture.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.stop_capture_event, self.stop_capture)
        radio_list = ["Low time", "High time", "Full period"]
        self.rb = wx.RadioBox(
            self, label="Select width:", choices=radio_list, majorDimension=3,
            style=wx.RA_SPECIFY_COLS)
        capture_sizer.Add(self.set_capture, 0, wx.ALL, border=5)
        capture_sizer.Add(self.get_capture, 0, wx.ALL, border=5)
        capture_sizer.Add(self.stop_capture, 0, wx.ALL, border=5)
        capture_sizer.Add(self.rb, 0, wx.ALL, border=5)
        self.set_encoder = wx.Button(self, label='Start encoder')
        self.Bind(wx.EVT_BUTTON, self.start_encoder_event, self.set_encoder)
        self.stop_encoder = wx.Button(self, label='Stop encoder')
        self.Bind(wx.EVT_BUTTON, self.stop_encoder_event, self.stop_encoder)
        self.stop_encoder.Enable(False)
        self.gauge = wx.Gauge(self, range=100, size=(100, 15))
        self.current_position = wx.TextCtrl(
            self, style=wx.TE_READONLY | wx.TE_CENTRE)
        self.encoder_value = wx.TextCtrl(self, style=wx.TE_CENTRE)
        radio_list = ["Circular", "Linear"]
        self.mode_encoder = wx.RadioBox(
            self, label="Select mode:", choices=radio_list, majorDimension=3,
            style=wx.RA_SPECIFY_COLS)

        self.resolution_label = wx.StaticText(self, label="Resolution:")
        encoder_sizer.Add(self.gauge, pos=(0, 1))
        encoder_sizer.Add(self.current_position, pos=(0, 0))
        encoder_sizer.Add(self.mode_encoder, pos=(1, 0), span=(1, 2))
        encoder_sizer.Add(self.resolution_label, pos=(2, 0))
        encoder_sizer.Add(self.encoder_value, pos=(2, 1))
        encoder_sizer.Add(self.set_encoder, pos=(3, 0), span=(1, 2))
        encoder_sizer.Add(self.stop_encoder, pos=(4, 0), span=(1, 2))
        self.pwm_grap_horizontal_sizer.Add(pwm_sizer, 0, wx.CENTRE)
        self.capture_grap_horizontal_sizer.Add(capture_sizer, 0, wx.CENTRE)
        self.counter_grap_horizontal_sizer.Add(counter_sizer, 0, wx.CENTRE)
        self.encoder_grap_horizontal_sizer.Add(encoder_sizer, 0, wx.CENTRE)
        grid.Add(self.pwm_grap_horizontal_sizer, flag=wx.EXPAND, pos=(1, 1))
        grid.Add(
            self.capture_grap_horizontal_sizer, flag=wx.EXPAND, pos=(0, 1))
        grid.Add(
            self.counter_grap_horizontal_sizer, flag=wx.EXPAND, pos=(1, 0))
        grid.Add(
            self.encoder_grap_horizontal_sizer, flag=wx.EXPAND, pos=(0, 0))
        vertical_sizer.Add(grid, 0, wx.ALL, border=20)
        main_sizer.Add(vertical_sizer, 0, wx.ALL, border=20)
        self.SetSizer(main_sizer)

        #Create publisher receiver
        pub.subscribe(self.refresh_counter, "counter_value")
        pub.subscribe(self.refresh_capture, "capture_value")
        pub.subscribe(self.refresh_encoder, "encoder_value")

    def refresh_counter(self, msg):
        if isinstance(msg.data, int):
            self.get_counter.Clear()
            self.get_counter.AppendText(str(msg.data))

    def refresh_capture(self, msg):
        if isinstance(msg.data, int):
            capture = msg.data
            self.get_capture.Clear()
            if not 0 < capture < 65000:
                capture = "overflow"
            self.get_capture.AppendText(str(capture))

    def refresh_encoder(self, msg):
        if isinstance(msg.data, int):
            encoder = msg.data
            self.current_position.Clear()
            self.current_position.AppendText(str(encoder))
            if self.encoder_resolution != 0:
                encoder = encoder * 100 / self.encoder_resolution
                self.gauge.SetValue(pos=encoder)
            else:
                self.gauge.SetValue(0)

    def set_pwm_event(self, event):
        self.deactivate_starts()
        self.stop_pwm.Enable(True)
        self.reset_pwm.Enable(True)
        self.get_counter.Clear()
        self.get_capture.Clear()
        self.frame.timer_thread.stop()
        self.period = self.period_edit.GetValue()
        self.period_edit.SetValue(self.period)
        self.duty = self.duty_edit.GetValue() * 1023 / 100
        self.frame.daq.init_pwm(self.duty, self.period)

    def start_counter(self, event):
        self.frame.daq.init_counter(0)
        self.deactivate_starts()
        self.stop_counter.Enable(True)
        self.get_counter.Clear()
        self.frame.timer_thread.start_counter()

    def start_capture(self, event):
        self.frame.daq.init_capture(2000)
        self.deactivate_starts()
        self.stop_capture.Enable(True)
        self.get_capture.Clear()
        self.frame.timer_thread.start_capture()

    def stop_capture_event(self, event):
        self.frame.daq.stop_capture()
        self.activate_starts()
        self.stop_capture.Enable(False)
        self.frame.timer_thread.stop()

    def reset_pwm_event(self, event):
        self.stop_pwm_event(0)
        self.set_pwm_event(0)

    def stop_pwm_event(self, event):
        self.activate_starts()
        self.reset_pwm.Enable(False)
        self.stop_pwm.Enable(False)
        self.frame.daq.stop_capture()
        self.frame.daq.stop_pwm()

    def stop_counter_event(self, event):
        self.frame.daq.stop_capture()
        self.activate_starts()
        self.stop_counter.Enable(False)
        self.frame.timer_thread.stop()

    def start_encoder_event(self, event):
        if self.mode_encoder.GetSelection() == 0:
            if self.encoder_value.GetLineText(0).isdigit():
                self.encoder_resolution = int(
                    self.encoder_value.GetLineText(0))
                if self.encoder_resolution < 0 or \
                        self.encoder_resolution > 65535:
                        dlg = wx.MessageDialog(
                            self,
                            "Resolution can not be neither greater than 65535 \
                            nor lower than 1", "Error!",
                            wx.OK | wx.ICON_WARNING)
                        dlg.ShowModal()
                        dlg.Destroy()
                        return
            else:
                dlg = wx.MessageDialog(
                    self, "Not a valid resolution", "Error!",
                    wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()
                return
        else:
            self.encoder_resolution = 0
        self.encoder_value.Enable(False)
        self.frame.daq.init_encoder(self.encoder_resolution)
        self.deactivate_starts()
        self.frame.page_3.deactivate_digital(6)
        self.stop_encoder.Enable(True)
        self.frame.timer_thread.start_encoder()

    def stop_encoder_event(self, event):
        self.activate_starts()
        self.frame.page_3.activate_digital(6)
        self.encoder_value.Enable(True)
        self.frame.daq.stop_encoder()
        self.stop_encoder.Enable(False)
        self.frame.timer_thread.stop()

    def activate_starts(self):
        self.set_counter.Enable(True)
        self.set_capture.Enable(True)
        self.set_encoder.Enable(True)
        self.set_pwm.Enable(True)
        self.frame.page_3.activate_digital(5)

    def deactivate_starts(self):
        self.set_counter.Enable(False)
        self.set_capture.Enable(False)
        self.set_encoder.Enable(False)
        self.set_pwm.Enable(False)
        self.frame.page_3.deactivate_digital(5)


class MainFrame(wx.Frame):
    def __init__(self, port):
        self.comunication_thread = None
        self.timer_thread = None
        wx.Frame.__init__(
            self, None, title="DAQControl",
            style=wx.DEFAULT_FRAME_STYLE &
            ~(wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        self.daq = DAQ(port)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        if hasattr(sys, "frozen"):
            executable = sys.executable
        else:
            executable = __file__

        icon_path = os.path.join(
            os.path.dirname(executable), 'resources', 'icon64.ico')
        icon = wx.Icon(icon_path, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetFieldsCount(2)
        info = self.daq.get_info()
        hw_ver = "[M]" if info[0] == 1 else "[S]"
        fw_ver = (
            str(info[1] / 100) + "." + str((info[1] / 10) % 10) + "." +
            str(info[1] % 10))
        self.status_bar.SetStatusText("H:%s V:%s" % (hw_ver, fw_ver), 0)
        # Here we create a panel and a notebook on the panel
        self.p = wx.Panel(self)
        self.note_book = wx.Notebook(self.p)
        # create the page windows as children of the notebook
        self.page_1 = PageOne(self.note_book, info[0], self)
        self.page_1.SetBackgroundColour('#ece9d8')
        self.page_3 = PageThree(self.note_book, self)
        self.page_3.SetBackgroundColour('#ece9d8')
        self.page_4 = PageFour(self.note_book, self)
        self.page_4.SetBackgroundColour('#ece9d8')
        # add the pages to the notebook with the label to show on the tab
        self.note_book.AddPage(self.page_1, "Analog I/O")
        self.note_book.AddPage(self.page_3, "Digital I/O")
        self.note_book.AddPage(self.page_4, "Timer-Counter")
        # finally, put the notebook in a sizer for the panel to manage
        # the layout
        sizer = wx.BoxSizer()
        sizer.Add(self.note_book, 1, wx.EXPAND)
        self.p.SetSizer(sizer)
        self.sizer = sizer
        sz = self.page_1.GetSize()
        sz[1] += 80
        sz[0] += 10
        self.SetSize(sz)
        self.daq.enable_crc(1)
        self.daq.set_analog(0)
        self.daq.set_port_dir(0)

    def on_close(self, event):
        dlg = wx.MessageDialog(
            self, "Do you really want to close this application?",
            "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.comunication_thread.stop_thread()
            self.timer_thread.stop_thread()
            self.Destroy()
            self.daq.close()

    def show_error_parameters(self):
        dlg = wx.MessageDialog(
            self, "Verify parameters", "Error!", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()

    def daq_error(self, number=0, foo=0):
        error_str = (
            "DAQ invokes an error. Line number:" + str(number) + " in " + foo +
            " function.")
        dlg = wx.MessageDialog(
            self, error_str, "Error!", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()


class InitDlg(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(
            self, None, title="DAQControl", style=(
                wx.STAY_ON_TOP | wx.CAPTION))
        self.horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.horizontal_sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        self.vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        self.gauge = wx.Gauge(self, range=100, size=(100, 15))
        self.horizontal_sizer.Add(self.gauge, wx.EXPAND)
        self.horizontal_sizer_2.Add(self.gauge, wx.EXPAND)
        avaiable_ports = list(comports())
        self.sample_list = []
        if len(avaiable_ports) != 0:
            for nombre in avaiable_ports:
                self.sample_list.append(nombre[0])
        self.label_hear = wx.StaticText(self, label="Select Serial Port")
        self.edit_hear = wx.ComboBox(
            self, size=(-1, -1), choices=self.sample_list,
            style=wx.CB_READONLY)
        self.edit_hear.SetSelection(0)
        self.horizontal_sizer.Add(self.label_hear, wx.EXPAND)
        self.horizontal_sizer.Add(self.edit_hear, wx.EXPAND)
        self.button_ok = wx.Button(self, label="OK")
        self.Bind(wx.EVT_BUTTON, self.ok_event, self.button_ok)
        self.button_cancel = wx.Button(self, label="Cancel")
        self.Bind(wx.EVT_BUTTON, self.cancel_event, self.button_cancel)
        self.horizontal_sizer_2.Add(self.button_ok, wx.EXPAND)
        self.horizontal_sizer_2.Add(self.button_cancel, wx.EXPAND)
        self.vertical_sizer.Add(self.horizontal_sizer, wx.EXPAND)
        self.vertical_sizer.Add(self.horizontal_sizer_2, wx.EXPAND)

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
                    self, "DAQControl started", "Continue",
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

    if app.connected:
        frame = MainFrame(app.com_port)
        comunication_thread = ComThread(frame)
        timer_thread = TimerThread(frame)
        frame.comunication_thread = comunication_thread
        frame.timer_thread = timer_thread
        timer_thread.start()
        frame.Centre()
        frame.Show()
        app.MainLoop()


if __name__ == "__main__":
    main()
