# Python script which makes a mean coherence file to be plotted with GMT.

import sys
sys.path.append("/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts")
from postprocessing import *

if len(sys.argv) < 1:
    print('Usage: create_meancoherence.py directory')
    print('  You screwed up, ERROR')
    sys.exit(1)

directory = sys.argv[1]

data=read_InSAR_data(directory)
data.calc_mean_correlation(save=True,filename='mean_coherence.txt')