# converts complex binary SLC to binary float of absolute values.

import numpy as np
import sys 


if len(sys.argv) < 1:
    print('Usage: SLC_viewer.py filename')
    print('  You screwed up, ERROR')
    sys.exit(1)

binary_dem_filename = sys.argv[1]

A_raw = np.fromfile('%s' % binary_dem_filename, dtype='complex64', sep="")
print('Length of %s is %i' % (binary_dem_filename,len(A_raw)))

print('Maximum abs value in %s is %f' % (binary_dem_filename,np.max(np.abs(A_raw))))
print('Maximum real part in %s is %f' % (binary_dem_filename,np.max(np.real(A_raw))))
print('Maximum imaginary value in %s is %f' % (binary_dem_filename,np.max(np.imag(A_raw))))

print('Calculating absolute values')
A_abs = np.abs(A_raw)
print('Saving absolute values')
A_abs.astype('float64').tofile('%s.amplitude' % binary_dem_filename) # save as float64 format

