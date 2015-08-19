#!/usr/bin/env python

from setuptools import setup

DESCRIPTION = "GUI interface for openDAQ"
LONG_DESCRIPTION = """`OpenDAQ <http://www.open-daq.com/>`_ is an open source
acquisition instrument which provides several physical interaction capabilities
such as analog inputs and outputs, digital inputs and outputs, timers and
counters."""


setup(
    name='opendaq-gui',
    version='0.1.0',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Adrian Alvarez',
    author_email='alvarez.lopez.adri@ingen10.com',
    url='http://github.com/Ingen10/easydaq',
    license='LGPL',
    platforms=['any'],
    install_requires=['opendaq', 'wxPython==2.8.12.1', 'numpy', 'matplotlib'],
    packages=['easy_daq', 'daq_control', 'daq_calibration'],
    include_package_data = True,
    entry_points={
        'gui_scripts': [
	    'daq_control = daq_control.main:main',
	    'easy_daq = easy_daq.main:main',
	    'daq_calibration = daq_calibration.main:main'
	]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
