import sys
sys.path.append("/Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/python_subroutines")
from postprocessing import *

if len(sys.argv) < 1:
    print('Usage: create_linear_velocity_estimate.py directory')
    print('  You screwed up, ERROR')
    sys.exit(1)


directory=sys.argv[1]

data=InSAR_data(directory)
data.read_unwrapped_interferograms()
create_linear_stack_naive(data.unwrapped_interferograms,data.deltaT,data.demrsc,save=True,filename='vel_est_naive.txt')
#data.create_linear_stack(save=True,filename='velocity_estimate.txt')

