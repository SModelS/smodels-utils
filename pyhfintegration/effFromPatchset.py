#!/usr/bin/env python3

""" some code snippet to extract efficiency maps from patchsets.
needs to be adapted to new situations.
"""

import json
import sys
import os
codedir = f"{os.environ['HOME']}/git/"
sys.path.append(f'{codedir}/smodels-utils')
sys.path.append(f'{codedir}/smodels')
from smodels_utils.morexsecs.refxsecComputer import RefXSecComputer
from smodels.base.physicsUnits import fb, pb

with open('EWKinos_bkgonly.json', 'r') as f:
    bkg = json.load(f)

# Getting the paths of each SR from the background JSON
chPath = {}
iCh = 0
for ch in bkg['channels']:
    srName = ch['name']
    # if srName[:2] == 'SR':
    chPath[srName] = '/channels/%d/samples/' % iCh
    iCh += 1

# Preparing the cross sections
lumi = 139/fb
xs = RefXSecComputer()
n2c1m = xs.getXSecsFrom(f'{codedir}/smodels-utils/smodels_utils/morexsecs/tables/xsecN2C1m13.txt')
n2c1p = xs.getXSecsFrom(f'{codedir}/smodels-utils/smodels_utils/morexsecs/tables/xsecN2C1p13.txt')
# Extracting the signals from the patchset and writing the exlusive eff. files

# selectSR = 'high_0J'
# selectMass = [150., 60.]
# selectEff = 0

with open('EWKinos_patchset.json', 'r') as f:
    patchset = json.load(f)

for i,sr in enumerate(chPath):
    name = f"{sr}_winobino(+)_efficiency.csv"
    goodpath = chPath[sr]
    if i <= 5: # CRs
        BR =  0.6741*(0.03363+0.03366)
    elif i <= 11: # 1l1T SRs
        BR =  0.6741*(0.03363+0.03366) # C1 -> W* (-> qq) + N1 = 0.6741, and N2 -> ee + N1 = 0.03363 and N2 -> mumu + N1 = 0.03366
    elif i <= 27:
        BR =  0.6741*0.03363 # C1 -> qq + N1 = 0.6741 and N2 -> ee + N1 = 0.03363
    else:
        BR =  0.6741*0.03366 # C1 -> qq + N1 = 0.6741 and N2 -> mumu + N1 = 0.03366
    with open(name, 'w') as out:
        out.write('M(c1,n2),M(c1,n2)-M(n1),Efficiency\n')
        for pa in patchset['patches']:
            massvector = pa['metadata']['values']
            if massvector[0] != "WinoBino_noWeight":
                continue
            scale_factor = 1.
            if massvector[1]-massvector[2] < 10: # If mN2-mN1 < 10 GeV, Z -> bb is not accessible anymore, thus need to rescale Z -> ll
                scale_factor = 1./(1-0.156) # BR_i,rescaled = BR_i/(1-BR_bb), with BR_bb = 0.156
            xsec = None
            plus = xs.interpolate(massvector[1], n2c1p)
            minus = xs.interpolate(massvector[1], n2c1m)
            if plus and minus: # could be None if we are out of the interpolation hull
                xsec = plus + minus
            signal = None
            for op in pa['patch']:
                if goodpath in op['path']:
                    signal = op['value']['data'][0]
            if signal != None and xsec != None:
                xsec *= fb
                eff = signal/xsec/lumi/(BR*scale_factor)
                if eff > 1. :
                    print("ERROR. sr : ", sr," | signal : ", signal, " | xs : ", xsec, " | massv : ", massvector)
                    continue
                # if selectSR in sr and selectMass == massvector:
                #     print(sr)
                #     selectEff += eff
                # print("{},{},{}".format(massvector[0], massvector[1], eff))
                out.write(f"{massvector[1]},{massvector[1] - massvector[2]},{eff}\n")
# print('"""%s"""' % selectSR)
# print("{},{},{}".format(selectMass[0], selectMass[0]-selectMass[1], selectEff))
