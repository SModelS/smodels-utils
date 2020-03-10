#!/usr/bin/env python3
import sys
sys.path.insert(0,"/home/alguero/Work/smodels")
import json
from pyhfInterface import PyhfData
from pyhfInterface import PyhfUpperLimitComputer
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import pb, fb, GeV

# SUSY-2018-31
jsoninputs = []
with open("SUSY-2018-31_likelihoods/RegionA/BkgOnly.json", "r") as f:
    jsoninputs.append(json.load(f))
with open("SUSY-2018-31_likelihoods/RegionB/BkgOnly.json", "r") as f:
    jsoninputs.append(json.load(f))
with open("SUSY-2018-31_likelihoods/RegionC/BkgOnly.json", "r") as f:
    jsoninputs.append(json.load(f))

lumi = 139
# Fetching the efficiencies from the database
dir = "/home/alguero/Work/smodels-database"
d=Database( dir, discard_zeroes = True )
# print(d)
results=d.getExpResults()
x, y = (1300, 530)
massvec = 2*[[x*GeV,y*GeV,(y - 130)*GeV]]
effs = []
print("Efficiencies were found for the following SRs :")
dsets = ["SRA_L", "SRA_M","SRA_H",
               "SRB",
               "SRC_22","SRC_24","SRC_26","SRC_28"
                    ]
for ds in dsets:
    # print ( e.globalInfo.id )
    topo = "T6bbHH"
    for e in results:
        eff = e.getEfficiencyFor ( topo, massvec, ds )
        # if eff == None: continue
    if eff == None:
        eff = 0
    else:
        print(ds)
    effs.append ( eff )
# SUSY-2018-04
# jsoninputs = []
# with open("SUSY-2018-04_likelihoods/Region-combined/BkgOnly.json", "r") as f:
    # jsoninputs.append(json.load(f))
# # with open("SUSY-2018-04_likelihoods/Region-highMass/BkgOnly.json", "r") as f:
    # # jsoninputs.append(json.load(f))
# lumi = 139 # fb
# # Fetching the efficiencies from the database
# dir = "/home/alguero/Work/smodels-database"
# d=Database( dir, discard_zeroes = True )
# # print(d)
# results=d.getExpResults()
# massvec = [[280*GeV,200*GeV], [280*GeV,200*GeV]]
# effs = []
# print("Efficiencies were found for the following SRs :")
# dsets = ["SRlow" ,"SRhigh"]
# for ds in dsets:
    # # print ( e.globalInfo.id )
    # topo = "TStauStau"
    # for e in results:
        # eff = e.getEfficiencyFor ( topo, massvec, ds )
        # # if eff == None: continue
        # print(ds)
    # if eff == None:
        # eff = 0
    # effs.append ( eff )
# Upper limit calculation
data = PyhfData(effs,
                            lumi,
                            jsoninputs)
ulcomputer = PyhfUpperLimitComputer(data)
result = ulcomputer.ulSigma()
print("sigma95 = ", result)
# with open("bsm.txt", "w") as out:
    # json.dump(ulcomputer.workspaces[0], out, indent=2)
with open("patch.json", "w") as p:
    json.dump(ulcomputer.patches[0], p, indent=2)