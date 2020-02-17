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
from datetime import datetime
from matplotlib import path
import struct
import copy

class InSAR_data():
    '''Class for holding InSAR data. Takes argument directory, which should be a directory containing interfero'''
    def __init__(self, directory):
        self.directory = directory
        
        print('Checking directory exists.')
        
        if not os.path.exists(directory):
            raise Exception("%s does not exist. Aborting." % directory)
        else:
            print('Directory %s found.\n' % directory)
            
        #print('Directory %s found with %i files.\n' % (directory,len(glob.glob(directory+'/*'))))
             
        print('Making unwrapped interferogram filelist.')
        self.unwrapped_filelist=[]
        if glob.glob(directory+'/unwrappedfiles'):
            for direc in glob.glob(directory+'/unwrappedfiles*'):
                print('\tLooking for .u files in %s.' % direc)
                unwrapped_filelisttmp = [os.path.join(direc,file) for file in os.listdir(direc) if file.endswith(".u")]
                self.unwrapped_filelist.extend(unwrapped_filelisttmp)
        else:
            print('No unwrapped files found in folder '+directory+'/unwrappedfiles.')
            
            
        print('Making correlation files filelist.')
        self.correlation_filelist=[]
        if glob.glob(directory+'/correlationfiles'):
            for direc in glob.glob(directory+'/correlationfiles*'):
                correlationdirectory=direc
                print('\tLooking for .cc files in %s.' % correlationdirectory)
                correlation_filelisttmp = [os.path.join(correlationdirectory,file) for file in os.listdir(correlationdirectory) if file.endswith(".cc")]
                self.correlation_filelist.extend(correlation_filelisttmp)
        else:
            print('No correlation files found in folder '+directory+'/correlationfiles.')
            self.correlation_filelist=[]
            
        print('Making wrapping files filelist.')
        self.wrapping_filelist=[]
        if glob.glob(directory+'/flatfiles'):
            for direc in glob.glob(directory+'/flatfiles*'):
                self.flatdirectory=direc
                print('\tLooking for .flat files in %s.' % self.flatdirectory)
                wrapping_filelisttmp = [os.path.join(self.flatdirectory,file) for file in os.listdir(self.flatdirectory) if file.endswith(".flat")]
                self.wrapping_filelist.extend(wrapping_filelisttmp)
        else:
            print('No wrapping interferograms found in folder '+directory+'/flatfiles.')
            

        print(len(self.wrapping_filelist),"wrapping interferograms,",len(self.unwrapped_filelist),"unwrapped interferograms and",len(self.correlation_filelist),"correlation files found in",directory,'.\n')
        
        if not glob.glob(directory+'/dem.rsc'):
            raise Exception("No dem.rsc file found in folder "+directory+" you silly fart.")
        
        self.demrsc=np.genfromtxt(directory+'/dem.rsc')
        self.rawlength=int(self.demrsc[0,1]*self.demrsc[1,1])        
        print("InSAR data found with rawlength",self.rawlength,".")

        
        print("Initialising (empty) arrays for wrapping, unwrapped, and correlation files.")
        self.wrapping_interferograms=np.zeros((len(self.wrapping_filelist),self.rawlength))
        self.unwrapped_interferograms=np.zeros((len(self.unwrapped_filelist),self.rawlength))
        self.correlation_array=np.zeros((len(self.correlation_filelist),self.rawlength))

        
        
        self.unwrapped_dates_list = [name.split('/')[-1].split('.u')[0] for name in self.unwrapped_filelist]
        firstdate = [datetime.strptime(date.split('_')[0],'%Y%m%d').toordinal() for date in self.unwrapped_dates_list]
        seconddate = [datetime.strptime(date.split('_')[1],'%Y%m%d').toordinal() for date in self.unwrapped_dates_list]
        self.deltaT = np.array(seconddate) - np.array(firstdate)
        self.dates_list_unique = np.unique(np.concatenate(([date.split('_')[0] for date in self.unwrapped_dates_list],[date.split('_')[1] for date in self.unwrapped_dates_list])))
        self.dates_list_unique_ordinal = [datetime.strptime(date,'%Y%m%d').toordinal() for date in self.dates_list_unique]
        self.deltaT_unique = [self.dates_list_unique_ordinal[i+1] - self.dates_list_unique_ordinal[i] for i in range(len(self.dates_list_unique_ordinal) - 1)]
        print("Wrapping interferograms represent passes ranging from",np.min(self.deltaT),"to",np.max(self.deltaT),"days apart.")
    
    def plot_temporal_coverage(self):
        '''Makes a scatter plot showing the temporal coverage of the interferograms held.'''
        print('Plotting temporal coverage.')
        
        self.dates_list_unique_ordinal = [datetime.strptime(date,'%Y%m%d').toordinal() for date in self.dates_list_unique]
        plt.plot_date(self.dates_list_unique_ordinal,np.ones_like(self.dates_list_unique_ordinal))
    
    def read_correlation_files(self,plot=False):
        print(len(self.correlation_filelist),"correlation files found; initialising array and reading files in.")
        for i in range(len(self.correlation_filelist)):
            with open(self.correlation_filelist[i], 'rb') as fid:
                correlation_array_temp = np.fromfile(fid, np.float32)
                # Make the correct shape...
                nr=int(self.demrsc[0,1])
                naz=int(self.demrsc[1,1])
                temparray = np.reshape(correlation_array_temp,(naz,2*nr))
                temparray=temparray[:,nr:]
                self.correlation_array[i]=temparray.flatten()
                print("    Read in file",i,"/",len(self.correlation_filelist))
        if plot:
            print("    Done; plotting a random one as sanity check.")
            randomnum=np.random.randint(0,len(self.correlation_filelist))
            plt.figure()
            self.quick_plot(self.correlation_array[randomnum,:])
        else:
            print("    Done.")
            
    def read_correlation_file(self,idx,plot=False,StoreInRAM=True):
        '''Reads in a single .cc correlation file corresponding to idx. By default, this function doesn't plot, but does store the file in RAM under self.correlation_array[idx,:].'''
        if not hasattr(self,'correlation_array'):
            if StoreInRAM:
                print('Correlation_array not initialised. Initialising...')
                print(len(self.correlation_filelist),"correlation files found; initialising     array.")
                self.correlation_array=np.zeros((len(self.correlation_filelist),self.rawlength))

        with open(self.correlation_filelist[idx], 'rb') as fid:
            correlation_array_temp = np.fromfile(fid, np.float32)
            # Make the correct shape...
            nr=int(self.demrsc[0,1])
            naz=int(self.demrsc[1,1])
            temparray = np.reshape(correlation_array_temp,(naz,2*nr))
            temparray=temparray[:,nr:]
            if StoreInRAM:
                print("Storing in self.correlation_array. (don't do this if you're reading in many 100s of files; RAM will crash and you'll explode in a ball of dead CPU.")
                self.correlation_array[idx]=temparray.flatten()
            print("    Read in file %s" % self.correlation_filelist[idx])
        if plot:
            print("    Plotting.")
            plt.figure()
            #self.quick_plot(self.correlation_array[idx,:])
            self.quick_plot(temparray.flatten())
            
        else:
            print("    Done.")

        


    def recalc_deltaT(self):
        dates = [name.split('/')[-1].split('.cc')[0] for name in self.correlation_filelist]
        firstdate = [datetime.strptime(date.split('_')[0],'%Y%m%d').toordinal() for date in dates]
        seconddate = [datetime.strptime(date.split('_')[1],'%Y%m%d').toordinal() for date in dates]
        self.deltaT = np.array(seconddate) - np.array(firstdate)
        print("Interferograms represent passes ranging from",np.min(self.deltaT),"to",np.max(self.deltaT),"days apart.")
            
    def read_unwrapped_interferograms(self,plot=False):
        print(len(self.unwrapped_filelist),"unwrapped interferograms found; initialising array and reading files in.")
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
            self.quick_plot_unwrapped(randomnum)
        else:
            print("    Done.")
    
    def read_unwrapped_interferogram(self,idx,plot=False,StoreInRAM=True):
        '''Reads in individual unwrapped interferogram, given by idx.'''
        array_temp = np.fromfile(self.unwrapped_filelist[idx], np.float32)
        # Make the correct shape...
        nr=int(self.demrsc[0,1])
        naz=int(self.demrsc[1,1])
        temparray = np.reshape(array_temp,(naz,2*nr))
        temparray = temparray[:,nr:]

        if StoreInRAM:
            print("Storing in self.unwrapped_interferograms. (don't do this if you're reading in many 100s of files; RAM will crash and you'll explode in a ball of dead CPU.")
            self.unwrapped_interferograms[idx]=temparray.flatten()
            print("    Read in file %s" % self.unwrapped_filelist[idx])
        if plot:
            print("    Plotting.")
            #self.quick_plot_unwrapped(idx)
            self.quick_plot(temparray.flatten())
        else:
            print("    Done.")

    
    def read_wrapping_interferograms(self,plot=False):
        print(len(self.wrapping_filelist),"wrapping interferograms found; initialising array and reading files in.")
        self.wrapping_interferograms=np.zeros((len(self.wrapping_filelist),self.rawlength))
        for i in range(len(self.wrapping_filelist)):
            with open('%s/%s' % (self.flatdirectory,self.wrapping_filelist[i]), 'rb') as fid:
                wrapping_interferogram_temp = np.fromfile(fid, np.complex64)
                wrapping_interferogram_temp = np.angle(wrapping_interferogram_temp) # Get the phase from the complex valued number you read in.
                # Make the correct shape...
                nr=int(self.demrsc[0,1])
                naz=int(self.demrsc[1,1])
                temparray = np.reshape(wrapping_interferogram_temp,(naz,2*nr))
                temparray=temparray[:,nr:]
                self.wrapping_interferograms[i]=temparray.flatten()

                print("    Read in file",i,"/",len(self.wrapping_filelist))
        if plot:
            print("    PLOT NOT YET SUPPORTED.")
