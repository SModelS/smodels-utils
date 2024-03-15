#!/usr/bin/env python3

from smodels_utils.morexsecs.refxsecComputer import RefXSecComputer
from smodels.tools.physicsUnits import fb, pb
import numpy as np
import matplotlib.pyplot as plt

xs = RefXSecComputer()
c1c1_wino  = xs.getXSecsFrom('/home/pascal/SModelS/smodels-utils/smodels_utils/morexsecs/tables/xsecC1C113.txt')
n2c1m_wino = xs.getXSecsFrom('/home/pascal/SModelS/smodels-utils/smodels_utils/morexsecs/tables/xsecN2C1m13.txt')
n2c1p_wino = xs.getXSecsFrom('/home/pascal/SModelS/smodels-utils/smodels_utils/morexsecs/tables/xsecN2C1p13.txt')

c1c1_hino  = xs.getXSecsFrom('/home/pascal/SModelS/smodels-utils/smodels_utils/morexsecs/tables/xsecC1C113hino.txt')
n2c1m_hino = xs.getXSecsFrom('/home/pascal/SModelS/smodels-utils/smodels_utils/morexsecs/tables/xsecN2C1m13hino.txt')
n2c1p_hino = xs.getXSecsFrom('/home/pascal/SModelS/smodels-utils/smodels_utils/morexsecs/tables/xsecN2C1p13hino.txt')
n2n1_hino = xs.getXSecsFrom('/home/pascal/SModelS/smodels-utils/smodels_utils/morexsecs/tables/xsecN2N1p13hino.txt')

masses = np.arange(100,1201,25)

fig,ax=plt.subplots(figsize=(8,7))

plt.yscale('log')
plt.tick_params(which="major", length=5, direction="in", bottom=True, top=True, left=True, right=True)
plt.tick_params(labelbottom=True, labelleft=True, labeltop=False, labelright=False)
plt.grid(alpha=0.6)
plt.xticks(fontsize=21)
plt.yticks(fontsize=21)

p1 = plt.plot(masses, [xs.interpolate(float(mass), c1c1_wino)/1000. for mass in masses], label = r'$\tilde\chi_1^\pm \tilde\chi_1^\mp$ (wino)',lw=2)
p2 = plt.plot(masses, [xs.interpolate(float(mass), n2c1m_wino)/1000.+xs.interpolate(float(mass), n2c1p_wino)/1000. for mass in masses], label = r'$\tilde\chi_1^\pm \tilde\chi_2^0\;\,\,\,$(wino)',lw=2)
plt.plot(1,1,color='w',alpha=0,label = ' ',)

plt.plot(masses, [xs.interpolate(float(mass), c1c1_hino)/1000. for mass in masses], color=p1[0].get_color(), ls='-.', label = r'$\tilde\chi_1^\pm \tilde\chi_1^\mp$ (higgsino)',lw=2)
plt.plot(masses, [xs.interpolate(float(mass), n2c1m_hino)/1000. + xs.interpolate(float(mass), n2c1p_hino)/1000. for mass in masses], color=p2[0].get_color(), ls='-.', label = r'$\tilde\chi_1^\pm \tilde\chi_2^0\;\;\,$(higgsino)',lw=2)
plt.plot(masses, [xs.interpolate(float(mass), n2n1_hino)/1000. for mass in masses],ls='-.', label = r'$\tilde\chi_2^0 \tilde\chi_1^0\,$   (higgsino)',lw=2)

plt.legend(fontsize=18, frameon=True, edgecolor='black', handlelength=1.3, labelspacing=0.5, ncol=2, columnspacing=0.8)
plt.xlim(100,1200)
plt.ylim(2e-5,99)

plt.ylabel('cross section [pb]', fontsize=21)
plt.xlabel('mass [GeV]', fontsize=21)
plt.title(r'pp, $\sqrt{s} = 13$ TeV, NLO+NLL', fontsize=21, loc='right')

plt.tight_layout()
plt.savefig('EWino_cross_sections.png',dpi=250,bbox_inches='tight')
plt.show()
