python-opendaq
==============
- - -
Python binding for openDAQ hardware.

openDAQ libraries and examples are compatible with Python 2.X. Python 3.X is not yet supported.

support@open-daq.com

* * *

OpenDAQ is an open source acquisition instrument, 
which provides user with several physical interaction capabilities such as analog inputs 
and outputs, digital inputs and outputs, timers and counters.

By means of an USB connection, openDAQ brings all the information that it captures to a host computer, 
where you can decide how to process, display and store it. Several demos and examples are provided 
in website's support page. (http://www.open-daq.com/paginas/support)

This repository includes some libraries and examples to control openDAQ from Python. Python is 
a high-level interpreted programming language. It has become very popular during the last few years, 
especially as a scripting language, although it also can be used to generate standalone executables. 
Most important, CPython, the reference implementation of Python, is free and open source software and 
has a community-based development model, as do nearly all of its alternative implementations.

Be aware that there are two versions of Python available right now, Python 2 and Python 3. Although 
the last is newer and has some improvements, it has not fully compatibility with all operating systems, 
and many third party tools are not available yet for it. For these reasons, openDAQ libraries and 
examples are only compatible with Python 2.X.

You can find and download IDE and interpreter here:
http://python.org/download/

You will find the following stuff in this repository:

* DAQcontrol: This is a demo program of complete test panels. It has user controls to access via 
Comand-Response mode to most of the device functions, including: Analog Inputs, Analog Output, 
Digital I/Os, and Timer/Counter functions (PWM, Capture and Counter).

* EasyDAQ: This is another demo program, which provides an easy way to configure and perform stream 
mode experiments. User can configure analog line, gain and scan rate for up to four simultaneous 
experiments.


Please, go to http://www.open-daq.com for additional info.



