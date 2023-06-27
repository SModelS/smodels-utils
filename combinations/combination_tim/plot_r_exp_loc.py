#!/usr/bin/env python3

import copy
import matplotlib.pyplot as plt
import numpy as np

outputFile = 'output100Comb.py'

exec(open(outputFile).read())
outputList= copy.deepcopy(outputList)

combNumberList = []
drDict = {}

for output in outputList:
    r_exp_max = 0
    combNumber = ''

    for key,value in output.items():
        if 'combo' in key:
            if value['r_exp'] > r_exp_max:
                r_exp_max = value['r_exp']
                combNumber = key

    if combNumber != 'combo0':
        print(output)
        drDict[output['slhafile']] = output[combNumber]['r_exp'] - output['combo0']['r_exp']
    combNumberList.append(combNumber)

max = max(list(drDict.values()))
file = list(drDict.keys())[list(drDict.values()).index(max)]
for output in outputList:
    if output['slhafile'] == file:
        dict = output

print(f'The highest r_exp difference is {max} for {dict}')

i=0
for combNumber in combNumberList:
    if combNumber != 'combo0':
        i+=1
print(f'The best combination is not the one with highest L_BSM^exp/L_SM^exp for {i} case over {len(combNumberList)}.')

fig = plt.figure(figsize=(8,6))
plt.ylabel(r'number of points with highest r_exp', fontsize=12)

labels, counts = np.unique(combNumberList,return_counts=True)
ticks = range(len(counts))
plt.bar(ticks,counts, align='center')
plt.xticks(ticks, labels)
plt.title('r_exp with respect to L_BSM/L_SM position')
plt.tight_layout()
plt.savefig('r_exp_loc.png', dpi=150)
