:Authors:
 openDAQ
:Version:
 1.0
:Date:
 05/12/2013

===================
FUNCTION REFERENCE:
===================

**crc(data):**
===============

Create cyclic redundancy check.

**check_crc(data):**
====================

Cyclic redundancy check.

*Args:*
    + data: variable that saves the checksum.
*Raises:*
    + CRCError: Checksum incorrect.

check_stream_crc(head, data):
=============================

Cyclic redundancy check for streaming.

*Args:*
    + head: variable that defines the header.
    + data: variable that defines the data.

__init__(self, port):
=====================
Class constructor.

open(self):
===========

Open serial port.

Configure serial port to be opened.

close(self):
============

Close serial port.

Configure serial port to be closed.

send_command(self, cmd, ret_fmt, debug=False):
==============================================

Send a command to openDAQ.

*Args:*
    + cmd: variable that defines the command.
    + ret_fmt: variable that defines the format.
    + debug: variable that defines the debug mode.
*Returns:*
    + The command number into variable 'data'.
*Raises:*
    + LengthError: An error occurred.

get_info(self):
===============

Read device configuration: serial number, firmware
version and hardware version.

get_vHW(self):
==============

Get the hardware version.

Recognize the hardware version.

read_adc(self):
===============

Read the analog-to-digital converter.

Read data from adc and return it in 'value'.

read_analog(self):
==================

Read the analog data.

Read raw data.

conf_adc(self, pinput, ninput=0, gain=0, nsamples=20):
======================================================

Configure the analog-to-digital converter.

Get the parameters for configure the analog-to-digital
converter.     

*Args:*
    - pinput: variable that defines the input pin
    - ninput: variable that defines the input number
    - gain: variable that defines the gain
    - nsamples: variable that defines the samples number

enable_crc(self, on):
=====================

Enable/Disable cyclic redundancy check.

*Args:*
    - on: variable that defines the enable status.
    
set_led(self, color):
=====================

Choose LED status.

LED switch on (green, red or orange) or switch off.

*Args:*
    - color: variable that defines the led color (0=off,
        1=green,2=red, 3=orange). 
*Raises:*
    - ValueError: An error ocurred caused for invalid
        selecction,must be in [0,1,2,3] and print
        'invalid color number'. 
        
set_analog(self, volts):
========================

Set DAC output voltage (milivolts value).

Set the output between the voltage hardware limits.
(-4.096V and +4.096V for openDAQ[M])
(0V and +4.096V for openDAQ[S])

*Args:*
    - volts: variable that defines the output value.
*Raises:*
    - ValueError: An error ocurred when voltage is out of
        range and print 'DAQ voltage out of range'.

set_dac(self, raw):
===================

Set DAC with raw value.

Set the raw value into DAC before conditioning the data.

*Args:*
    - raw: variable with the raw data.

set_port_dir(self, output):
===========================

Configure/Read all PIOs directions.

*Args:*
    - output: variable that defines PIOs direction values
        (0 inputs, 1 outputs).

set_port(self, value):
======================

Write/Read all PIOs in a port.

*Args:*
   - value: variable that defines PIOs output value.

set_pio_dir(self, number, output):
==================================

Configure PIO direction.

*Args:*
    - number: variable that defines the PIO number.
    - output: variable that defines PIO direction (0 input, 
        1 output).
*Raises:*
    - ValueError: An error ocurred when the PIO number doesn't
        exist, and print 'Invalid PIO number'.

set_pio(self, number, value):
=============================

Write/Read PIO output.

*Args:*
    - number: variable that defines the PIO number.
    - value: variable that defines low or high voltage 
        output (+5V).
*Raises:*
    - ValueError: An error ocurred when the PIO number doesn´t
        exist, and print 'Invalid PIO number'.
    
init_counter(self, edge):
=========================

Initialize the edge counter.

Configure which edge increments the count:
Low-to-High or High-to-Low.

*Args:*
    - edge: variable that definess the increment mode
        (1 Low-to-High, 0  High-to-Low).
    
get_counter(self, reset):
=========================

Get counter value.

*Args:*
    - reset: variable that reset the count (1 reset
        accumulator).

init_capture(self, period):
===========================

Start capture mode arround a given period.

*Args:*
    - period: variable that definess the aproximate period oft
        the wave (microseconds).

stop_capture(self):
===================

Stop capture mode.

get_capture(self, mode):
========================

Get current period length.

Low cycle, High cycle or Full period.

*Args:*
    - mode: variable that defines the period length.
        - 0 Low cycle
        - 1 High cycle
        - 2 Full period

init_encoder(self, resolution):
===============================

Start encoder function.

*Args:*
    - resolution: variable that defines maximun number of
        ticks per round [0:255].

get_encoder(self):
==================

Get current encoder relative position.

init_pwm(self, duty, period):
=============================

Start PWM whit a given period and duty.

