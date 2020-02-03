import json
import pyhf

lumi = 12.7 # fb
efficiencies = [0.154, 0.628, 0.470]
xsection = 0.2 # pb
nsignals = [eff*xsection*lumi for eff in efficiencies]

pdic = [{}]
pdic[0]['op']='replace'
pdic[0]['path']="/channels/0/samples/0/data"
pdic[0]['value']=nsignals

with open('patch.bsm.json', 'w') as outputfile:
    json.dump(pdic, outputfile, indent=4)
