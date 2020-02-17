# Imports an InSAR data set, masks pixels by a minimum mean correlation value, and saves a new dataset.

import sys

if len(sys.argv) < 3:
    print('Usage: filter_by_correlation.py infile min_corr_threshold outfile')
    sys.exit(1)

sys.path.append('/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts')
from InSAR_postSBASprocessing import *

infile = sys.argv[1]
corr_threshold = float(sys.argv[2])
outfile = sys.argv[3]


A= import_InSAR_csv(infile,sep=' ')

B = filter_mean_correlation(A,corr_threshold)

print('Saving new file as %s' % outfile)
B.to_csv(outfile,sep=' ',index=False)