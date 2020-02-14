#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 15 15:17:26 2019

@author: mlees
"""

import numpy as np
import matplotlib.pyplot as plt
import sys 

if len(sys.argv) < 1:
    print('Usage: create_usable_unwrapped_interferogram.py filename')
    print('  You screwed up, ERROR')
    sys.exit(1)

#binary_dem_filename = sys.argv[1]
binary_dem_filename = '20170824_20170905.u'

with open(binary_dem_filename, 'rb') as fid:
    data_array = np.fromfile(fid, np.float32)

nr=1488
naz=960

data_array = np.reshape(data_array,(naz,2*nr))

data_array = data_array[:,nr:]

#plt.imshow(data_array,filternorm=1)

data_array.astype('float64').tofile('%s.readable' % binary_dem_filename) # save as float64 format