#            randomnum=np.random.randint(0,len(self.unwrapped_filelist))
#            plt.figure()
#            self.quick_plot_interferogram(randomnum)
        else:
            print("    Done.")

    def read_wrapping_interferogram(self,idx,plot=False,StoreInRAM=True):
        '''Reads in a single .flat wrapping file corresponding to idx. By default, this function doesn't plot, but does store the file in RAM under self.wrapping_interferograms[idx,:].'''
        with open(self.wrapping_filelist[idx], 'rb') as fid:
            array_temp = np.fromfile(fid, np.complex64)
            array_temp = np.angle(array_temp)
            # Make the correct shape...
            nr=int(self.demrsc[0,1])
            naz=int(self.demrsc[1,1])
            temparray = np.reshape(array_temp,(naz,nr))
            if StoreInRAM:
                print("Storing in self.wrapping_interferograms. (don't do this if you're reading in many 100s of files; RAM will crash and you'll explode in a ball of dead CPU.")
                self.wrapping_interferograms[idx]=temparray.flatten()
            print("    Read in file %s" % self.wrapping_filelist[idx])
        if plot:
            print("    Plotting.")
            plt.figure()
            self.quick_plot(self.wrapping_interferograms[idx,:])
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
    
    def quick_plot_unwrapped(self,i):
        '''quick_plot_interferogram(i) plots the i'th interferogram (corresponding to entry i in unwrapped_filelist)'''
        if not(hasattr(self,'unwrapped_interferograms')):
            print('Interferograms not yet imported...importing...')
            self.read_unwrapped_interferograms()
        oned_array=self.unwrapped_interferograms[i,:]
        title=self.unwrapped_filelist[i].split('/')[-1]
        f=plt.figure()
        ax=f.add_subplot(111)
        self.quick_plot(oned_array)
        plt.text(0.1,0.9,title,fontsize=10,bbox=dict(facecolor='white',alpha=0.3),transform=ax.transAxes)
    
    def quick_plot_correlation(self,i):
        '''quick_plot_correlation(i) plots the i'th correlation file (corresponding to entry i in correlation_filelist)'''
