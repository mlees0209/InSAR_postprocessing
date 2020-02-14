#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 17:41:09 2019

Plots a NASA InSAR dataset as time series at each pixel, then exports as a kml. If you enter a number for 'every x pixels', then only every x'th pixel has a timeseries plotted. (for v large datasets). There is a bit further down which removes all zero pixels and removes all pixels outside of the Central Valley polygon; can remove this if you want.

@author: mlees
"""

import sys

if len(sys.argv) < 1:
    print('Usage: form_kml_NASA_project.py infile [every_x_pixels]')
    sys.exit(1)


sys.path.append('/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts')
from InSAR_postSBASprocessing import *


dataset=sys.argv[1]
print("Removing .txt at the end of the filename. If your file doesn't end in .txt this won't work, dummy!")
foldername=dataset.split('.txt')[0]
print('New foldername is '+foldername)

if sys.argv[2:]:
	step=int(sys.argv[2])
else:
	step=1	

try: data
except NameError: data = import_InSAR_csv(dataset) # NEed to change Sep for ' ' vs csv.

try: data_filtered
except NameError: data_filtered = remove_rows_all_zeros(data)

C= import_kml_polygon('/Users/mlees/Documents/RESEARCH/Understanding_Valley/InSAR_signal_analysis/Polygons/CV_larger.kml')
Lons= C[0]
Lats = C[1]
data_filtered = extract_from_polygon(Lons,Lats,data_filtered)


#data_filtered = data


os.system('mkdir timeseries_plots_%s' % foldername)

currentdir = os.getcwd()
    
import simplekml
kml = simplekml.Kml()

# def create_plot_of_fit(Series,dates,amplitude,period,phase,mean):
#     plt.plot_date(dates,Series,'.',label='Detrended data')
#     plt.plot_date(dates,amplitude* np.sin( (2*np.pi*(dates-dates[0]-phase)) / period  ) + mean,'-',label='Fitted sinusoid')
#     plt.title('amp = %.1f \n phase = %.1f \n period = %.1f' % (amplitude,phase,period))
# 
#     plt.ylabel('Deformation (mm)')
#     plt.legend()



plt.ioff()

f =plt.figure(figsize=(18,12))
ax = f.add_subplot(111)

print("Starting to form plots for each pixel, doing every %ith pixel. Progress comes every %ith pixel." % (step, step*500))

for i in range(0,len(data_filtered),step):
    if not (i/step)%500:
        print('%i out of %i completed.' % (i, len(data_filtered)))

    plot_series_latlon(data_filtered,lat=data_filtered['Latitude'].iloc[i],lon=data_filtered['Longitude'].iloc[i],factor=1,newFig=False)
    sns.set_context('poster')
    #sns.set(font_scale=2)
    
    plt.xlabel('Date',fontsize=26)
    plt.ylabel('Deformation (mm)',fontsize=26)
    plt.savefig('timeseries_plots_%s/timeseries_%i.jpg' % (foldername,i), quality=20)
    plt.cla() # clears the axis, ready for the next plot to be made. This should be the quickest way of doing this!

    kml.newpoint(coords=[(data_filtered['Longitude'].iloc[i],data_filtered['Latitude'].iloc[i])],description='<img style="max-width:500px;" src="%s/timeseries_plots_%s/timeseries_%i.jpg">' % ( currentdir,foldername,i))  # lon, lat, optional height
    
    
kml.save("fitted_timeseries_%s.kml" % foldername)
