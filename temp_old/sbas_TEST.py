#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 17 16:34:12 2019

@author: mlees
"""

import numpy as np
import matplotlib.pyplot as plt
import sys 

interferogram1 = '20170812_20170824.u'
interferogram2 = '20170824_20170905.u'

with open(interferogram1, 'rb') as fid:
    data_array1 = np.fromfile(fid, np.float32)

with open(interferogram2, 'rb') as fid:
    data_array2 = np.fromfile(fid, np.float32)



nr=864
naz=768

#data_array1 = np.reshape(data_array1,(naz,2*nr))
#data_array1 = data_array1[:,nr:]
#
#data_array2 = np.reshape(data_array2,(naz,2*nr))
#data_array2 = data_array2[:,nr:]
#
#
#
#plt.imshow(data_array1,filternorm=1)
#plt.figure()
#plt.imshow(data_array2,filternorm=1)
#


v12 = data_array1/12
v23 = data_array2/12

v12 = np.reshape(v12,(naz,2*nr))
v12 = v12[:,nr:]
plt.imshow(v12,filternorm=1)
