#!/usr/bin/env python

from setuptools import setup
from easydaq import __version__

DESCRIPTION = "GUI interface for openDAQ"
LONG_DESCRIPTION = """`OpenDAQ <http://www.open-daq.com/>`_ is an open source
acquisition instrument which provides several physical interaction capabilities
such as analog inputs and outputs, digital inputs and outputs, timers and
counters."""


setup(
    name='easydaq',
    version=__version__,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Adrian Alvarez',
    author_email='alvarez.lopez.adri@ingen10.com',
    url='http://github.com/Ingen10/easydaq',
    license='LGPL',
    platforms=['any'],
    install_requires=['pyserial', 'wx'],
    packages=['easydaq'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Scientific/Engineering'
        ' :: Libraries :: Python Modules',
    ]
)
