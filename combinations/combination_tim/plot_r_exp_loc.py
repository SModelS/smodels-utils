#!/usr/bin/env python3

import copy
import matplotlib.pyplot as plt
import numpy as np

outputFile = 'output.py'

exec(open(outputFile).read())
outputDict = copy.deepcopy(outpoutDict)

combNumberList = []

for output in outputDict:
    r_exp_max = 0
    combNumber = ''

    for key,value in ouput.items():
        if 'combo' in key:
            if value['r_exp'] > r_exp_max:
                r_exp_max = value['r_exp']
                combNumber = key

    combNumberList.append(combNumber)

fig = plt.figure(figsize=(8,6))
plt.ylabel(r'number of points with highest r_exp', fontsize=12)

labels, counts = np.unique(combNumberList,return_counts=True)
ticks = range(len(counts))
plt.bar(ticks,counts, align='center')
plt.xticks(ticks, labels)
plt.title('r_exp with respect to L_BSM/L_SM position')
plt.tight_layout()
plt.savefig('r_exp_loc.png', dpi=150)
