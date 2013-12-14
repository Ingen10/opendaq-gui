:Authors:
 JRB, MF
:Version:
 1.0
:Date:
 05/12/2013

==================================
OPENDAQ DAQ.PY FUNCTION REFERENCE:
==================================

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


open():
===========

Open serial port.

Configure serial port to be opened.

close():
============

Close serial port.

Configure serial port to be closed.

send_command(cmd, ret_fmt, debug):
==============================================

Send a command to openDAQ.

*Args:*
    + cmd: ID that defines the command (command number).
    + ret_fmt: Format of the arguments for the command (byte/int16).
    + debug: Toggle debug mode ON/OFF.
*Returns:*
    + The command ID and different arguments depending on the specific command.
*Raises:*
    + LengthError: The length of the response is not the expected.

get_info():
===============

Read device configuration: serial number, firmware version and hardware version.

*Returns:*
    + Hardware version.
    + Firmware version.
    + Device ID number.

get_vHW():
==============

Get the hardware version.

*Returns:*
    + Hardware version.

read_adc():
===============

Read the analog-to-digital converter.

Read data from ADC and return the 'RAW' value.

*Returns:*
    + ADC value: ADC raw value.

read_analog():
==================

Read the analog data.

ead data from ADC and convert it to millivolts using calibration values.

*Returns:*
    + Analog reading: Analog value converted into millivolts.

conf_adc(pinput, ninput, gain, nsamples):
======================================================

Configure the analog-to-digital converter.

Get the parameters for configure the analog-to-digital
converter.     

*Args:*
    - pinput: variable that defines the input pin
    - ninput: variable that defines the input number
    - gain: variable that defines the gain
    - nsamples: variable that defines the samples number

*Returns:*
    - ADC value: ADC raw value
    - pinput: variable that defines the input pin
    - ninput: variable that defines the input number
    - gain: variable that defines the gain
    - nsamples: variable that defines the samples number


enable_crc(on):
=====================

Enable/Disable cyclic redundancy check.

*Args:*
    - on: variable that defines the enable status.
    
set_led(color):
=====================

Choose LED status.

LED switch on (green, red or orange) or switch off.

*Args:*
    - color: variable that defines the led color (0=off,
        1=green,2=red, 3=orange). 
*Raises:*
    - ValueError: An error ocurred caused for invalid selection, must be in [0,1,2,3] and print 'Invalid color number'. 
        
set_analog(volts):
========================

Set DAC output voltage (millivolts value).

Set the output voltage value between the voltage hardware limits.
Device calibration values are used for the calculation.
Range: -4.096V to +4.096V for openDAQ[M]
Range: 0V to +4.096V for openDAQ[S]

*Args:*
    - volts: variable that defines the output value.
*Raises:*
    - ValueError: An error ocurred when voltage is out of range and print 'DAc voltage out of range'.

set_dac(raw):
===================

Set DAC with raw value.

Set the raw value into DAC without data conversion.

*Args:*
    - raw: RAW binary ADC data value.
*Raises:*
    - ValueError: An error ocurred when voltage is out of range and print 'DAC voltage out of range'.

set_port_dir(output):
===========================

Configure all PIOs directions.
Set the direction of all D1-D6 terminals.

*Args:*
    - output: variable that defines PIOs direction values (flags: 0 inputs, 1 outputs).

set_port(value):
======================

Write all PIOs values.
Set the value of all D1-D6 terminals.

*Args:*
   - value: Port output value byte (flags: 0 low, 1 high).


set_pio_dir(number, output):
==================================

Configure PIO direction.
Set the direction of a specific DIO terminal (D1-D6).

*Args:*
    - number: variable that defines the PIO number.
    - output: variable that defines PIO direction (0 input, 1 output).
*Raises:*
    - ValueError: An error ocurred when the PIO number doesn't exist, and print 'Invalid PIO number'.

set_pio(number, value):
=============================

Set PIO output value.
Set the value of the DIO terminal (0: low, 1: high).

*Args:*
    - number: variable that defines the PIO number.
    - value: variable that defines low or high voltage output (+5V).
*Raises:*
    - ValueError: An error ocurred when the PIO number doesn´t exist, and print 'Invalid PIO number'.
    
init_counter(edge):
=========================

Initialize the edge counter.

Configure which edge increments the count:
Low-to-High (1) or High-to-Low (0).

*Args:*
    - edge: variable that definess the increment mode (1 Low-to-High, 0  High-to-Low).
    
get_counter(reset):
=========================

Get counter value.

*Args:*
    - reset: variable that reset the count (1 reset accumulator).

init_capture(period):
===========================

Start capture mode arround a given period.

*Args:*
    - period: variable that defines the period of the wave (microseconds).

stop_capture():
===================

Stop capture mode.

get_capture(mode):
========================

Get current period length.

Low cycle, High cycle or Full period.

*Args:*
    - mode: variable that defines the period length.
        - 0 Low cycle
        - 1 High cycle
        - 2 Full period
*Returns:*
    - mode: 
    - Period: The period length in microseconds.


init_encoder(resolution):
===============================

Start encoder function.

*Args:*
    - resolution: variable that defines maximun number of ticks per round [0:65535].

get_encoder():
==================

Get current encoder relative position.

*Returns:*
    - Position: The actual encoder value. 

init_pwm(duty, period):
=============================

Start PWM whit a given period and duty.

*Args:*
    - duty: variable that defines the high time of the signal [0:1023](0 always low, 1023 always high)
    - period:variable that defines the frecuency of the signal (microseconds) [0:65535]
    
stop_pwm():
===============

Stop PWM.

__get_calibration(gain_id):
=================================

Read device calibration for a given analog configuration.
Gets calibration gain and offset for the corresponding analog configuration.

