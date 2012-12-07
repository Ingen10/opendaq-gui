'''
Created on 13/11/2012

@author: Adrian
'''
from distutils.core import setup
import py2exe

options = {'py2exe':{'dll_excludes':['MSVCP90.dll']}}
setup(windows=['DAQControl.py'], options=options)