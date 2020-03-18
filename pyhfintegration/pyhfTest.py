#!/usr/bin/env python3
import sys
sys.path.insert(0,"/home/alguero/Work/smodels")
import json
from pyhfInterface import PyhfData
from pyhfInterface import PyhfUpperLimitComputer
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import pb, fb, GeV

# SUSY-2018-31
# jsoninputs = []
# with open("SUSY-2018-31_likelihoods/RegionA/BkgOnly.json", "r") as f:
    # jsoninputs.append(json.load(f))
# with open("SUSY-2018-31_likelihoods/RegionB/BkgOnly.json", "r") as f:
    # jsoninputs.append(json.load(f))
# with open("SUSY-2018-31_likelihoods/RegionC/BkgOnly.json", "r") as f:
    # jsoninputs.append(json.load(f))

# lumi = 139
# # Fetching the efficiencies from the database
# dir = "/home/alguero/Work/smodels-database"
# d=Database( dir, discard_zeroes = True )
# # print(d)
# results=d.getExpResults()
# x, y = (1300, 530)
# massvec = 2*[[x*GeV,y*GeV,(y - 130)*GeV]]
# effs = []
# print("Efficiencies were found for the following SRs :")
# topo = "T6bbHH"
# dsets = ["SRA_L", "SRA_M","SRA_H",
               # "SRB",
               # "SRC_22","SRC_24","SRC_26","SRC_28"
                    # ]
# for ds in dsets:
    # # print ( e.globalInfo.id )
    # for e in results:
        # eff = e.getEfficiencyFor ( topo, massvec, ds )
        # # if eff == None: continue
        # if eff != None:
            # print(ds)
            # break
    # if eff:
        # effs.append ( eff )
    # else:
        # effs.append(0)
# SUSY-2018-04
jsoninputs = []
with open("SUSY-2018-04_likelihoods/Region-combined/BkgOnly.json", "r") as f:
    jsoninputs.append(json.load(f))
# with open("SUSY-2018-04_likelihoods/Region-highMass/BkgOnly.json", "r") as f:
    # jsoninputs.append(json.load(f))
lumi = 139 # fb
# Fetching the efficiencies from the database
dir = "/home/alguero/Work/smodels-database"
d=Database( dir, discard_zeroes = True )
# print(d)
results=d.getExpResults()
massvec = 2*[[240*GeV,40*GeV]]
effs = []
print("Efficiencies were found for the following SRs :")
topo = "TStauStau"
dsets = ["SRlow" ,"SRhigh"]
for ds in dsets:
    # print ( e.globalInfo.id )
    for e in results:
        eff = e.getEfficiencyFor ( topo, massvec, ds )
        # if eff == None: continue
        if eff != None:
            print(ds)
            break
    if eff:
        effs.append ( eff )
    else:
        effs.append(0)
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