*Args:*
    - gain_id: variable that defines the analog configuration.
      (1:6 for openDAQ [M])
      (1:17 for openDAQ [S])
*Returns:*
    - Gain (100000[M] or 10000[S])
    - Offset

get_cal():
==============

Gets calibration values for all the available device configurations.

*Returns:*
    - The gains and offsets values.

get_dac_cal():
==================

Read DAC calibration.

*Returns:*
    - The gain and offset value.

__set_calibration(gain_id, gain, offset):
===============================================

Set device calibration.

*Args:*
    - gain_id: ID of the analog configuration setup
    - gain: variable that defines gain multiplied by 100000 ([M]) or 10000 ([S])
    - offset: variable that defines the offset raw value. [-32768:32768].

set_cal(gains, offsets, flag):
====================================

Set device calibration.

set_DAC_cal(self, gain, offset):
================================

Set DAC calibration.
Write all the calibration structures into the device

conf_channel(number, mode, pinput, ninput, gain, nsamples):
=======================================================================

Configure one of the experiments (ANALOG, +IN, -IN, GAIN).

*Args:*
    - number: variable that defines the number of DataChannel to assign.
    - mode: variable that defines mode [0:5], 0 ANALOG_INPUT, 1 ANALOG_OUTPUT, 2 DIGITAL_INPUT, 3 DIGITAL_OUTPUT, 4 COUNTER_INPUT, 5 CAPTURE INPUT.
    - pinput: variable that defines positive/SE analog input [1:8] (default 5).
    - ninput: variable that defines negative analog input [0, 25, 5:8] (default 0).
    - gain: variable that defines gain multiplier [0:4] (0 x(1/2), 1 x(1), 2 x(2, 3 x(10), 4 x(100) default (1)).
    - nsamples: variable that defines number of samples per point [1:255].
    
setup_channel(number, npoints, continuous):
======================================================

Configure the experiment's number of points.

*Args:*
    - number: variable that defines the number of DataChannel to assign.
    - npoints: variable that defines the number of total points [0:65536] (0 indicates continuous acquisition).
    - continuous: variable that defines repetition mode [0:1] 0 continuous, 1 run once.

destroy_channel(number):
==============================

Delete Datachannel structure.

*Args:*
    - number: variable that defines the number of DataChannel to clear [0:4] 0 reset all DataChannel.

create_stream(number, period):
====================================

Create stream experiment.

*Args:*
    - number: variable that defines the number of DataChannel to assign [1:4].
    - period: variable that defines the period of the stream experiment [1:65536].

create_burst(period):
===========================

Create burst experiment.

*Args:*
    - period: variable that defines the period of the burst experiment (microseconds) [100:65535].

create_external(number, edge):
====================================

Create external experiment.

*Args*
    - number: variable that defines the number of DataChannel to assign [1:4].
    - edge: [0:1].

load_signal(data, offset):
================================

Load an array of values to preload DAC output.

*Args:*
    - data: variable that defines the data number [1:400].
    - offset: variable that defines the offset.

start():
============

Start an automated measurement.

stop():
===========

Stop actual measurement.

flush():
============

Call ser.flushInput().

flush_stream(data, channel):
==================================

Get stream from serial and receive data in the buffer.

*Args:*
   - data: variable that defines the data.
   - channel: variable that defines the channel.

*Returns:*
    - 0 if there is no incoming data.
    - 1 if data stream was processed.
    - 2 if no data stream received. Useful for debugging.

*Raises:*
   - LengthError: An error ocurred.

get_stream(data, channel, callback):
============================================

*Args:*
    - data: variable that defines the data
    - channel: variable that defines the channel
    - callback: variable that defines the callback mode

*Returns:*
    - 0 if there aren't any incoming data.
    - 1 if data stream was processed.
    - 2 if no data stream received. Useful for debuging.

setVHW(v):
================

Choose the hardware version.

*Args:*
    - v: variable that defines the hardware version (m openDAQ [M], s openDAQ[S]).

set_DAC_gain_offset(g, o):
================================

Set DAC gain and offset.

*Args:*
    - g: variable that defines DAC gain.
    - o: variable that defines DAC offset.

set_gains_offsets(g, o):
==============================

Set gains and offsets.

*Args:*
    - g: variable that defines gains.
    - o: variable that defines offsets.

set_id(id):
=================

Identify openDAQ device.

*Args:*
    - id: variable that defines id number [000:999].

spisw_config(cpol, cpha):
===============================

Bit-Bang SPI configure (clock properties).

*Args:*
    - cpol: variable that defines clock polarity (clock pin state when inactive).
    - cpha: variable that defines clock phase (leading 0, or trailing 1 edges read).

*Raises:*
    - ValueError: An error ocurred and print 'Invalid spisw_config values'.

spisw_setup(nbytes, bbsck, bbmosi, bbmiso):
=======================================================

Bit-Bang SPI setup (PIO numbers to use).

*Args:*
    - nbytes: variable that defines number of bytes.
    - bbsck: variable that defines clock pin for bit bang SPI
        transfer.
    - bbmosi: variable that defines master out-Slave in pin for bit bang SPI transfer.
    - bbmiso: variable that defines master in-Slave out pin for bit bang SPI transfer.
*Raises:*
    - ValueError: An error ocurred when nbytes isn't between [0:3] and print 'Invalid number of bytes' or when (bbsck, bbmosi or bbmiso) are out of range and print 'Invalid spisw_setup values'.

spisw_bytetransfer(value):
================================

Bit-Bang SPI transfer (send+receive) (byte).

*Args:*
    - value: variable that defines data to send (byte to transmit)(MOSI output).

spisw_wordtransfer(value):
================================

Bit-Bang SPI transfer (send+receive) (word).

*Args:*
    - value: variable that defines data to send (word to transmit)(MOSI output).
