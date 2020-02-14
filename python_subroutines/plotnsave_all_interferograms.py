#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 13:35:18 2019

@author: mlees
"""

import sys
sys.path.append("/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts")
from postprocessing import *

if len(sys.argv) < 1:
    print('Usage: plotnsave_all_interferograms.py directory')
    print('  You screwed up, ERROR')
    sys.exit(1)

directory = sys.argv[1]
data=InSAR_data(directory)
data.read_unwrapped_interferograms()
#%%

for i in range(len(data.unwrapped_filelist)):
    title=data.unwrapped_filelist[i].split('/')[-1]
    f=plt.figure(figsize=(12,8))
    ax=f.add_subplot(111)
    nr=int(data.demrsc[0,1])
    naz=int(data.demrsc[1,1])
    tempplot = np.reshape(5.5/(2*np.pi) * data.unwrapped_interferograms[i,:],(naz,nr))
    plt.imshow(tempplot,filternorm=1)
    cbar= plt.colorbar()
    cbar.set_label('LOS Subsidence / cm')
    plt.text(0.75,0.97,title,fontsize=10,bbox=dict(facecolor='white',alpha=0.3),transform=ax.transAxes)
    plt.savefig("%s.png" % data.unwrapped_filelist[i].split('/')[-1])