*Args:*
    - duty: variable that defines the high time of the signal
        [0:1023](0 always low, 1023 always high
    - period:variable that defines the frecuency of the signal 
        (microseconds) [0:65535]
    
stop_pwm(self):
===============

Stop PWM.

__get_calibration(self, gain_id):
=================================

Read device calibration.

*Args:*
    - gain_id: variable that defines the gain multiplier [0:4]
        (0 x(1/2), 1 x(1), 2 x(2, 3 x(10), 4 x(100) default 
        (1)).

get_cal(self):
==============

Read device calibration.

*Returns:*
    - The gains and offsets values.

get_dac_cal(self):
==================

Read DAC calibration.

*Returns:*
    - The gain and offset value.

__set_calibration(self, gain_id, gain, offset):
===============================================

Set device calibration.

*Args:*
    - gain_id: variable that defines the gain multiplier [0:4]
        (0 x(1/2), 1 x(1), 2 x(2, 3 x(10), 4 x(100) default
        (1)).
    - gain: variable that defines gain multiplied by 100000
        (m=Slope/100000, 0 to 0.65) [0:65535].
    - offset: variable that defines the offset raw value.
        [-32768:32768].

set_cal(self, gains, offsets, flag):
====================================

Set device calibration.

set_DAC_cal(self, gain, offset):
================================

Set DAC calibration.

conf_channel(self, number, mode, pinput, ninput=0, gain=1, nsamples=1):
=======================================================================

Configure one of the experiments (ANALOG, +IN, -IN, GAIN).

*Args:*
    - number: variable that defines the number of DataChannel
        to assign.
    - mode: variable that defines mode [0:5], 0 ANALOG_INPUT,
        1 ANALOG_OUTPUT, 2 DIGITAL_INPUT, 3 DIGITAL_OUTPUT,
        4 COUNTER_INPUT, 5 CAPTURE INPUT.
    - pinput: variable that defines positive/SE analog input
        [1:8] (default 5).
    - ninput: variable that defines negative analog input
        [0, 25, 5:8] (default 0).
    - gain: variable that defines gain multiplier [0:4]
        (0 x(1/2), 1 x(1), 2 x(2, 3 x(10), 4 x(100) default 
        (1)).
    - nsamples: variable that defines number of samples per
        point [1:255].
    
setup_channel(self, number, npoints, continuous=True):
======================================================

Configure the experiment's number of points.

*Args:*
    - number: variable that defines the number of DataChannel
        to assign.
    - npoints: variable that defines the number of total
        points [0:65536] (0 indicates continuous
        acquisition).
    - continuous: variable that defines repetition mode [0:1]
        0 continuous, 1 run once.

destroy_channel(self, number):
==============================

Delete Datachannel structure.

*Args:*
    - number: variable that defines the number of DataChannel
        to clear [0:4] 0 reset all DataChannel.

create_stream(self, number, period):
====================================

Create stream experiment.

*Args:*
    - number: variable that defines the number of DataChannel
        to assign [1:4].
    - period: variable that defines the period of the stream
        experiment [1:65536].

create_burst(self, period):
===========================

Create burst experiment.

*Args:*
    - period: variable that defines the period of the burst
        experiment (microseconds) [100:65535].

create_external(self, number, edge):
====================================

Create external experiment.

*Args*
    - number: variable that defines the number of DataChannel
        to assign [1:4].
    - edge: [0:1].

load_signal(self, data, offset):
================================

Load an array of values to preload DAC output.

*Args:*
    - data: variable that defines the data number [1:400].
    - offset: variable that defines the offset.

start(self):
============

Start an automated measurement.

stop(self):
===========

Stop actual measurement.

flush(self):
============

Call ser.flushInput().

flush_stream(self, data, channel):
==================================

Get stream from serial and reveive data in the buffer.

*Args:*
   - data: variable that defines the data.
   - channel: variable that defines the channel.

*Returns:*
    - 0 if there aren't any incoming data.
    - 1 if data stream was processed.
    - 2 if no data stream received. Useful for debuging.

*Raises:*
   - LengthError: An error ocurred.

get_stream(self, data, channel, callback=0):
============================================

*Args:*
    - data: variable that defines the data
    - channel: variable that defines the channel
    - callback: variable that defines the callback mode

*Returns:*
    - 0 if there aren't any incoming data.
    - 1 if data stream was processed.
    - 2 if no data stream received. Useful for debuging.

setVHW(self, v):
================

Choose the hardware version.

*Args:*
    - v: variable that defines the hardware version (m openDA
        [M], s openDAQ[S]).

set_DAC_gain_offset(self, g, o):
================================

Set DAC gain and offset.

*Args:*
    - g: variable that defines DAC gain.
    - o: variable that defines DAC offset.

set_gains_offsets(self, g, o):
==============================

Set gains and offsets.

*Args:*
    - g: variable that defines gains.
    - o: variable that defines offsets.

set_id(self, id):
=================

Identify openDAQ device.

*Args:*
    - id: variable that defines id number [000:999].

spisw_config(self, cpol, cpha):
===============================

Bit-Bang SPI configure (clock properties).

*Args:*
    - cpol: variable that defines clock polarity (clock pin
        state when inactive).
    - cpha: variable that defines clock phase (leading 0, or
        trailing 1 edges read).
*Raises:*
    - ValueError: An error ocurred and print 'Invalid
        spisw_config values'.

spisw_setup(self, nbytes, bbsck=1, bbmosi=2, bbmiso=3):
=======================================================

Bit-Bang SPI setup (PIO numbers to use).

*Args:*
    - nbytes: variable that defines number of bytes.
    - bbsck: variable that defines clock pin for bit bang SPI
        transfer.
    - bbmosi: variable that defines master out-Slave in pin
        for bit bang SPI transfer.
    - bbmiso: variable that defines master in-Slave out pin
        for bit bang SPI transfer.
*Raises:*
    - ValueError: An error ocurred when nbytes isn't between
        [0:3] and print 'Invalid number of bytes' or when
        (bbsck, bbmosi or bbmiso) are out of range and print  
        'Invalid spisw_setup values'.

spisw_bytetransfer(self, value):
================================

Bit-Bang SPI transfer (send+receive) (byte).

*Args:*
    - value: variable that defines data to send (byte to
        transmit)(MOSI output).

spisw_wordtransfer(self, value):
================================

Bit-Bang SPI transfer (send+receive) (word).

*Args:*
    - value: variable that defines data to send (word to
        transmit)(MOSI output).

