#!/usr/bin/python3

from __future__ import print_function
import sys, os, time
sys.path.insert(0,"/home/alguero/Work/smodels")
from smodels.experiment.databaseObj import Database
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.experiment.exceptions import SModelSExperimentError
from smodels.tools.smodelsLogging import setLogLevel
from smodels.tools.colors import colors
from smodels.tools.physicsUnits import pb, fb, GeV
from smodels.theory import slhaDecomposer

colors.on = True
setLogLevel ( "debug" )

# smstoplist = smstoplist = slhaDecomposer.decompose( "T6bbHH.slha" )
# print ( "smstoplist=",len(smstoplist ) )
# dir = "corrdb/"
dir = "/home/alguero/Work/smodels-database"
# dir = "database/"
d=Database( dir, discard_zeroes = True )
print(d)
results=d.getExpResults()

# print ( "is uncorrelated?" )
# print ( results[0].isUncorrelatedWith ( results[1] ) )
# sys.exit()

massvec = [[200*GeV,120*GeV], [200*GeV,120*GeV]]

effs = []
for e in results:
    # print ( e.globalInfo.id )
    dsets = [ "SRhigh", "SRlow"]
    # dsets = [ "sr0", "sr1" ]
    topo = "TStauStau"
    for ds in dsets:
        eff = e.getEfficiencyFor ( topo, massvec, ds )
        if not eff: continue
        effs.append ( eff )
        
print(effs)