#        if not(hasattr(self,'unwrapped_interferograms')):
#            print('Interferograms not yet imported...importing...')
#            self.read_unwrapped_interferograms()
        oned_array=self.correlation_array[i,:]
        title=self.correlation_filelist[i].split('/')[-1]
        #f=plt.figure()
        #ax=f.add_subplot(111)
        self.quick_plot(oned_array)
        plt.text(0.05,0.95,title,fontsize=10,bbox=dict(facecolor='white',alpha=0.3),transform=plt.gca().transAxes)

    def quick_plot_wrapping(self,i):
        '''quick_plot_correlation(i) plots the i'th correlation file (corresponding to entry i in correlation_filelist)'''
#        if not(hasattr(self,'unwrapped_interferograms')):
#            print('Interferograms not yet imported...importing...')
#            self.read_unwrapped_interferograms()
        oned_array=self.wrapping_interferograms[i,:]
        title=self.wrapping_filelist[i].split('/')[-1]
        #f=plt.figure()
        #ax=f.add_subplot(111)
        self.quick_plot(oned_array)
        plt.text(0.05,0.95,title,fontsize=10,bbox=dict(facecolor='white',alpha=0.3),transform=plt.gca().transAxes)

    
    def plot_all_interferograms(self):
        if not(hasattr(self,'unwrapped_interferograms')):
            print('Interferograms not yet imported...importing...')
            self.read_unwrapped_interferograms()
        for i in range(len(self.unwrapped_filelist)):
            title=self.unwrapped_filelist[i].split('/')[-1]
            f=plt.figure(figsize=(16,16))
            ax=f.add_subplot(111)
            self.quick_plot_raw(self.unwrapped_interferograms[i,:])
            plt.text(0.1,0.9,title,fontsize=12,bbox=dict(facecolor='white',alpha=0.3),transform=ax.transAxes)

    
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


    def find_latlon_from_idx(self,idx):
        if not hasattr(self,'lats'):
            self.create_latlon_arrays()
        lat = self.lats[idx]
        lon = self.lons[idx]
        latlon = [lat,lon]
        return latlon
    
    def read_amp_grid(self,gridfile):
        '''Reads in a gridded .nc GMT amplitude file, resampled to the dem.rsc size, so this grid can be used as a background for other plots.'''
    
    def plot_wrapping_interferogram(self,i,Amplitude):
        interferogram=np.reshape(self.wrapping_interferograms[i],(int(self.demrsc[1,1]),int(self.demrsc[0,1])))
        plt.imshow(Amplitude,cmap='gray',interpolation='spline16',vmin=0,vmax=np.mean(Amplitude)+1.25*np.std(Amplitude))
        plt.imshow(interferogram,cmap='hsv',alpha=0.4)
        title=self.wrapping_filelist[i].split('/')[-1]
        plt.text(0.05,0.95,title,fontsize=8,bbox=dict(facecolor='white',alpha=0.3),transform=plt.gca().transAxes)

        plt.colorbar()
    
    def filter_by_dateslist(self,dateslist):
        '''Returns a new InSAR_data instance with filelists filtered to only contain files corresponding to dates in dateslist. Useful if you want to keep only certain scenes.'''
        Data_new = self
        Data_new.correlation_filelist = [filename for filename in self.correlation_filelist if any(dates in filename for dates in dateslist)]
        Data_new.unwrapped_filelist = [filename for filename in self.unwrapped_filelist if any(dates in filename for dates in dateslist)]
        Data_new.unwrapped_dates_list = [name.split('/')[-1].split('.u')[0] for name in Data_new.unwrapped_filelist]
        firstdate = [datetime.strptime(date.split('_')[0],'%Y%m%d').toordinal() for date in Data_new.unwrapped_dates_list]
        seconddate = [datetime.strptime(date.split('_')[1],'%Y%m%d').toordinal() for date in Data_new.unwrapped_dates_list]
        Data_new.deltaT = np.array(seconddate) - np.array(firstdate)
        Data_new.dates_list_unique = np.unique(np.concatenate(([date.split('_')[0] for date in Data_new.unwrapped_dates_list],[date.split('_')[1] for date in Data_new.unwrapped_dates_list])))
        Data_new.dates_list_unique_ordinal = [datetime.strptime(date,'%Y%m%d').toordinal() for date in Data_new.dates_list_unique]
        Data_new.deltaT_unique = [Data_new.dates_list_unique_ordinal[i+1] - Data_new.dates_list_unique_ordinal[i] for i in range(len(Data_new.dates_list_unique_ordinal) - 1)]
        print("Wrapping interferograms represent passes ranging from",np.min(Data_new.deltaT),"to",np.max(Data_new.deltaT),"days apart.")

        return Data_new
    
    def filter_by_pairslist(self,pairslist):
        '''Returns a new InSAR_data instance with filelists filtered to only contain files corresponding to dates in pairslist. Useful if you want to keep only certain interferograms.'''
        Data_new = copy.copy(self)
        Data_new.correlation_filelist = [filename for filename in self.correlation_filelist if any(dates in filename for dates in pairslist)]
        Data_new.unwrapped_filelist = [filename for filename in self.unwrapped_filelist if any(dates in filename for dates in pairslist)]
        Data_new.unwrapped_dates_list = [name.split('/')[-1].split('.u')[0] for name in Data_new.unwrapped_filelist]
        firstdate = [datetime.strptime(date.split('_')[0],'%Y%m%d').toordinal() for date in Data_new.unwrapped_dates_list]
        seconddate = [datetime.strptime(date.split('_')[1],'%Y%m%d').toordinal() for date in Data_new.unwrapped_dates_list]
        Data_new.deltaT = np.array(seconddate) - np.array(firstdate)
        Data_new.dates_list_unique = np.unique(np.concatenate(([date.split('_')[0] for date in Data_new.unwrapped_dates_list],[date.split('_')[1] for date in Data_new.unwrapped_dates_list])))
        Data_new.dates_list_unique_ordinal = [datetime.strptime(date,'%Y%m%d').toordinal() for date in Data_new.dates_list_unique]
        Data_new.deltaT_unique = [Data_new.dates_list_unique_ordinal[i+1] - Data_new.dates_list_unique_ordinal[i] for i in range(len(Data_new.dates_list_unique_ordinal) - 1)]
        print("Wrapping interferograms represent passes ranging from",np.min(Data_new.deltaT),"to",np.max(Data_new.deltaT),"days apart.")

        return Data_new
    
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

