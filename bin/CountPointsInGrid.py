#!/usr/bin/env python3

# %% Load smodels

import sys,os
sys.path.append(os.path.expanduser('~/smodels'))
from smodels.experiment.databaseObj import Database
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns
sns.set() #Set style
sns.set_style('ticks',{'font.family':'serif', 'font.serif':'Times New Roman'})
sns.set_context('paper', font_scale=1.8)
sns.set_palette(sns.color_palette("Paired"))


# %% Load the Database of experimental results:
database = Database("official")


# %% Count number of points in each txname
nptsList = []
for exp in database.getExpResults():
    for tx in exp.getTxNames():
        nptsList.append(len(tx.txnameData.tri.points))

# %% Plot histogram
plt.hist(nptsList,bins=20)
plt.yscale('log')
plt.ylabel('Number of Maps (UL+EM)')
plt.xlabel('Number of Points in the Grid')
plt.title(f'Database version: {database.txt_meta.databaseVersion}')
plt.tight_layout()

# %% Save to file
plt.savefig('gridpointsCount.png')
#plt.show()
