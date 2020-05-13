#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  2 21:02:18 2019

This script defines a number of functions which will be used for InSAR postprocessing. They are designed to be used on data which Tom has processed through the kml-maps portal: https://maps.ksat-gms.com/; or, data from another source in a similar .csv format.

Several of these functions are directly lifted from an earlier version called 'InSAR_processing.py'. Others are new. 

The functions are organised as follows:
    1. Functions which import things eg GPS data, inSAR data, kml lines...
    2. Functions which take inSAR data and extract a subset. eg extract from box, etc.
    3. Functions which plot things, eg. plot from box, etc.
    4. Miscellaneous functions.

@author: mlees
"""

print('Importing functions, modules and classes needed for InSAR postprocessing. Please wait a few moments.')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from datetime import datetime as dt
import seaborn as sns
from datetime import date
import geopy.distance
from fastkml import kml
from matplotlib import path
import os as os
import os.path as ospath
#import pygmt
from scipy.optimize import leastsq
import cartopy.io.img_tiles as cimgt
import cartopy.crs as ccrs
import scipy.signal
import simplekml
import sys
from astropy.convolution import convolve

#%% Define important constants.

FEET_TO_MM = 304.8




#%% 1. Functions which import things

def import_InSAR_csv(filename,sep=','):
    '''Imports InSAR data as a Pandas DataFrame. 'InSAR data' needs to be a csv file downloaded from the ksat maps tool, or another InSAR dataset in the same format. To download an appropriate csv from ksat tools, use the polygon selection tool and click the green CSV button.'''
    fileloc = '%s' % filename
    print('Importing InSAR data from: "%s".' % fileloc)
    print('\tFilesize found to be %s.' % file_size(fileloc))
    csvData = pd.read_csv(fileloc,sep=sep,skipinitialspace=True)
    
    if 'X' in csvData.columns:
        print('\tRenaming columns from X/Y to latitude/longitude.')
        csvData.rename(columns={'X':'Longitude', 'Y':'Latitude'},inplace=True)
    
    if 'latitude' in csvData.columns:
        print('\tRenaming columns from latitude/longitude to Latitude/Longitude.')
        csvData.rename(columns={'longitude':'Longitude', 'latitude':'Latitude'},inplace=True)
    
    print('\tChecking if any of the date columns start with the letter D and removing that character.')
    A = [tit for tit in csvData.columns if tit.startswith('D20')]
    if len(A) >0:
        print("\t\tRenaming date columns from DXXXXX to XXXXX.")
#	date_idxs = np.where(np.isin(csvData.columns,A)) 
        B = [tit.replace('D','') for tit in A]
        for i in range(len(A)):
            csvData.rename(columns={A[i]:B[i]},inplace=True)
		

    print('\tSuccessfully imported data of size %ix%i.\n' % (csvData.shape[0],csvData.shape[1]) )
    return csvData

def import_GPS_stations():
    '''Reads in the UNAVCO list of all GPS stations.'''
    
    print("Checking if we're in Linux or Mac...")
    if ospath.exists('/home/Users/mlees/Documents/RESEARCH/bigdata/GPS'):
        mac=1
        linux=0
        print("\tWe're in Mac, looking for downloaded GPS data accordingly.")
        file='/Users/mlees/Documents/RESEARCH/ground_deformation/GPS/gage_gps.igs08.txt'
    elif ospath.exists('/home/mlees/bigdata/GPS'):
        linux=1
        mac=0
        print("\tWe're in Linux, looking for downloaded GPS data accordingly.")
        file='/home/mlees/ground_deformation/GPS/gage_gps.igs08.txt'
    else:
        print("\tUnable to find downloaded GPS data. Check for bigdata/GPS folder. Aborting.")
        sys.exit()

    gpsfile = pd.read_csv(file,header=5, skipinitialspace=True, delimiter=", ")
    gpsfile.rename(columns={'Latitude (deg)':'Latitude','Longitude (deg)': 'Longitude'},inplace=True)
    return gpsfile


def import_GPS_data(filename,path_to_folder='data'):
    '''imports GPS data when the data is a "nam08" csv as downloaded from here: https://www.unavco.org/instrumentation/networks/status/pbo/overview/P566.'''
    fileloc = '%s/%s' % (path_to_folder,filename)
    print('Importing GPS data from: "%s".' % fileloc)
  
    # COMMENTED STUFF IS OLD!!
#    X = np.genfromtxt(fileloc,delimiter=',')
#    
#    file=open(fileloc,'r')
#    ftot=file.readlines()
#    datesgps = [ftot[i].rstrip().split(',')[0] for i in range(len(ftot))]
#    file.close()
#    
#    datesgps = datesgps[1:]
#    
#    gpsdates_list = [dt.strptime(date, '%Y-%m-%d').date() for date in datesgps]
#    
#    gpsdates = date2num(gpsdates_list)
    
    csvdata= pd.read_csv(fileloc,header=11,delimiter=',',skipinitialspace=True)
    datesgps = csvdata['Date']
    gpsdates_list = [dt.strptime(date, '%Y-%m-%d').date() for date in datesgps]    
    gpsdates = date2num(gpsdates_list)
    
    Data = np.vstack((csvdata['North (mm)'],csvdata['East (mm)'],csvdata['Vertical (mm)'])) 
    
    
    print('Successfully imported GPS data of size %i.\n' % len(gpsdates) )
    
    #return X[1:,1:6], gpsdates
    return Data,gpsdates

def import_GPS_data_new(station_name,update=0,ref_frame='nam08',solution='pbo',fileformat='csv',startdate=False,enddate=False,StartEndDateFormat='%d/%m/%Y'):
    '''imports GPS data from station name. Returns [data, dates]. Assumes data is stored tidily in /Users/mlees/Documents/RESEARCH/bigdata/GPS/; if it isn't, see the script in that folder which downloads new data.
    Start and End dates can be specified. Default format for that is '%d/%m/%Y', but can also be 'DateNum'. '''
    filename = '%s.%s.%s.%s' % (station_name,solution,ref_frame,fileformat)
    print("Checking if we're in Linux or Mac...")
    if ospath.exists('/Users/mlees/Documents/RESEARCH/bigdata/GPS'):
        mac=1
        linux=0
        print("\tWe're in Mac, looking for downloaded GPS data accordingly.")
        fileloc = '/Users/mlees/Documents/RESEARCH/bigdata/GPS/%s/%s' % (station_name,filename)        
    elif ospath.exists('/home/mlees/bigdata/GPS'):
        linux=1
        mac=0
        print("\tWe're in Linux, looking for downloaded GPS data accordingly.")
        fileloc = '/home/mlees/bigdata/GPS/%s/%s' % (station_name,filename)        
    else:
        print("\tUnable to find downloaded GPS data. Check for bigdata/GPS folder. Aborting.")
        sys.exit()
        
    
    if update:
        print('Attempting to fetch latest GPS data; currently only works on Mac.')
        os.system('/Users/mlees/Documents/RESEARCH/bigdata/GPS/fetch_GPS_data.sh %s' % station_name)
        
    print('Importing GPS data from: "%s".' % fileloc)

    if solution != 'pbo':
        csvdata = pd.read_csv(fileloc,header=0,delim_whitespace=True)
        csvdata.rename(columns={'YYMMMDD':'Date'},inplace=True)
        datesgps = csvdata['Date']
        gpsdates_list = [dt.strptime(date, '%y%b%d').date() for date in datesgps]    
        gpsdates = date2num(gpsdates_list)

    else:
        csvdata= pd.read_csv(fileloc,header=11,delimiter=',',skipinitialspace=True)
        datesgps = csvdata['Date']
        gpsdates_list = [dt.strptime(date, '%Y-%m-%d').date() for date in datesgps]    
        gpsdates = date2num(gpsdates_list)
    
    #Data = np.vstack((csvdata['North (mm)'],csvdata['East (mm)'],csvdata['Vertical (mm)'])) 
    if startdate:
        if enddate:
            if StartEndDateFormat =='DateNum':
                print('\tFiltering to between STARTDATE and ENDDATE.')
                idxs = np.argwhere((startdate <= gpsdates) & (gpsdates <= enddate))
                gpsdates = gpsdates[idxs]   
                csvdata = csvdata.iloc[idxs.flatten()]
            else:
                    
                            
                print('\tFiltering to between STARTDATE and ENDDATE.')
            #plt.xlim([dt.strptime(startdate, '%d/%m/%Y').date(),dt.strptime(enddate, '%d/%m/%Y').date()])
                idxs = np.argwhere((date2num(dt.strptime(startdate, '%d/%m/%Y').date()) <= gpsdates) & (gpsdates <= date2num(dt.strptime(enddate, '%d/%m/%Y').date())))
                gpsdates = gpsdates[idxs]   
                csvdata = csvdata.iloc[idxs.flatten()] 
    
    dodgy_titles = ['__east(m)','_north(m)','____up(m)']
    dodgy_titles_dictionary = {'__east(m)':'East (mm)','_north(m)':'North (mm)','____up(m)':'Vertical (mm)'} # Sometimes the headers have these unhappy names and we need to fix that.    
    if any(np.isin(csvdata.columns,dodgy_titles)):
        print('\tImported data has weird headings and units of metres. Correcting both.')
        for i in np.where(np.isin(csvdata.columns,dodgy_titles))[0]:
            print('\t\tChanging m to mm.')
            csvdata[csvdata.columns[i]] = csvdata[csvdata.columns[i]]*1000
        
        print('\t\tRenaming headings according to %s.' % dodgy_titles_dictionary)
        csvdata.rename(columns=dodgy_titles_dictionary,inplace=True)

    
    print('\tSuccessfully imported GPS time series of length %i.\n' % len(gpsdates) )
    
    #return X[1:,1:6], gpsdates
    return csvdata,gpsdates

def import_GPS_data_CAMPAIGN(stn):
    '''Returns DATES, SERIES for a Matt_Jacobus GPS station with name stn. Series is the vertical series in mm.'''
    
    passive_data = pd.read_excel('/Users/mlees/Documents/RESEARCH/ground_deformation/GPS/From_Matt_Jacobus/MLees_20200228.xlsx')

    dates = passive_data['YRMO'][passive_data['STATION']==stn]

    dates = [date2num(dt.strptime(date, '%Y%b').date()) for date in dates]
    data=FEET_TO_MM* passive_data['ELEf'][passive_data['STATION']==stn].values
    return dates,data


def import_kml_line(filename):
    '''import a single .kml line created in Google Earth. Note that this will probably import only the first segment of 'multi segment' lines. Which is fine......'''
    
    kml_file = filename # Name of the kml file
    
    # Load the file as a string, skipping the first line because for some reason fastkml cannot deal with that...
    with open(kml_file, 'rt', encoding="utf-8") as myfile:
        doc=myfile.readlines()[1:]
        myfile.close()
    doc = ''.join(doc) # gets it as a string
    
    # Using the very opaque fastkml module to parse out the features. I wonder if the length of features is 2 if it's a 2-segment line..?
    k = kml.KML()
    k.from_string(doc)
    features = list(k.features())
    
    # Extract the first feature and a LineString object corresponding to it!
    f1 = list(features[0].features())
    t = f1[0].geometry
    
    # Get the coordinates of the line's nodes.
    xy = t.xy
    x0 = xy[0][0]
    x1 = xy[0][1]
    y0 = xy[1][0]
    y1 = xy[1][1]
    
    return x0,x1,y0,y1

def import_kml_polygon(filename):
    '''import a single .kml polygon created in Google Earth. Should work in simple cases.......'''
    
    kml_file = filename # Name of the kml file
    
    # Load the file as a string, skipping the first line because for some reason fastkml cannot deal with that...
    with open(kml_file, 'rt', encoding="utf-8") as myfile:
        doc=myfile.readlines()[1:]
        myfile.close()
    doc = ''.join(doc) # gets it as a string
    
    # Using the very opaque fastkml module to parse out the features. I wonder if the length of features is 2 if it's a 2-segment line..?
    k = kml.KML()
    k.from_string(doc)
    features = list(k.features())
    
    # Extract the first feature and a LineString object corresponding to it!
    f1 = list(features[0].features())
    t = f1[0].geometry

    A = np.array(t.exterior.coords)
    Polylon = A[:,0]
    Polylat = A[:,1]
    
    return Polylon, Polylat

def import_reservoir_data(filename):
    '''Imports reservoir data, when the aforementioned data is of the format outlined here, taken from the Readme.txt in "Study_Area/Reservoir_Data":
        Contains daily reservoir level data for the reservoirs/lakes in the study area.

        Data source for these files: http://cdec.water.ca.gov/misc/daily_res.html
        To get the timespan you want, hack the URLs... for instance: http://cdec.water.ca.gov/dynamicapp/QueryDaily?s=TRM&end=2019-07-15&span=1600days.
    '''

    Data = pd.read_csv(filename)
    storage = Data['STORAGE AF']
    
    # Convert into a Numpy array
    storage = [s.replace(',' , '') for s in storage]
    storage = [s.replace('--' , '0') for s in storage] # no data is often denoted '--'
    storage = np.array([float(s) for s in storage])
    storage[np.where(storage==0)] = np.nan # I assume no months have 0.00 as their reservoir level, else those months would now not be plotted. (Reasonable..)
    
    dates= Data['DATE / TIME (PST)']
    dates= [dt.strptime(date, '%m/%d/%Y').date() for date in dates]
    dates = date2num(dates)
    return storage,dates


def import_well_seasonaltimeseries(filename):
    '''Imports a seasonal timeseries well dataset, which is in turn produced by a MATLAB script I also wrote. (see well_data_MATLAB or similar such folder).'''
    
    csvData = pd.read_csv(filename,sep=',',skipinitialspace=True)
    headings = list(csvData.columns.values)
    dates=headings[6:] # dates start in the 6th column

    dates2 = [date.replace('Fall','Sep') for date in dates]
    dates2 = [date.replace('Spring','May') for date in dates2]
    
    dates= [dt.strptime(date, '%b%Y').date() for date in dates2]
    dates = date2num(dates)
    return csvData, dates

#%% 2. Functions which extract subsets of InSAR data.

def extract_from_polygon(Polylon,Polylat,Data):
    '''Takes a Pandas Dataframe Data, and a polygon defined by it's (ordered) lon and lat coordinates, and returns a Pandas Datafame corresponding to data only within that polygon.'''
    
    print('Extracting from polygon.')
    print('\tStarting with %i pixels.' % len(Data))
    lat = np.array(Data['Latitude'])
    lon = np.array(Data['Longitude'])
        
    inbox = inpolygon(np.asarray(lon),np.asarray(lat),np.asarray(Polylon),np.asarray(Polylat))
    Datafilt = Data[inbox]
    print('\tExraction completed. New dataset has %i pixels.' % len(Datafilt))
    return Datafilt

def extract_series_from_latlon(lat,lon,Data,startdate=False,enddate=False,factor=1):
    '''Returns the time series for a given latitude and longitude pair. First finds the nearest pixel to your lat/lon, then extracts the series. Optionally scale the data by a factor (eg to go from LOS to vertical, etc).
        Start and End dates can be specified. Default format for that is '%d/%m/%Y'.

    Returns: dates, Series.'''
    
    dist = np.array(np.sqrt((Data["Latitude"] - lat)**2 + (Data["Longitude"] - lon)**2))
    if np.min(dist) >= 0.5:
        raise Exception("No pixels found within 0.5 degree of given lat/lon.")
    index = np.argmin(dist)

    headings = list(Data.columns.values)
    idx_firstdate=np.where([head.startswith('20') for head in headings])[0][0]
    dates = headings[idx_firstdate:]
    dates_list = [dt.strptime(date, '%Y%m%d').date() for date in dates]
    dates = date2num(dates_list)
    
    Series = factor * Data.iloc[index,idx_firstdate:]
    
    if startdate:
        if enddate:
        
            print('\tFiltering to between STARTDATE and ENDDATE.')        
            idxs = np.argwhere((date2num(dt.strptime(startdate, '%d/%m/%Y').date()) <= dates)  & (dates <= date2num(dt.strptime(enddate, '%d/%m/%Y').date())))
            dates = dates[idxs]   
            Series = Series.iloc[idxs.flatten()]

    
    
    return dates,Series

def filter_mean_correlation(Data,threshold):
	'''Returns a data instance containing only pixels with mean_correlation greater than threshold.'''
	print('\tFiltering by mean correlation %.2f. Input data of length %i' % (threshold,len(Data)))
	Data_filt = Data[Data.Mean_Corr >= threshold]
	print('\tDone. Output data of length %i' % len(Data_filt))
	return Data_filt
		

#%% 3. Functions which do stuff with GPS data - eg project, smooth, make relative.
	
def GPSsmooth(GPSdataframe,GPSdates,smooth_window=11):
    '''Takes a GPS dataframe and returns a smoothed version. Smooth_window is the number of days to smooth over.
    Returns:      GPStwelvedayavg_NORTH, GPStwelvedayavg_EAST, GPStwelvedayavg_UP, GPSUPdates_padded'''

    GPSUP,GPSUPdates_padded = nanpad_series(GPSdates,GPSdataframe['Vertical (mm)'])
    GPSEAST,GPSEASTdates_padded = nanpad_series(GPSdates,GPSdataframe['East (mm)'])
    GPSNORTH,GPSNORTHdates_padded = nanpad_series(GPSdates,GPSdataframe['North (mm)'])

    GPStwelvedayavg_UP = convolve(GPSUP,np.array([1]*smooth_window)/smooth_window,preserve_nan=True,boundary='extend')
    GPStwelvedayavg_EAST = convolve(GPSEAST,np.array([1]*smooth_window)/smooth_window,preserve_nan=True,boundary='extend')
    GPStwelvedayavg_NORTH = convolve(GPSNORTH,np.array([1]*smooth_window)/smooth_window,preserve_nan=True,boundary='extend')
    
    return GPStwelvedayavg_NORTH, GPStwelvedayavg_EAST, GPStwelvedayavg_UP, GPSUPdates_padded


def GPSproject(GPS_North,GPS_East,GPS_Up,gpsdates,azimuth,look_angle):
    '''Takes 3 gps components and projects them to LOS direction.
    Returns: projected_GPS'''
    
    normal_vector = [np.sin(np.deg2rad(look_angle)) * np.sin(np.deg2rad(azimuth)),-np.sin(np.deg2rad(look_angle)) * np.cos(np.deg2rad(azimuth)),np.cos(np.deg2rad(look_angle))]
    
    projected_GPS = [np.dot([GPS_North[i],GPS_East[i],GPS_Up[i]],normal_vector) for i in range(len(gpsdates))]

    return projected_GPS

def correct_for_jump(series,dates,date_of_jump,dateformat='dd/mm/yyyy',jumplength=10):
    '''If you give this function a series and its corresponding dates, it will correct a jump at date_of_jump. date_of_jump should be format 'dd/mm/yyyy'.
    I GOT IN A RIGHT MESS OVER THIS SO IT PROBABLY DOESNT WORK.'''


    print('FUNCTION NOT FINISHED -- I DO NOT THINK THIS WORKS!!!')
    
    if dateformat == 'dd/mm/yyyy':
        print('\tCorrecting for jump in series at %s.' % date_of_jump)
        date_of_jump2 = date2num(dt.strptime(date_of_jump, '%d/%m/%Y'))
        idx = np.argmin(np.abs(dates-date_of_jump2))
        if ~np.isnan(series[idx]):
            series[idx-jumplength:] = series[idx-jumplength:] - (series[idx]-series[idx-jumplength]) # correct the jump
            series[idx-jumplength:idx] = np.nan
        else:
            print('This will likely now break as your jumpdate is a nan.')
            E = series[idx-30:idx]
            goodvalues = ~np.isnan(E)
            goodargs = np.argwhere(goodvalues)
            tmp = np.argmin(np.abs(goodargs-30))
            firstarg = goodargs[tmp][0] - 30

            F = series[idx+30:idx]
            goodvalues = ~np.isnan(E)
            goodargs = np.argwhere(goodvalues)
            tmp = np.argmin(np.abs(goodargs-30))
            secondarg = goodargs[tmp][0] - 30


            series[(idx+firstarg):] = series[(idx+firstarg):] - (series[idx+secondard]-series[idx+firstarg]) # correct the jump

    else:
        
        print('\tCorrecting for jump in series at %s.' % date_of_jump)
        idx = np.argmin(np.abs(dates-date_of_jump))
        series[idx:] = series[idx:] - (series[idx]-series[idx-1]) # correct the jump
        

    return series

#%% 4. Functions which plot things.

def form_kml_timeseries(Data,outname,every_x_pixels=1,plotscalefactor=1,corr_threshold=False):
	'''Takes an InSAR Data class and creates time series plots for every pixel in that class. Then, packages these plots into a .kml and saves it as outname.'''

	foldername=outname.split('.')[0]
	os.system('mkdir timeseries_plots_%s' % foldername)

	currentdir = os.getcwd()
	
	kml = simplekml.Kml()

	plt.ioff()

	f =plt.figure(figsize=(18,12))
	ax = f.add_subplot(111)

	print("Starting to form plots for each pixel, doing every %ith pixel. Progress comes every %ith pixel." % (every_x_pixels, every_x_pixels*500))

	for i in range(0,len(Data),every_x_pixels):
		if not (i/every_x_pixels)%500:
			print('%i out of %i completed.' % (i, len(Data)))

		if not corr_threshold:
			plot_series_latlon(Data,lat=Data['Latitude'].iloc[i],lon=Data['Longitude'].iloc[i],factor=plotscalefactor,newFig=False)
	
		if corr_threshold:
			plot_series_latlon(Data,lat=Data['Latitude'].iloc[i],lon=Data['Longitude'].iloc[i],factor=plotscalefactor,newFig=False,title_noints_threshold=True)

		sns.set_context('poster')
			#sns.set(font_scale=2)
	
		plt.xlabel('Date',fontsize=26)
		plt.ylabel('Deformation (mm)',fontsize=26)
		plt.savefig('timeseries_plots_%s/timeseries_%i.jpg' % (foldername,i), quality=20)
		plt.cla() # clears the axis, ready for the next plot to be made. This should be the quickest way of doing this!

		kml.newpoint(coords=[(Data['Longitude'].iloc[i],Data['Latitude'].iloc[i])],description='<img style="max-width:500px;" src="%s/timeseries_plots_%s/timeseries_%i.jpg">' % ( currentdir,foldername,i))  # lon, lat, optional height
	
		kml.save(outname)


def plot_average_series(Data,avg='both',detrended=False,feet=False,newfig=True):
    '''Takes a panda Dataframe and plots the average time series. avg can be 'both','mean', or 'median'.'''
    
    if newfig:
        fig = plt.figure(figsize=(18,12))
        ax = fig.add_subplot(111)
    else:
        fig = plt.gcf()
        ax = plt.gca()
    
    headings = list(Data.columns.values)
    idx_firstdate=np.where([head.startswith('20') for head in headings])[0][0]
    print('\tFirst date is found in column %i' % idx_firstdate)
    dates = headings[idx_firstdate:]
    dates_list = [dt.strptime(date, '%Y%m%d').date() for date in dates]
    dates = date2num(dates_list)
    
    Series = Data[Data.columns[idx_firstdate:]].values
    
    if detrended:
        print('\t Detrending InSAR series for plot.')
        Series = scipy.signal.detrend(Series)
    
    if feet:
        Series = FEET_TO_MM * Series
    
    pal = sns.color_palette(palette="RdBu",n_colors=10).as_hex()[::-1]
    
    mean_def = np.mean(Series,axis=0)
    median_def = np.median(Series,axis=0)
    
    if avg == 'both': 
        ax.plot_date(dates,mean_def,linestyle='solid',label='Mean')
        ax.plot_date(dates,median_def,linestyle='solid',label='Median')
        plt.legend()
    elif avg=='mean':
        ax.plot_date(dates,mean_def,linestyle='solid',label='Mean InSAR')
    elif avg=='median':
        ax.plot_date(dates,median_def,linestyle='solid',label='Median')
    else: print('Error. avg not correctly defined. Can be both, mean or median.')

    #ax.axhline(linestyle='dashed',color='black')
    plt.xlabel('Date')
    plt.ylabel('InSAR displacement (mm)')
    
#    dateticks = np.zeros(8)f
#    dateticks[0] = date.toordinal(date(2015,1,1))
#    dateticks[1] = date.toordinal(date(2015,7,1))
#    dateticks[2] = date.toordinal(date(2016,1,1))
#    dateticks[3] = date.toordinal(date(2016,7,1))
#    dateticks[4] = date.toordinal(date(2017,1,1))
#    dateticks[5] = date.toordinal(date(2017,7,1))
#    dateticks[6] = date.toordinal(date(2018,1,1))
#    dateticks[7] = date.toordinal(date(2018,7,1))    
#    
#    plt.xticks(dateticks)
#    ax.xaxis.set_major_formatter(DateFormatter('%b-%Y') )
    
    return fig, ax

def plot_series_latlon(Data,lat,lon,factor=1,newFig=True,title_noints_threshold=False,rezero_on_date=False):
    '''Plots the time series for a given latitude and longitude pair. First finds the nearest pixel to your lat/lon, then plots the series. Optionally scale the data by a factor (eg to go from LOS to vertical, etc).''' 
    dist = np.array(np.sqrt((Data["Latitude"] - lat)**2 + (Data["Longitude"] - lon)**2)) 
    if np.min(dist) >= 1:
        raise Exception("No pixels found within 1 degree of given lat/lon.") 
    index = np.argmin(dist) 
    if newFig: 
        fig = plt.figure(figsize=(18,12)) 
        ax = fig.add_subplot(111) 
    else: 
        fig = plt.gcf() 
        ax = plt.gca() 
        
    headings = list(Data.columns.values) 
    idx_firstdate=np.where([head.startswith('20') for head in headings])[0][0] 
    dates = headings[idx_firstdate:] 
    dates_list = [dt.strptime(date, '%Y%m%d').date() for date in dates] 
    dates = date2num(dates_list)      
    Series = factor * Data.iloc[index,idx_firstdate:]  
    if rezero_on_date:
        Series = rezero_series(Series,dates,rezero_on_date)
    ax.plot_date(dates,Series,linestyle='solid') 

    if title_noints_threshold: 
	    plt.title('No interferograms = %i; correlation threshold = %.2f' % (Data.iloc[index,np.where([head=='Noints' for head in headings])[0][0]], Data.iloc[index,np.where([head=='Corr_threshold' for head in headings])[0][0]]))     
    return fig, ax 


def plot_line_with_boxes(x0,x1,y0,y1,BOXESX,BOXESY,lats,lons,fig,colours='RdBu',palette='forwards'):
    '''Takes a line from (x0,y0) to (x1,y1) which has been segmented into boxes with corners given by the arrays BOXESX and BOXESY. These arrays should be created by the 'segment line to boxes' function. All units should be lat/lon.'''
        
    coords1 = (y0,x0)
    coords2 = (y1,x1)
    Len = geopy.distance.distance(coords1, coords2).m
    
    # get vectors with length 1m parallel and perpendicular to the line
    linevector = np.array([x1-x0,y1-y0])
    
    stamen_terrain = cimgt.Stamen('terrain-background')
    ax1 = fig.add_axes([0.125,0.15,0.75,0.75],projection=stamen_terrain.crs)
    ax1.add_image(stamen_terrain, 11)
    ax1.set_extent([x0+0.1, x1-0.1, y1-(y0-y1), y0+(y0-y1)])
    ax1.plot([x0,x1],[y0,y1],'k--',linewidth=0.5,transform=ccrs.Geodetic())    
    ax1.gridlines(draw_labels=True)
    
    if palette=='backwards':
        pal = sns.color_palette(palette=colours,n_colors=np.size(BOXESX,0)).as_hex()[::-1]
    else:
        pal = sns.color_palette(palette=colours,n_colors=np.size(BOXESX,0)).as_hex()     
        
    for i in range(len(lats)-1):
        ax1.plot(BOXESX[i,:],BOXESY[i,:],c=pal[i],linewidth=3,transform=ccrs.Geodetic())
        ax1.text(lons[i]+0.5*(lons[i+1]-lons[i]),lats[i]+0.5*(lats[i+1]-lats[i]),'%i' % i, transform=ccrs.Geodetic(),horizontalalignment='center',verticalalignment='center')

    return ax1

def plot_map_finaltimestep(Data,backgroundquality=10,projection="M8i",region="tight",pixelsize='250e',cmap='viridis'):
    '''This function uses the PyGMT package to produce a nice, simple map showing the spatial variation of deformation between the first and last timestep. At the moment, PyGMT does not provide facility for a scalebar or title. This function creates a file called 'points.tmp.pdf' which has to be manually removed afterwards. This function doesn't deal with Tom's newer data in which X and Y are called latitude and longitude.

    Optional arguments:

    backgroundquality is a number, typically between 10 and 12, selecting the resolution of the background satellite image. Lower number = lower resolution.

    projection is a string containing a GMT encoded proction, for instance an 8 inch figure with Mercator projection would be 'M8i'.

    region is a string which should read either "CVSouth" or "tight", which selects the plotting region to either be the entire Southern CV, or a 'tight' 10% margin around the data extent.

    pixelsize is pixel width in GMT-speak; so, the suffix 'e' means metre, etc. See GMT documentation for more. '''
    # This bit deals with the region; in future, put this in a separate function???
    if region=="CVSouth":
        R = [-125,-115,30,40]
    elif region=="tight":
        xrange = np.max(Data["Longitude"]) - np.min(Data["Longitude"])
        yrange = np.max(Data["Latitude"]) - np.min(Data["Latitude"])
        xmin = np.min(Data["Longitude"]) - 0.1 * xrange
        xmax = np.max(Data["Longitude"]) + 0.1 * xrange
        ymin = np.min(Data["Latitude"]) - 0.1 * yrange
        ymax = np.max(Data["Latitude"]) + 0.1 * yrange
        R = [xmin,xmax,ymin,ymax]
    else:
        R=False

    print('Plotting a nice map of InSAR data.')


    print('\tOpening GMT figure.')
    fig = pygmt.Figure() # initiate the gmt figure
    #fig.coast(region=[-125,-115,30,40],projection="M8i",shorelines=True,frame=True)

    print('\tPlotting background at detail level %i.' % backgroundquality)
    fig.grdimage("/Users/mlees/Documents/RESEARCH/bigdata/Google_Satellite_Imagery/SouthCentralValley_zoom%s.tif" % backgroundquality,projection=projection, frame=True, region=R) # Plot the background
    fig.grdimage("/Users/mlees/Documents/RESEARCH/bigdata/Google_Satellite_Imagery/NorthCentralValley_zoom%s.tif" % backgroundquality,projection=projection, frame=True, region=R) # Plot the background


    # Normalise the displacement on the final timestep
    print('\tNormalising displacement (pygmt currently only plots values between 0 and 1).')
    finaltime = list(Data.columns.values)[-1]
    normalised_displacement=0.5*(Data[finaltime]/ np.max([np.max(Data[finaltime]),np.abs(np.min(Data[finaltime]))]) + 1)

    print('\tPlotting InSAR data.')
    fig.plot(x=Data["Longitude"],y=Data["Latitude"],style="J-%s" % pixelsize,color=normalised_displacement,pen=False,cmap=cmap) # style = J-250e means 250m edge length rectangles

    print('\tRendering, saving, displaying.')
    fig.savefig("points.tmp.pdf",show=True,crop=True)

    print("\tDone.\n")


def plot_individual_gps_station_vertical(station_name,sln_type='pbo',startdate=False,enddate=False,update=0):
    '''A quick plot of the vertical timeseries for an individual GPS station.
    
    Startdate: string in format 'dd/mm/yyyy'. Ditto for enddate. Update refers to whether we try and download new GPS data.'''
    print('Plotting vertical time series for station %s.' % station_name )

    if sln_type=='pbo':
        data,dates = import_GPS_data_new(station_name,update=update)
        plt.plot_date(dates,data['Vertical (mm)'])

    elif sln_type=='ngl':
        data,dates = import_GPS_data_new(station_name,solution='ngl',ref_frame='NA',fileformat='tenv3')
        plt.plot_date(dates,data['Vertical (mm)'])

    
    
    if startdate:
        if enddate:
            plt.xlim([dt.strptime(startdate, '%d/%m/%Y').date(),dt.strptime(enddate, '%d/%m/%Y').date()])
    
    plt.title(station_name)
    plt.ylabel('Vertical motion / mm')

#%% 5. Functions which fit or detrend the data.
    
def fit_straight_line_to_series(Series,dates):
    '''Fits a straight line and returns misfit, est_slope, est_intercept.'''
    N = len(Series) # number of data points
    t = dates
    #f = 1.15247 # Optional!! Advised not to use
    data = Series # create artificial data with noise
    
    guess_intercept = Series[0]
    guess_slope = (np.max(Series) - np.min(Series)) / (t[-1]-t[0])
    
    # we'll use this to plot our first estimate. This might already be good enough for you
    #data_first_guess = guess_std*np.sin(guess_freq*t+guess_phase) + guess_mean
    
    # Define the function to optimize, in this case, we want to minimize the difference
    # between the actual data and our "guessed" parameters
    optimize_func = lambda x: x[0]*(t-t[0]) +x[1] - data
    est_slope, est_intercept = leastsq(optimize_func, [guess_slope, guess_intercept])[0]
    
    
    data_fit=est_slope * (t - t[0]) + est_intercept
    misfit = np.sum( np.sqrt(np.abs((Series**2 - data_fit**2))))/len(dates)#    plt.figure()

    return misfit,est_slope,est_intercept


def fit_sinusoid_to_series(Series,dates):
    
    bnds = ((0, 30), (0, 400),(-20,400),(0,100))
    N = len(Series) # number of data points
    t = dates
    #f = 1.15247 # Optional!! Advised not to use
    data = Series # create artificial data with noise
    
    guess_mean = np.mean(data)
    #guess_std = 3*np.std(data)/(2**0.5)/(2**0.5)
    guess_period = 365
    guess_phase = guess_period/4 - (t[np.argwhere(np.diff(Series)<=0)[0][0]] - t[0])
    #guess_phase = 190
    guess_amp = (np.max(Series) - np.min(Series)) /2
    guess = [guess_amp,guess_period,guess_phase,guess_mean]
    # we'll use this to plot our first estimate. This might already be good enough for you
    #data_first_guess = guess_std*np.sin(guess_freq*t+guess_phase) + guess_mean
    
    # Define the function to optimize, in this case, we want to minimize the difference
    # between the actual data and our "guessed" parameters
    func = lambda x: x[0]* np.sin( (2*np.pi*(t-t[0]-x[2])) / x[1]  ) + x[3]
    
    
    optimize_func = lambda x: np.linalg.norm(x[0]* np.sin( (2*np.pi*(t-t[0]-x[2])) / x[1]  ) + x[3] - data)
    sln = scipy.optimize.minimize(optimize_func, guess,bounds=bnds)
    est_amp, est_period, est_phase, est_mean = sln.x
    misfit = sln.fun / len(t)
    return misfit,est_amp,est_period,est_phase,est_mean





#%% 6. Miscellaneous functions.

def segment_line_to_boxes(x0,x1,y0,y1, spacing, width):
    ''' Returns two arrays containing the lon and lat of boxes, where the boxes are equally spaced along the line defined by two points x0,y0 and x1,y1 (in lat/lon) with spacing and width given in metres.'''
        
    # Calculate the length of the line
    coords1 = (y0,x0)
    coords2 = (y1,x1)
    Len = geopy.distance.distance(coords1, coords2).m
    
    nopoints = int(np.floor(Len/spacing)) # calculate number of boxes
    
    lats = np.linspace(y0,y1,num=nopoints) # get lat/lon coordinates for those boxes
    lons = np.linspace(x0,x1,num=nopoints)
        
    # get unit normal vector (1m) to the line
    linevector = np.array([x1-x0,y1-y0])
    perpvector = np.empty_like(linevector)
    perpvector[0] = -linevector[1]
    perpvector[1] = linevector[0]
    NormLen = geopy.distance.distance((0,0),(perpvector[0],perpvector[1])).m    
    unitnorm = 1/NormLen * perpvector
        
    BOXESX = np.zeros((len(lats)-1,5))
    BOXESY = np.zeros_like(BOXESX)
    
    for i in range(0,len(lats)-1):
        
        topright = (lons[i]-unitnorm[0]*width, lats[i]-unitnorm[1]*width)
        topleft = (lons[i+1]-unitnorm[0]*width, lats[i+1]-unitnorm[1]*width)
        botright = (lons[i]+unitnorm[0]*width, lats[i]+unitnorm[1]*width)
        botleft = (lons[i+1]+unitnorm[0]*width, lats[i+1]+unitnorm[1]*width)
        
        rectx = [topright[0], topleft[0], botleft[0], botright[0],topright[0]]
        recty = [topright[1], topleft[1], botleft[1], botright[1],topright[1]]
        
        BOXESX[i,:] = rectx
        BOXESY[i,:] = recty
    
    return BOXESX, BOXESY, lats, lons

def remove_rows_all_zeros(Data):
    '''Takes a Pandas InSAR dataframe and returns one where rows containing only zeros are removed. Initially designed with the TRE dataset in mind.'''
    print('Removing rows with only zeros.')
    print("\tDon't worry, this one tends to hang for ages but it does work..give it a minute or so.")
    data_raw = Data.drop(['Longitude','Latitude'],axis=1)
    booool = (data_raw.T != 0).any()
    data_filtered = Data[booool]
    return data_filtered

def remove_rows_all_nans(Data):
    '''Takes a Pandas InSAR dataframe and returns one where rows containing only nans are removed.'''
    print('Removing rows with only nans.')
    print("\tDon't worry, this one may hang for ages but it does work..give it a minute or so.")
    headings = list(Data.columns.values)
    datesheadings = [heading for heading in headings if '20' in heading] # assume they all contain the string '20...'
    data_timeseries = Data[datesheadings]
    booool = (~np.isnan(data_timeseries.T)).any()
    data_filtered = Data[booool]
    return data_filtered


def rezero_series(series,dates,zerodate,zerodateasfloat=0,nansearchdist=6):
    '''Takes a data series (InSAR, GPS, heads) and the list of dates which correspond to it. Then it zeros the data at the date closest to that specified by the string zerodate. Zerodate = 'MMM-YYYY' eg 'Jan-2018'. If the value at the closest date is a nan, this will search for nansearchdist either side of that value to find the closest non-nan.
    
    Returns newdata.'''
    if not zerodateasfloat:
        dateasnum = date2num(dt.strptime(zerodate, '%b-%Y').date())
    else:
        dateasnum=zerodate
    idx = (np.abs(dates - dateasnum)).argmin()
    if not np.isnan(series[idx]):       
        newdata = series - series[idx]
    else:
        if np.sum(np.isnan(series[idx-nansearchdist:idx+nansearchdist])) >= 1:
            E = series[idx-nansearchdist:idx+nansearchdist]
            goodvalues = ~np.isnan(E)
            goodargs = np.argwhere(goodvalues) - nansearchdist
            tmp = np.argmin(np.abs(goodargs))
            bestarg = goodargs[tmp]
            newdata = series - series[idx + bestarg]
            
            
    return newdata

def get_mean_series(Data):
    '''Takes a Pandas Dataframe and returns single dataseries corresponding to the mean deformation at each timestep in the origianl data.'''
    headings = list(Data.columns.values)
    idx_firstdate=np.where([head.startswith('20') for head in headings])[0][0]

    Series = Data[Data.columns[idx_firstdate:]].values
    mean_def = np.mean(Series,axis=0)
    n = Data.shape[0]
    #median_def = np.median(Series,axis=0)
    return mean_def,n


def inpolygon(xq, yq, xv, yv):
    shape = xq.shape
    xq = xq.reshape(-1)
    yq = yq.reshape(-1)
    xv = xv.reshape(-1)
    yv = yv.reshape(-1)
    q = [(xq[i], yq[i]) for i in range(xq.shape[0])]
    p = path.Path([(xv[i], yv[i]) for i in range(xv.shape[0])])
    return p.contains_points(q).reshape(shape)

def get_dates(Data):
    '''Takes a Pandas Dataframe and returns a list of numeric dates in a format which they can be plotted using plt.plot_date().'''
    headings = list(Data.columns.values)
    idx_firstdate=np.where([head.startswith('20') for head in headings])[0][0]
    dates = headings[idx_firstdate:]
    dates_list = [dt.strptime(date, '%Y%m%d').date() for date in dates]
    dates = date2num(dates_list)
    return dates

def create_dateticks():
    '''Returns a nice premade list of dateticks every 3 months from 2015 to 2018. Helpful shortcut.'''
    dateticks = np.zeros(17)
    dateticks[0] = date.toordinal(date(2015,1,1))
    dateticks[1] = date.toordinal(date(2015,4,1))
    dateticks[2] = date.toordinal(date(2015,7,1))
    dateticks[3] = date.toordinal(date(2015,10,1))
    dateticks[4] = date.toordinal(date(2016,1,1))
    dateticks[5] = date.toordinal(date(2016,4,1))
    dateticks[6] = date.toordinal(date(2016,7,1))
    dateticks[7] = date.toordinal(date(2016,10,1))
    dateticks[8] = date.toordinal(date(2017,1,1))
    dateticks[9] = date.toordinal(date(2017,4,1))
    dateticks[10] = date.toordinal(date(2017,7,1))
    dateticks[11] = date.toordinal(date(2017,10,1))
    dateticks[12] = date.toordinal(date(2018,1,1))
    dateticks[13] = date.toordinal(date(2018,4,1))
    dateticks[14] = date.toordinal(date(2018,7,1))
    dateticks[15] = date.toordinal(date(2018,10,1))
    dateticks[16] = date.toordinal(date(2019,1,1))
    return dateticks


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def file_size(file_path):
    """
    this function will return the file size
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)

def kml_to_txt_polygon(kml_filename,outputfilename):
    data=import_kml_polygon(kml_filename)
    dat = np.c_[data[0],data[1]]
    np.savetxt(outputfilename,dat)

def nanpad_series(dates,series):
    '''Takes a series and its corresponding dates. If there are any missing days in dates, this returns a new series with the missing days filled with 'nans'.'''
    firstdate = np.min(dates)
    finaldate = np.max(dates)
    
    dates_new = np.arange(firstdate,finaldate+1,1)
    
    nanpadded_series = np.empty_like(dates_new)
    nanpadded_series[:] = np.nan
    
    nanpadded_series[np.isin(dates_new,dates)] = series
    
    return nanpadded_series,dates_new


#%%
        
print('\tModules import done.\n')
