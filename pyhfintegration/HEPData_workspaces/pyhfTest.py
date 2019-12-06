#!/usr/bin/env python3

import json
from pyhfInterface import PyhfData
from pyhfInterface import PyhfUpperLimitComputer

jsoninputs = []
with open("RegionA/BkgOnly.json", "r") as f:
    jsoninputs.append(json.load(f))
with open("RegionB/BkgOnly.json", "r") as f:
    jsoninputs.append(json.load(f))
with open("RegionC/BkgOnly.json", "r") as f:
    jsoninputs.append(json.load(f))

data = PyhfData([0.154, 0.628, 0.470],
                1.0,
                12.7,
                jsoninputs)
ulcomputer = PyhfUpperLimitComputer(data, 0.95)

result = ulcomputer.ulSigma()
print("mU95 = ", result)
print("sigma95 = ", result*0.0145)