#def read_single_pixel_unwrapped(filelist,pixelno,linelength):
#    ''' For list of files in fileslist, reads in each one, but only the specified pixel in each one.'''
#    X=[]
#    treadcum=0
#    tseekcum=0
#    tunpackcum=0
#    ttotalcum=0
#    for file in filelist:
#        ttotal=time.time()
#        if len(X) % 2000==0:         
#            print(str(len(X))+' / '+str(len(filelist)))
#            print('Reading time is %f' % treadcum)
#            print('Seeking time is %f' % tseekcum)
#            print('Unpacking time is %f' % tunpackcum)
#            print('Total time is %f' % ttotalcum)
#        with open(file,'rb') as binary_file:
#            binaryfile = open(file,'rb')
#            tseek=time.time()
#            
#            lineno=1+int(pixelno/linelength) # int rounds down which is what I want
#            pixelinline = pixelno % linelength
#            bitno = 4*(2*lineno -1 )* linelength + 4*pixelinline
#            #print(bitno)
#            binary_file.seek(bitno,0)
#            tseek=time.time() - tseek
#            tseekcum+=tseek
#            #print('T-seek = %f' % tseek)
#            
#            tread = time.time()
#            couple_bytes = binary_file.read(4)
#            tread = time.time() - tread
#            treadcum+=tread
#            #print('T-read = %f' % tread)
#            
#            tunpack= time.time()
#            [num] = struct.unpack('f',couple_bytes)
#            tunpack=time.time()-tunpack
#            tunpackcum+=tunpack
#            
#            X.append(num)
#            #binary_file.close()
#            
#            ttotal=time.time()-ttotal
#            ttotalcum+=ttotal
#    return X

