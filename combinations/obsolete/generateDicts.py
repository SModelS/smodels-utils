#!/usr/bin/env python3

import os, subprocess
from smodels.theory import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.tools.physicsUnits import fb, GeV
from smodels.experiment.databaseObj import Database
from smodels.theory.model import Model
from smodels.theory.topology import TopologyList
from smodels.theory.theoryPrediction import TheoryPredictionList, TheoryPrediction
from smodels.experiment.databaseObj import ExpResultList
from smodels.tools.ioObjects import OutputStatus
from smodels.tools.coverage import Uncovered
from smodels.tools.printer import PyPrinter

inputFile="gluino_squarks.slha"
fout = "dict.py"

if os.path.exists ( fout ):
    subprocess.getoutput ( "cp %s old.py" % fout )

printer = PyPrinter ( output="file", filename=fout )
printer.printingOrder = [ OutputStatus,ExpResultList,TopologyList,
                          TheoryPredictionList,TheoryPrediction,Uncovered ]

model = Model ( BSMList, SMList )
model.updateParticles ( inputFile=inputFile )

mingap=10*GeV
sigmacut=0.02*fb

print ( "Now decompose" )
topos = decomposer.decompose ( model, sigmacut, minmassgap=mingap )
printer.addObj ( topos )

database=Database("../../smodels-database/")
# database=Database("./test/database/")
listOfExpRes = database.getExpResults()
r = printer.addObj ( listOfExpRes )
# print ( "adding expres", r )

allPredictions = []
for expRes in listOfExpRes:
    print ( "expRes", expRes.globalInfo.id )
    predictions = theoryPredictionsFor ( expRes, topos )
    if predictions == None:
        continue
    for p in predictions:
        p.computeStatistics()
    allPredictions += predictions._theoryPredictions
maxcond = 0.2
theoryPredictions = TheoryPredictionList(allPredictions, maxcond)
r = printer.addObj ( theoryPredictions )
# print ( "adding theory pred", predictions, r )

printer.flush()
