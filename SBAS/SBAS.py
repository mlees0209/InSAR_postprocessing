#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 14:25:53 2019

@author: mlees
"""

#%% Set up and read in the InSAR data.

import sys
sys.path.append("/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/")
from postprocessing import *
import pandas as pd

directory = "/Users/mlees/drummer15/data1/mlees/CentralValleyProject1/Subsidence_Phase/interferograms"

data_imported = InSAR_data(directory)

flatlist=np.loadtxt(directory+'/flatlist', dtype='str')

data_imported.unwrapped_filelist = [os.path.join(directory,file).replace(".flat",".u") for file in flatlist]     
data_imported.correlation_filelist = [os.path.join(directory,file).replace(".flat",".cc") for file in flatlist]     


data_imported.read_unwrapped_interferograms()
data_imported.read_correlation_files()

data_imported.calc_mean_correlation()

data_imported.recalc_deltaT()

#%% Read in the matrix B, and do the SBAS inversion.

data_imported.create_latlon_arrays()

B = np.loadtxt(directory+'/Tm.out')

reference_pixel=[36.324, -119.229] # This is GPS station P566; chosen as it shows the least subsidence of any in the region of interest.

## Should probably make this into a function at some point...
#closestlat = np.min(np.abs(data_imported.lats-reference_pixel[0]))
#latindxs = np.where(np.abs(data_imported.lats-reference_pixel[0])==closestlat)
#
#closestlon = np.min(np.abs(data_imported.lons-reference_pixel[1]))
#lonindxs = np.where(np.abs(data_imported.lons-reference_pixel[1])==closestlon)
#
#ref_pix_idx = np.intersect1d(latindxs,lonindxs)

ref_pix_idx=data_imported.find_idx_from_latlon(reference_pixel)

ref_pix_phases=data_imported.unwrapped_interferograms[:,ref_pix_idx]

#refphase=np.mean(ref_pix_phases) # This is the way done in Yujie's script

velocity=np.zeros((len(data_imported.lats),10))

print("Starting the SBAS inversion, takes a bit of time.")
for i in range(len(data_imported.lats)):
    if(i%50000 == 0):
        print('i = %i out of %i' % (i,len(data_imported.lats)))
    
    # weight by coherence
    w = data_imported.correlation_array[:,i]/np.max(data_imported.correlation_array[:,i])
    W = np.diag(w)
    Bw = np.matmul(np.sqrt(W),B)
    d = np.array(data_imported.unwrapped_interferograms[:,i]) - ref_pix_phases[:,0] # This is My Way (so probably wrong)
    dw = np.matmul(np.sqrt(W),d)
    #d = np.array(data_imported.unwrapped_interferograms[:,i]) - refphase # This is Yujie's way (so probably right)

    velocity[i,:] = np.matmul(np.linalg.pinv(Bw),dw)

#%% Convert velocity to displacement in mm.

wavelen = 60 # wavelength in mm

#sub_centre=[36.0382, -119.472]
sub_centre=[35.8347,-119.944]

ind_subcentre=data_imported.find_idx_from_latlon(sub_centre)


timegaps = np.genfromtxt(directory+'/timedeltas.out')

phi = np.zeros((306240,11))

for n in range(1,len(timegaps)+1):
    phi[:,n] = phi[:,n-1] + timegaps[n-1] * velocity[:,n-1]

t=np.zeros(len(timegaps)+1)
t[1:] = t[0]+np.cumsum(timegaps)

disp = phi * wavelen/(4*np.pi)
#%% Put into a "Tom format" dataframe to work with.

data_imported.create_latlon_arrays()

LOS_E = 0.66
LOS_N = 0.11
LOS_Up = -0.74

los=np.ones_like(data_imported.lats)
LOS_E = LOS_E * los
LOS_N = LOS_N * los
LOS_Up = LOS_Up * los

#pixelsize=["100e"]*len(LOS_E) # in metres

azimuth=80
azimuth=azimuth*los

numpyarrayOUT=np.column_stack((data_imported.lats,data_imported.lons,LOS_E,LOS_N,LOS_Up,azimuth,data_imported.mean_correlation,disp))

dates=data_imported.dates_list_unique



df = pd.DataFrame(data=numpyarrayOUT,columns=np.concatenate((['latitude'],['longitude'],['LOS_East'],['LOS_North'],['LOS_up'],['Azimuth'],['Mean_Correlation'],dates)))

mask=data_imported.mean_correlation>0.3

numpyarrayOUTmask=np.column_stack((data_imported.lats[mask],data_imported.lons[mask],LOS_E[mask],LOS_N[mask],LOS_Up[mask],azimuth[mask],data_imported.mean_correlation[mask],disp[mask]))
dfmask = pd.DataFrame(data=numpyarrayOUTmask,columns=np.concatenate((['latitude'],['longitude'],['LOS_East'],['LOS_North'],['LOS_up'],['Azimuth'],['Mean_Correlation'],dates)))

#dfmask.to_csv('subsidence_phase_SBAS1.csv',index=False)

#np.savetxt('testout.txt',numpyarrayOUT,header="latitude longitude %s %s %s" % (t[0],t[1],t[2]))
    


#%% Mask by coherence
    
mask=data_imported.mean_correlation>0.4




#%% Plot things

vmin=np.min(phi)
vmax = np.max(phi)

for i in range(len(t)):
    
    plt.figure()
    #quick_plot(phase_total,data_imported.demrsc)
    plt.scatter(data_imported.lons[mask],data_imported.lats[mask],s=1,c=phi[:,i][mask], vmin=vmin, vmax=vmax)
    plt.colorbar()
    plt.title('Cumulative phase change after %i days' % t[i])
    plt.savefig('cumphasechange_%iDAYS.tmp.png' % t[i])

plt.figure()
quick_plot(data_imported.mean_correlation,data_imported.demrsc)
plt.title('Mean correlation')

plt.figure()
plt.plot(t,phi[ind_subcentre,:].transpose())
plt.title('Subsidence centre timeseries')


plt.figure()
plt.plot(t,phi[ref_pix_idx,:].transpose())
plt.title("Reference Pixel Timeseries")