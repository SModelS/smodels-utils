#!/usr/bin/python

import sys,os
sys.path.insert(0,"../../../../../smodels-utils/")
sys.path.insert(0,"../../../../../smodels/")

from smodels.experiment.databaseObjects import DataBase
from validation.plotProducer import ValidationPlot, getExpIdFromPath
from smodels.tools.physicsUnits import pb

## ValidationPlot.computeWrongnessFactor = computeWrongnessFactor

txname="T2tt"
axes="2*Eq(mother,x)_Eq(lsp,y)"

filename="%s_%s.py" % ( txname, axes.replace("(","").replace(")","").replace(",","").replace("*","") )
execfile(filename)

database = DataBase("../../../../")
expRes = database.getExpResults(analysisIDs=[ getExpIdFromPath() ],datasetIDs=[None])


plot=ValidationPlot( expRes, txname, axes )
plot.data=validationData
agreement = plot.computeAgreementFactor()
print "agreement=",agreement

plot.getPlot()
plot.savePlot()

# import IPython
# IPython.embed()
