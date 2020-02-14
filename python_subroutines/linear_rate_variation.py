#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 16:15:50 2019

@author: mlees
"""
import pandas as pd
import sys
sys.path.append("/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/python_subroutines")
from postprocessing import *
import seaborn as sns

directory='/Users/mlees/drummer15/data1/mlees/CentralValleyProject1/Subsidence_Phase/interferograms'

data=InSAR_data(directory)
data.read_unwrapped_interferograms()
data.calc_mean_correlation()
data.create_latlon_arrays()

#%%
linearrate = create_linear_stack_naive(data.unwrapped_interferograms,data.deltaT,data.demrsc)

example=np.array([data.lons.transpose(),data.lats.transpose(),data.mean_correlation.transpose(),linearrate.transpose()])
example2 = np.vstack((example,data.unwrapped_interferograms))

columns=['longitude','latitude','mean_correlation','linear_estimate']
names=[data.unwrapped_filelist[i].split('/')[-1] for i in range(len(data.unwrapped_filelist))]
columns = np.hstack((columns, names))

output = pd.DataFrame(example2.transpose(),columns=columns)

polyLat=[36.16,36.16,36.04,36.04]
polyLon=[-119.28,-119.15,-119.15,-119.28]
datanew=extract_from_polygon(polyLon,polyLat,output)

meanrate=spatial_mean(datanew,'linear_estimate')

#%%

sns.set_context("notebook")

dates = [name.split('/')[-1].split('.u')[0] for name in names]
firstdates = [datetime.strptime(date.split('_')[0],'%Y%m%d').toordinal() for date in dates]
seconddates = [datetime.strptime(date.split('_')[1],'%Y%m%d').toordinal() for date in dates]

startdate=np.min(firstdates)
enddate=np.max(seconddates)
x=np.linspace(startdate,enddate)
y=meanrate*x
y = y-np.min(y)
plt.figure()

for i in range(len(names)):  
    slope=spatial_mean(datanew,names[i]) * 5.5/(2*np.pi) / data.deltaT[i]
    firstdate = firstdates[i]
    seconddate=seconddates[i]
    plt.plot_date([firstdate,seconddate],[(firstdate-startdate)*meanrate,(firstdate-startdate)*meanrate + (seconddate-firstdate)*slope],'k.--')
    
plt.plot_date(x,y,'-',linewidth=5,label='Best Fit Linear Rate')
plt.ylabel('Net subsidence (cm)')
plt.legend()

for i in range(len(names)):  
    slope=spatial_mean(datanew,names[i]) * 5.5/(2*np.pi) / data.deltaT[i]
    firstdate = firstdates[i]
    seconddate=seconddates[i]
    plt.plot_date([firstdate,seconddate],[(firstdate-startdate)*meanrate,(firstdate-startdate)*meanrate + (seconddate-firstdate)*slope],'k.')

plt.gca().invert_yaxis()