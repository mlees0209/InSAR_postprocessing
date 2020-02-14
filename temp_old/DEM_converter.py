#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 10:11:01 2019

USAGE: python DEM_converter demname

demname is eg 'elevation.dem'. This script needs 'demname.rsc' to be in the same directory. 

@author: mlees
"""
import sys 

if len(sys.argv) < 1:
    print('Usage: DEM_viewer.py binary_dem_filename')
    print('  You screwed up, ERROR')
    sys.exit(1)

binary_dem_filename = sys.argv[1]
#binary_dem_filename = 'elevation.dem'

import numpy as np


# load in the DEM and its coordinates
A_raw = np.fromfile('%s' % binary_dem_filename, dtype='f2', sep="")
A_raw = np.nan_to_num(A_raw)

latloncoords = np.genfromtxt('%s.rsc' % binary_dem_filename)
length=np.int(latloncoords[1,1])
width=np.int(latloncoords[0,1])
#A = np.reshape(A_raw,[length, width])

# Make the lat,lon coordinates
lon = np.arange(latloncoords[2,1],latloncoords[2,1]+(width-1)*latloncoords[4,1],latloncoords[4,1])
lat = np.arange(latloncoords[3,1],latloncoords[3,1]+(length-1)*latloncoords[5,1],latloncoords[5,1])
lats = np.repeat(lat,width) 
lons = np.tile(lon,length)

example=np.array([lons,lats,A_raw]).transpose() # make a three column array of lat,lon,dem_value

outputname='%s.xyz' % binary_dem_filename.rstrip('.dem') # make the output filename
print('Saving 3x%i array as binary, please be paitent.' % len(lons))
example.astype('float32').tofile(outputname) # save as float32 format
print('Saved as %s; what a relief.' % outputname)

np.savetxt('outputname.tmp',[outputname], fmt='%s')
