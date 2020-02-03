#!/usr/bin/env python3

import json
from pyhfInterface import PyhfData
from pyhfInterface import PyhfUpperLimitComputer

# Fetching the json inputs
jsoninputs = []
with open("sbottom_workspaces/RegionA/BkgOnly.json", "r") as f:
    jsoninputs.append(json.load(f))
with open("sbottom_workspaces/RegionB/BkgOnly.json", "r") as f:
    jsoninputs.append(json.load(f))
with open("sbottom_workspaces/RegionC/BkgOnly.json", "r") as f:
    jsoninputs.append(json.load(f))

efficiencies = [0.15404183, 0.6278016 , 0.46972812, 0.0057462 , 0.02926009, 0.01845257, 0.00412215, 0. ]
xsec = 12.9E-03
lumi = 139

data = PyhfData(efficiencies,
                            xsec,
                            lumi,
                            jsoninputs)
ulcomputer = PyhfUpperLimitComputer(data, 0.95)
print(json.dumps(ulcomputer.patches[2], indent=2))
result = ulcomputer.ulSigma(ulcomputer.workspaces[2], expected=True)
print("mU95 = ", result)
print("sigma95 = ", result*xsec)
