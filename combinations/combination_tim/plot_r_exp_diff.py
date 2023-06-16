#!/usr/bin/env python3

import copy
import matplotlib.pyplot as plt
import numpy as np

outputFile = 'output100Comb.py'

exec(open(outputFile).read())
outputList= copy.deepcopy(outputList)

dr = []

for output in outputList:
    r_exp_max = 0
    combNumber = ''

    for key,value in output.items():
        if 'combo' in key:
            if value['r_exp'] > r_exp_max: # r_exp_max is the max r_exp among all the analysis combination results
                r_exp_max = value['r_exp']

    dr.append(r_exp_max - output['bestAna']['r_exp'])

fig = plt.figure(figsize=(8,6))
plt.ylabel(r'number of points', fontsize=12)
plt.xlabel(r'$r_{comb}^{exp} - r_{best}^{exp}$')
plt.title('Sensitivity gained through analyses combination')
plt.hist(dr)
plt.tight_layout()
plt.savefig('r_exp_diff.png', dpi=150)
