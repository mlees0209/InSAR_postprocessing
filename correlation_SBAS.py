#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:24:12 2019

SBAS with only interferograms above correlation threshold test.

@author: mlees
"""

#import sys
#sys.path.append('../../../postprocessing_scripts')
#from postprocessing import *
#
#Data = InSAR_data('drummer15_allinterferograms/')

#C = read_single_pixel_correlation(Data,1222866,1182)
Pass = np.array(C)>=0.65
filelist = np.array(Data.correlation_filelist)[Pass]
pairslist = [file.split('/')[-1].split('.cc')[0] for file in filelist]
Data_filt = Data.filter_by_pairslist(pairslist)
A = form_Tm_matrix(Data_filt)
rank=np.linalg.matrix_rank(A)
print('Rank is %i' % rank)
print('Shape is %i x %i' % (np.shape(A)[0],np.shape(A)[1]))

X = read_single_pixel_unwrapped(Data_filt,1222866,1182)

refpixelidx = find_idx_from_latlon(Data,(37.084,-119.739))
print('Reading Reference Pixel Interferograms.')
X_ref = read_single_pixel_unwrapped(Data,refpixelidx,length)

v = np.matmul(np.linalg.pinv(A),X)

phi_temp=[0.5 * wavelength / (2*np.pi) *  np.dot(v[0:1+i],Data_filt.deltaT_unique[0:i+1]) for i in range(len(Data_filt.deltaT_unique))]

phi=np.zeros(len(phi_temp) +1)
phi[1:] = phi_temp
plt.plot_date(Data_filt.dates_list_unique_ordinal,phi)
plt.ylabel('Displacement/cm')
plt.show()

#%%




def calc_series_from_corr_threshold(Data,C,threshold):
    result = np.empty(len(Data.dates_list_unique))
    result[:]= np.nan
    Pass = np.array(C)>=threshold
    filelist = np.array(Data.correlation_filelist)[Pass]
    pairslist = [file.split('/')[-1].split('.cc')[0] for file in filelist]
    Data_filt = Data.filter_by_pairslist(pairslist)
    A = form_Tm_matrix(Data_filt)
    rank=np.linalg.matrix_rank(A)
    print('Rank is %i' % rank)
    print('Shape is %i x %i' % (np.shape(A)[0],np.shape(A)[1]))
    noint = len(Data_filt.unwrapped_filelist)
    nodates = len(Data_filt.dates_list_unique)
    print('Reading unwrapped interferograms')
    X = read_single_pixel_unwrapped(Data_filt,1222866,1182)
    
    print('Doing the inversion')
    v = np.matmul(np.linalg.pinv(A),X-np.array(X_ref)[Pass])
    
    print('Integrating')
    phi_temp=[0.5 * wavelength / (2*np.pi) *  np.dot(v[0:1+i],Data_filt.deltaT_unique[0:i+1]) for i in range(len(Data_filt.deltaT_unique))]
    

    
    phi=np.zeros(len(phi_temp) +1)
    phi[1:] = phi_temp
    
    indices=np.isin(Data.dates_list_unique,Data_filt.dates_list_unique)
    result[indices]=phi
    
    return Data_filt,result,noint,nodates

#%%
for corr in [0.8,0.75,0.7,0.65,0.6,0.5,0.0]:
    Data_filt,result,noint,nodates = calc_series_from_corr_threshold(Data,C,corr)
    plt.plot_date(Data.dates_list_unique_ordinal,result,'.-',label='corr=%.2f; no. interferograms = %i; no dates = %i' % (corr,noint,nodates))

plt.legend()
