#!/usr/bin/env python3

import glob, copy, matplotlib
import matplotlib.pyplot as plt

outputFile = 'outputSpecificModels.py'
slhaFolder = '/home/pascal/SModelS/EWinoData/filter_slha/'

exec(open(outputFile).read())
outputDict= copy.deepcopy(outputDict)

for ana in outputDict:
    # M1 = []
    # M2 = []
    # mu = []
    M2mu = []
    M2M1 = []
    ctC1 = []
    diff = []
    for basename in outputDict[ana]:
        file = slhaFolder + basename

        with open(file) as f:
            lines = f.readlines()

        for line in lines:
            if 'M_1(MX)' in line.split():
                M1_float = float(line.split()[1])
                # M1.append(M1_float)
            elif 'M_2(MX)' in line.split():
                M2_float = float(line.split()[1])
                # M2.append(M2_float)
            elif 'mu(MX)' in line.split():
                mu_float = float(line.split()[1])
                # mu.append(mu_float)
            elif 'DECAY' in line.split() and '1000024' in line.split():
                wC1_float = float(line.split()[2])
                ctC1.append(299792458*6.582e-25/wC1_float)

        M2mu.append(M2_float/mu_float)
        M2M1.append(M2_float/M1_float)

        scaleList=[abs(M1_float),abs(M2_float),abs(mu_float)]
        maxScale=max(scaleList)
        scaleList.remove(maxScale)
        midScale=max(scaleList)
        diff.append(maxScale-midScale)

    scatter = plt.scatter(M2mu,M2M1,s=1.,c=diff,cmap='RdYlBu_r')
    plt.xlabel(r'$M_2 / \mu$')
    plt.ylabel(r'$M_2 / M_1$')
    plt.yscale('log')
    plt.xscale('log')
    cbar=plt.colorbar(scatter)
    cbar.set_label(r'$\Delta$ heaviest scale - second-to-heaviest scale',rotation=90)
    # cbar.set_label(r'$c \tau_{\tilde \chi^\pm_1}$ [m]',rotation=90)
    plt.legend()
    plt.savefig(f'scaleRatios_{ana}.png')
    plt.close()
