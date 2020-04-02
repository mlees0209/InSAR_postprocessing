# Imports an InSAR data set, filters to only include pixels within a .kml polygon, and saves a new dataset.
#
# Usage: python filter_by_polygon infile kml_file outfile

import sys

if len(sys.argv) < 3:
    print('Usage: filter_by_polygon.py infile kml_file outfile')
    sys.exit(1)


sys.path.append('/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/')
sys.path.append('/home/mlees/Documents/InSAR_processing/postprocessing_scripts/')
from InSAR_postSBAS import *



infile = sys.argv[1]
kml_file = sys.argv[2]
outfile = sys.argv[3]


A= import_InSAR_csv(infile)

[Polylon,Polylat] = import_kml_polygon(kml_file)
B = extract_from_polygon(Polylon,Polylat,A)


B.to_csv(outfile,index=False,na_rep='NaN')
