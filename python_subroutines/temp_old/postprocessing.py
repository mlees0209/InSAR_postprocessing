#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 09:35:28 2019

@author: mlees
"""

import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import numpy.ma as ma
from datetime import datetime
from matplotlib import path


class InSAR_data():
    def __init__(self, directory):
        self.directory = directory
        
        if not glob.glob(directory+'/*.u'):
            raise Exception("No unwrapped interferograms found in folder"+directory)
            
        self.unwrapped_filelist = [os.path.join(directory,file) for file in os.listdir(directory) if file.endswith(".u")]     
        self.correlation_filelist = [os.path.join(directory,file) for file in os.listdir(directory) if file.endswith(".cc")]     

        print(len(self.unwrapped_filelist),"unwrapped interferograms and",len(self.correlation_filelist),"correlation files found in",directory)
        
        if not glob.glob(directory+'/dem.rsc'):
            raise Exception("No dem.rsc file found in folder "+directory+" you silly fart.")
        
        self.demrsc=np.genfromtxt(directory+'/dem.rsc')
        self.rawlength=int(self.demrsc[0,1]*self.demrsc[1,1])        
        print("InSAR data found with rawlength",self.rawlength)
        
        dates = [name.split('/')[-1].split('.cc')[0] for name in self.correlation_filelist]
        firstdate = [datetime.strptime(date.split('_')[0],'%Y%m%d').toordinal() for date in dates]
        seconddate = [datetime.strptime(date.split('_')[1],'%Y%m%d').toordinal() for date in dates]
        self.deltaT = np.array(seconddate) - np.array(firstdate)
        print("Interferograms represent passes ranging from",np.min(self.deltaT),"to",np.max(self.deltaT),"days apart.")
        
    def read_correlation_files(self,plot=False):
        print(len(self.correlation_filelist),"correlation files found; initialising array and reading files in.")
        self.correlation_array=np.zeros((len(self.correlation_filelist),2*self.rawlength))
        for i in range(len(self.correlation_filelist)):
            with open(self.correlation_filelist[i], 'rb') as fid:
                self.correlation_array[i] = np.fromfile(fid, np.float32)
                print("    Read in file",i,"/",len(self.correlation_filelist))
        if plot:
            print("    Done; plotting a random one as sanity check.")
            randomnum=np.random.randint(0,len(self.correlation_filelist))
            plt.figure()
            self.quick_plot_raw(self.correlation_array[randomnum,:])
        else:
            print("    Done.")
            
    def read_unwrapped_interferograms(self,plot=False):
        print(len(self.unwrapped_filelist),"unwrapped interferograms found; initialising array and reading files in.")
        self.unwrapped_interferograms=np.zeros((len(self.unwrapped_filelist),self.rawlength))
        for i in range(len(self.unwrapped_filelist)):
            with open(self.unwrapped_filelist[i], 'rb') as fid:
                unwrapped_interferogram_temp = np.fromfile(fid, np.float32)
                # Make the correct shape...
                nr=int(self.demrsc[0,1])
                naz=int(self.demrsc[1,1])
                temparray = np.reshape(unwrapped_interferogram_temp,(naz,2*nr))
                temparray=temparray[:,nr:]
                self.unwrapped_interferograms[i]=temparray.flatten()

                print("    Read in file",i,"/",len(self.unwrapped_filelist))
        if plot:
            print("    Done; plotting a random one as sanity check.")
            randomnum=np.random.randint(0,len(self.unwrapped_filelist))
            plt.figure()
            self.quick_plot_interferogram(randomnum)
        else:
            print("    Done.")
    
    def read_dem(self,plot=False):
        print('Before this command will work, you need to create a downscaled DEM called "elevation_downscaled.dem" with associated .rsc file in the data directory.')
        with open(os.path.join(directory,'elevation_downscaled.dem'),'rb') as fid:
            self.dem=np.fromfile(fid,np.int16)
            print("    Read in DEM")
        if plot:
            plt.figure()
            self.quick_plot(self.dem)
    
    def quick_plot_interferogram(self,i):
        '''quick_plot_interferogram(i) plots the i'th interferogram (corresponding to entry i in unwrapped_filelist)'''
        if not(hasattr(self,'unwrapped_interferograms')):
            print('Interferograms not yet imported...importing...')
            self.read_unwrapped_interferograms()
        oned_array=self.unwrapped_interferograms[i,:]
        title=self.unwrapped_filelist[i].split('/')[-1]
        f=plt.figure()
        ax=f.add_subplot(111)
        self.quick_plot_raw(oned_array)
        plt.text(0.75,0.9,title,fontsize=10,bbox=dict(facecolor='white',alpha=0.3),transform=ax.transAxes)
    
    def plot_all_interferograms(self):
        if not(hasattr(self,'unwrapped_interferograms')):
            print('Interferograms not yet imported...importing...')
            self.read_unwrapped_interferograms()
        for i in range(len(self.unwrapped_filelist)):
            title=self.unwrapped_filelist[i].split('/')[-1]
            f=plt.figure()
            ax=f.add_subplot(111)
            self.quick_plot_raw(self.unwrapped_interferograms[i,:])
            plt.text(0.75,0.9,title,fontsize=12,bbox=dict(facecolor='white',alpha=0.3),transform=ax.transAxes)

    
    def quick_plot_raw(self,oned_array):
        ''' Takes a 1d array of length naz x (2*nr) and does a quick and dirty plot.'''
        nr=int(self.demrsc[0,1])
        naz=int(self.demrsc[1,1])
        tempplot = np.reshape(oned_array,(naz,2*nr))
        tempplot=tempplot[:,nr:]
        plt.imshow(tempplot,filternorm=1)
        plt.colorbar()
        
    def quick_plot(self,oned_array):
        ''' Takes a 1d array of length naz x nr and does a quick and dirty plot.'''
        nr=int(self.demrsc[0,1])
        naz=int(self.demrsc[1,1])
        tempplot = np.reshape(oned_array,(naz,nr))
        plt.imshow(tempplot,filternorm=1)
        plt.colorbar()


    def calc_mean_correlation(self,plot=False,save=False,**kwargs):
        '''Calculate the mean average correlation for the imported InSAR data. Can do a quick and dirty plot of the result with Plot=True, and can save it with save=True. If save=True, also specify filename='FILENAME' else an error will be raised. '''
        if not(hasattr(self,'correlation_array')):
            self.read_correlation_files()
        print("Calculating mean correlation.")    
        self.mean_correlation=np.mean(self.correlation_array,axis=0) # take the mean
        # grab every other line only.
        nr=int(self.demrsc[0,1])
        naz=int(self.demrsc[1,1])
        temparray = np.reshape(self.mean_correlation,(naz,2*nr))
        temparray=temparray[:,nr:]
        temparray=temparray.flatten()
        self.mean_correlation=temparray
        if plot:
            print("    Done; plotting a random one as sanity check.")
            plt.figure()
            self.quick_plot(self.mean_correlation)
        else:
            print("    Done.")
        if save:
            if 'filename' not in kwargs:
                raise Exception("Please specify filename in order to save.")
            else:
                filename=kwargs['filename']
                print("Saving mean correlation as",filename)
                self.mean_correlation.astype('float32').tofile(filename) # save as float32 format

                print("    Done.")
                
    def create_latlon_arrays(self):
        # grab info from demrsc.
        nlon=int(self.demrsc[0,1])
        nlat=int(self.demrsc[1,1])
        minlon=self.demrsc[2,1]
        minlat=self.demrsc[3,1]
        lonstep=self.demrsc[4,1]
        latstep=self.demrsc[5,1]

        lon = np.linspace(minlon,minlon+lonstep*nlon,num=nlon)
        lat = np.linspace(minlat,minlat+latstep*nlat,num=nlat)
        self.lats = np.repeat(lat,nlon) 
        self.lons = np.tile(lon,nlat)
   
def create_linear_stack_naive(unwrapped_interferograms,deltaT,demrsc,save=False,**kwargs):
    '''Give this function the stuff it requires and it will estimate a linear deformation rate over those interferograms. The units outputted are cm/day.'''
    
    weightedstack=np.zeros_like(unwrapped_interferograms[0,:])
    
    for i in range(len(deltaT)):
        weightedstack+= unwrapped_interferograms[i,:] 
        
    linear_stack_vel_estimate =5.5/(2*np.pi) * weightedstack/np.sum(deltaT) # multiplying by 5.5/2pi gives rates in cm/day. (wavelength is 5.5cm)
    
    # grab every other line only.
#    nr=int(demrsc[0,1])
#    naz=int(demrsc[1,1])
#    temparray = np.reshape(linear_stack_vel_estimate,(naz,2*nr))
#    temparray=temparray[:,nr:]
#    temparray=temparray.flatten()
#    linear_stack_vel_estimate=temparray

    
    if save:
        if 'filename' not in kwargs:
            raise Exception("Please specify filename in order to save.")
        else:
            filename=kwargs['filename']
            print("Saving linear stack velocity estimate as",filename)
            linear_stack_vel_estimate.astype('float32').tofile(filename) # save as float32 format

            print("    Done.")
    
    return linear_stack_vel_estimate

def quick_plot(oned_array,demrsc):
    ''' Takes a 1d array of length naz x nr and does a quick and dirty plot.'''
    nr=int(demrsc[0,1])
    naz=int(demrsc[1,1])
    tempplot = np.reshape(oned_array,(naz,nr))
    plt.imshow(tempplot,filternorm=1)
    plt.colorbar()
    

def extract_from_polygon(Polylon,Polylat,Data):
    '''Takes a Pandas Dataframe Data, and a polygon defined by it's (ordered) lon and lat coordinates, and returns a Pandas Datarfame corresponding to data only within that polygon.'''
    
    lat = np.array(Data['latitude'])
    lon = np.array(Data['longitude'])
        
    inbox = inpolygon(np.asarray(lon),np.asarray(lat),np.asarray(Polylon),np.asarray(Polylat))
    Datafilt = Data[inbox]
    return Datafilt

def inpolygon(xq, yq, xv, yv):
    shape = xq.shape
    xq = xq.reshape(-1)
    yq = yq.reshape(-1)
    xv = xv.reshape(-1)
    yv = yv.reshape(-1)
    q = [(xq[i], yq[i]) for i in range(xq.shape[0])]
    p = path.Path([(xv[i], yv[i]) for i in range(xv.shape[0])])
    return p.contains_points(q).reshape(shape)

def spatial_mean(Data,Field):
    '''Takes a Pandas Dataframe and averages the field Field over the entire spatial extent of the dataframe. Returns a single value.'''
    averaged_value = np.mean(Data['%s' % Field])
    return averaged_value