def read_single_pixel_unwrapped(Data,pixelno,linelength):
    ''' For list of files in fileslist, reads in each one, but only the specified pixel in each one.'''
    X=[]
    treadcum=0
    tseekcum=0
    tunpackcum=0
    ttotalcum=0
    filelist=Data.unwrapped_filelist
    for file in filelist:
        with open(file,'rb') as binary_file:
            lineno=1+int(pixelno/linelength) # int rounds down which is what I want
            pixelinline = pixelno % linelength
            bitno = 4*(2*lineno -1 )* linelength + 4*pixelinline
            binary_file.seek(bitno,0)
            #tseek=time.time() - tseek
            #tseekcum+=tseek
            #print('T-seek = %f' % tseek)

            #tread = time.time()
            couple_bytes = binary_file.read(4)
            [num] = struct.unpack('f',couple_bytes)

            X.append(num)
            #binary_file.close()

            #ttotal=time.time()-ttotal
            #ttotalcum+=ttotal
    return X


def find_index_containing_string(List,string):
    idxz = [i for i, s in enumerate(List) if string in s]
    if len(idxz)==1:
        [idxz]=idxz
    return idxz


def form_Tm_matrix(Data):
    '''Takes an InSAR_data class and returns the corresponding Tm matrix. This only works if Data.dates_list_unique is ordered, which I don't think is guaranteed; check!'''
    N = len(Data.dates_list_unique)
    i=0
    Tm = np.zeros((len(Data.unwrapped_dates_list),N-1))
    for pair in Data.unwrapped_dates_list:
        date1=pair.split('_')[0]
        date2=pair.split('_')[1]
        date1_idx = find_index_containing_string(Data.dates_list_unique,date1)
        date2_idx = find_index_containing_string(Data.dates_list_unique,date2)
        #print(date1_idx)
        #print(date2_idx)
        A = np.zeros(N-1)
        A[date1_idx:date2_idx] = np.diff(Data.dates_list_unique_ordinal[date1_idx:date2_idx+1])
        #print(A)
        Tm[i,:] = A
        i+=1
    return Tm


