#!/usr/bin/env python3

import sys
sys.path.insert(0,"../../smodels")
import json
from smodels.experiment.databaseObj import Database
import smodels.experiment.txnameObj
smodels.experiment.txnameObj.TxNameData._keep_values = True
from smodels.base.physicsUnits import pb, fb, GeV
from smodels.base.smodelsLogging import logger
logger.setLevel('INFO')
from smodels_utils.helper.memory_footprint import sizeof

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
db=Database( dir )
results=db.getExpResults()
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

ul = 3.*fb
import pyhfInterface
from pympler import muppy, summary
import inspect
import gc
import importlib

def retrieve_name(var, skip_names=[]):
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var if var_name not in skip_names ]

def objects_by_id(id_):
    for obj in gc.get_objects():
        if id(obj) == id_:
            return obj
    return None

# ba=[5,7,9]
# print ( "name", retrieve_name ( ba ) )
# sys.exit()
    

for _ in range(10):
    data = pyhfInterface.PyhfData(cbSig, cbJson)
    ulcomputer = pyhfInterface.PyhfUpperLimitComputer(data)
    print ( _ ) # , gc.get_count() )
    result = ulcomputer.ulSigma()*pb
    lh = ulcomputer.likelihood()

    #all_objects = muppy.get_objects()
    #sum1 = summary.summarize(all_objects)
    #summary.print_(sum1)

    #del all_objects, sum1

    #print ( "whats not in gc?" )
    # Get references to certain types of objects such as dataframe
    #lists = [ao for ao in all_objects if isinstance(ao, list)]
    #for i,address in enumerate(muppy.filter(all_objects, Type=list)):
    #      in_gc = objects_by_id(address)
    #      names = retrieve_name(address, skip_names = [ "address" ] )
    #      if in_gc: continue
    #      print("not in gc",i, names)
    #for l in lists:
    #    if len(l)>100000:
    #        print ( "list of size %d, name=``%s''" % ( len(l), retrieve_name(l) ) )
    #        print ( " `- ", l )
            #for i in range(len(l)):
            #    print ( "  `- nr=", i )
            #    print ( "  `- type=", type(l[i]) ) ## str(l).encode("utf-8")[:30] )
            #    if type(l[i])==dict:
            #        continue
            #    print ( "  `- content", l[i] )
            #    print ( "  `-  size=", sizeof(l[i]) )
