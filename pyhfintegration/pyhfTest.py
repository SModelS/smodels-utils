#!/usr/bin/env python3

import sys
sys.path.insert(0,"../../smodels")
import json
from pyhfInterface import PyhfData
from pyhfInterface import PyhfUpperLimitComputer
from smodels.experiment.databaseObj import Database
import smodels.experiment.txnameObj
smodels.experiment.txnameObj.TxNameData._keep_values = True
from smodels.tools.physicsUnits import pb, fb, GeV
from smodels.tools.smodelsLogging import logger
logger.setLevel('DEBUG')

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
cbJson = []
with open("SUSY-2018-04_likelihoods/SRcombined-aux.json", "r") as f:
    cbJson.append(json.load(f))
bestJsons = []
with open("SUSY-2018-04_likelihoods/Region-lowMass/BkgOnly.json", "r") as f:
    bestJsons.append(json.load(f))
with open("SUSY-2018-04_likelihoods/Region-highMass/BkgOnly.json", "r") as f:
    bestJsons.append(json.load(f))
# Fetching the efficiencies from the database
dir = "../../smodels-database"
d=Database( dir, discard_zeroes = True)
# print(d)
results=d.getExpResults()
massvec = 2*[[240*GeV,40*GeV]]
print("Efficiencies were found for the following SRs :")
topo = "TStauStau"
dsets = ["SRlow" ,"SRhigh"]
# for e in results:
#     txnames = e.getTxNames()
#     for tx in txnames:
#         if str(tx) == topo and tx.txnameData.dataType == "upperLimit":
#             data = eval(tx.txnameData.origdata)
# outputDataDict = []
# for d in data:
#     massvec = d[0]
#     print("Evalutating mass point %s" % massvec)
#     ul = d[1]
effs = []
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
lumi = 139/fb
nsig = [(lumi*eff).asNumber(1/pb) for eff in effs]
cbSig = [nsig]
bestSig = [[s] for s in nsig]
# Upper limit calculation for combined
data = PyhfData(cbSig, cbJson)
ulcomputer = PyhfUpperLimitComputer(data)
result = ulcomputer.ulSigma()*pb
lh = ulcomputer.likelihood()
# Upper limit calculation for best expected
# data = PyhfData(bestSig, bestJsons)
# ulcomputer = PyhfUpperLimitComputer(data)
# best = ulcomputer.bestUL()*pb
# i_best = ulcomputer.i_best
print("pyhf = %s, official = %s, discrepancy = %s, lh = %s" % (str(result),
                                                      str(ul),
                                                      str((result-ul)/ul),
                                                          str(lh)))
#     outputEntry = {}
#     outputEntry["m(stau)"] = massvec[0][0].asNumber()
#     outputEntry["m(chi1)"] = massvec[0][1].asNumber()
#     outputEntry["pyhfUL"] = result.asNumber()
#     outputEntry["officialUL"] = ul.asNumber()
#     outputEntry["discrepancy"] = ((result - ul)/ul).asNumber()
#     # outputEntry["bestExpUL"] = best.asNumber()
#     # outputEntry["bestSR"] = "SRlow" if i_best == 0 else "SRhigh"
#     outputDataDict.append(outputEntry)
#
# outputFile = open("output.py", "w")
# outputFile.write("outputDataDict="+str(outputDataDict)+"\n")
# outputFile.close()