def find_idx_from_latlon(Data,latlon):
    '''latlon should look like (lat,lon). Useful for finding a reference pixel.'''
    closestlat = np.min(np.abs(Data.lats-latlon[0]))
    latindxs = np.where(np.abs(Data.lats-latlon[0])==closestlat)

    closestlon = np.min(np.abs(Data.lons-latlon[1]))
    lonindxs = np.where(np.abs(Data.lons-latlon[1])==closestlon)

    [ref_pix_idx] = np.intersect1d(latindxs,lonindxs)
    return ref_pix_idx


def read_single_pixel_correlation(Data,pixelno,linelength):
        '''For a InSAR data instance, it reads the correlation file for the i'th pixel, where i= pixelno.'''
        filelist=Data.correlation_filelist
        X=[]
        for file in filelist:
                with open(file,'rb') as binary_file:
                        #binaryfile=open(file,'rb')
                        #print file
                        lineno=1+int(pixelno/linelength) # int rounds down which is what I want
                        pixelinline = pixelno % linelength
                        bitno = 4*(2*lineno -1 )* linelength + 4*pixelinline
                        binary_file.seek(bitno,0)
                        couple_bytes = binary_file.read(4)
                        [num] = struct.unpack('f',couple_bytes)
                        X.append(num)
        return X


def read_single_line_correlation(Data,lineno,linelength):
        '''For a InSAR data instance, it reads the correlation file for the i'th line, where i= lineno.'''
        filelist=Data.correlation_filelist
        X=np.zeros((len(Data.correlation_filelist),linelength))
        fileno=0
        for file in filelist:
                with open(file,'rb') as binary_file:
                        bitno = 4*(2*lineno + 1)* linelength
                        binary_file.seek(bitno,0)
                        couple_bytes = binary_file.read(4*linelength)
                        for i in range(linelength):
                            [num] = struct.unpack('f',couple_bytes[4*i:4*i + 4])
                            #print(num)
                            X[fileno,i] = num
                fileno+=1
        return X



def perform_SBAS(Data,refpixel):
    '''Function which will run a pixel-wise SBAS inversion on an InSAR data class. The inversion will take the data in the class, and from the list of unwrapped interferograms form a Tm matrix. Then, the inversion finds the reference pixel in the interferograms and reads in the unwrapped IGs for that pixel.  Next SBAS is performed on each pixel in turn.
    Data = InSAR_data class.
    refpixel = tuple (refpixellon, refpixellat)
    '''
    Tm = form_Tm_matrix(Data)
    Data.create_latlon_arrays()
    refpixelidx = find_idx_from_latlon(Data,refpixel)
    print('Reading in reference pixel.')
    RefPixelInterferograms = read_single_pixel_unwrapped(Data.unwrapped_filelist,refpixelidx,1182)
    phase_velocity = np.zeros((Data.rawlength,len(Data.dates_list_unique)-1))
    for i in range(Data.rawlength):
        print('Reading IGs for pixel %i.' % i)
        X = read_single_pixel_unwrapped(Data.unwrapped_filelist,i,1182)
        X_rel = np.array(X) - np.array(RefPixelInterferograms)
        phase_velocity[i,:] = np.matmul(np.linalg.pinv(Tm),X_rel)
        print(phase_velocity[i,:])
