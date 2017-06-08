#!/usr/bin/env python

import sys,os
sys.path.insert(0,os.path.join(os.path.expanduser("~"),"smodels"))
sys.path.insert(0,os.path.join(os.path.expanduser("~"),"smodels-utils"))

from smodels.experiment.databaseObj import Database
from validation.plottingFuncs import getExclusionCurvesFor

database = Database(os.path.join(os.path.expanduser("~"),"smodels-database/"))
missingCurves = []
for expRes in database.getExpResults(datasetIDs=[None]):
    txnames = expRes.getTxNames()
    for txname in txnames:
        axes = txname.getMetaData('axes')
        if not isinstance(axes,list): axes = [axes]
        for ax in axes:
            tgraph = None
            try:
                tgraph=getExclusionCurvesFor(expRes,txname.txName,ax)
            except: pass
            if not tgraph:
                missingCurves.append({'txname' : txname.txname, 'axes' : ax,
                                       'expRes' : expRes.getValuesFor('id'),
                                       'url' :  expRes.getValuesFor('url')})

print 'Number of missing curves =',len(missingCurves)                
for miss in missingCurves:
    print miss['expRes'],miss['txname'],miss['axes']
    print miss['url'],'\n'