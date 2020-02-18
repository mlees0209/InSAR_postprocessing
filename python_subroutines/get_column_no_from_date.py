#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 16:39:14 2020
quick one that returns an index for a filename
@author: mlees
"""

import sys
from matplotlib.dates import date2num
from datetime import datetime as dt
import numpy as np

filename=sys.argv[1]
indate=sys.argv[2]

f = open(filename)
line=f.readline()
line = line.split(',')

dates = [tit for tit in line if '20' in tit] # use containing 20 as an alias for being a date
dates = [dat.strip('D') for dat in dates]
dates = [dat.strip('\n') for dat in dates]

dates_as_numbers = [date2num(dt.strptime(date, '%Y%m%d')) for date in dates]

indate_as_number = date2num(dt.strptime(indate,'%Y%m%d'))

arg = np.argmin(np.abs(np.array(dates_as_numbers) - indate_as_number))

nondates = len(line) - len(dates)

print(arg+nondates)