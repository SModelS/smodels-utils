#!/usr/bin/env python3

import cabinetry
import copy
import json
#import subprocess

#from pyhf.contrib.utils import download

#download("https://www.hepdata.net/record/resource/1771533?view=true" ) # , "bottom-squarks")
# pyhf patchset apply SUSY-2018-04_likelihoods/Region-combined/BkgOnly.json SUSY-2018-04_likelihoods/Region-combined/patch.DS_360_200_Staus.json --name stau_360_200 --output-file atlas_susy_2018_04.json --> did not work
# jsonpatch SUSY-2018-04_likelihoods/Region-combined/BkgOnly.json SUSY-2018-04_likelihoods/Region-combined/patch.DS_360_200_Staus.json > Staus_360_200.json
# jsonpatch SUSY-2018-04_likelihoods/Region-combined/BkgOnly.json SUSY-2018-04_likelihoods/Region-combined/patch.DS_440_80_Staus.json > Staus_440_80.json


# jsonf = "bottom-squarks.json"
jsonf = "Staus_440_80.json"

# get channel names

with open ( jsonf, "rt" ) as jsonhandle:
    jsoncontent = json.load ( jsonhandle )

channels = [ x["name"] for x in jsoncontent["channels"] ]

ws = cabinetry.workspace.load( jsonf )
model, data = cabinetry.model_utils.model_and_data(ws)

fit_results = cabinetry.fit.fit(model, data)

cm = fit_results.corr_mat.tolist()

ed = model.expected_data( fit_results.bestfit )

boundaries = cabinetry.model_utils._get_channel_boundary_indices ( model )
boundaries = [0] + boundaries + [99999]
mydata = {}
for i,c in enumerate(channels):
    if "CR" in c: # control region
        continue
    print ( i, c , "boundaries", boundaries[i], boundaries[i+1] )
    mydata[c]=ed [ boundaries[i] : boundaries[i+1] ].tolist()

print ( "data", mydata )
    
"""
with open ( "cov_mat.py", "wt" ) as f:
    f.write ( "cm="+str(cm)+"\n" )
    f.close()
"""

import IPython
IPython.embed()
# print ( fit_results.corr_mat )
#print ( cm )

# import IPython
# IPython.embed()
