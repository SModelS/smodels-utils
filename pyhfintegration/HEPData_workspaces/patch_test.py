import json
import pyhf

efficiencies = [0.154, 0.628, 0.470]
xsection = 1.0 # pb
nsignals = [1.0, 2.0, 3.0]

pdic = [{}]
pdic[0]['op']='replace'
pdic[0]['path']="/channels/0/samples/0/data"
pdic[0]['value']=nsignals

with open('patch.bsm.json', 'w') as outputfile:
    json.dump(pdic, outputfile, indent=4)
