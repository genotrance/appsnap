import codecs
import ConfigParser
import filecmp
import getopt
import glob
import imp
import os
import os.path
import pycurl
import random
import re
import shutil
import socket
import string
import StringIO
import sys
import threading
import time
import traceback
import types
import unittest
import urllib
import _winreg
import wx
import wx.lib.dialogs
import yaml
import zipfile

def appsnap_main(mode='cli'):
    # Add directory to path
    sys.path.append('.')
    
    # Load appsnaplib module
    fp, pathname, description = imp.find_module('appsnaplib')
    appsnaplib = imp.load_module('appsnaplib', fp, pathname, description)
    if fp: fp.close()

    # Fix mode to be either cli or gui
    if mode != 'cli' and mode != 'gui': mode = 'cli'
    
    # Load cli/gui module
    fp, pathname, description = imp.find_module(mode, appsnaplib and appsnaplib.__path__)
    module = imp.load_module('appsnaplib.' + mode, fp, pathname, description)
    if fp: fp.close()
    module.appsnap_start()

if __name__ == '__main__':
    appsnap_main()
