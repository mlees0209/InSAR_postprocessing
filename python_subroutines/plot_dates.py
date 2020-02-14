# -*- coding: utf-8 -*-
"""
Spyder Editor

CALLED BY THE CHECK_L0_DATES script in the above directory; don't delete this no matter how tempting!!
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
from matplotlib.dates import  DateFormatter
import sys
import re

title=sys.argv[1] # actually not used anymore

currentdir=sys.argv[2]

dates = np.genfromtxt('%s/dates.tmp' % currentdir,dtype='str')

dates = [mdates.date2num(datetime.strptime(date,'%Y%m%d')) for date in dates]

#xticks = np.arange(np.min(dates),np.max(dates),14)

y = np.ones_like(dates)

plt.figure(figsize=(28,3))
plt.plot_date(dates,y,'g^')
plt.xticks(dates,rotation=90)
plt.gca().yaxis.set_visible(False)
plt.gca().xaxis.set_major_formatter( DateFormatter('%Y-%m-%d') )
plt.tight_layout()

plt.savefig('%s/L0_timeseries.png' % currentdir,bbox='tight')
print('\t Figure saved as %s/L0_timeseries.png.' % currentdir)