#!/usr/bin/env python3

""" store the theory predictions in pickle """

from smodels.theory import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.tools.physicsUnits import fb, GeV
from smodels.experiment.databaseObj import Database
from smodels.theory.model import Model
import pickle

inputFile="gluino_squarks.slha"

model = Model ( BSMList, SMList )
model.updateParticles ( inputFile=inputFile )

mingap=10*GeV
sigmacut=0.02*fb

print ( "Now decomposing" )
topos = decomposer.decompose ( model, sigmacut, minmassgap=mingap )

print ( "Decmoposed", topos )

database=Database("../../smodels-database/") 
# database=Database("../../smodels/test/database/") 
listOfExpRes = database.getExpResults()

likelihoods = []
for expRes in listOfExpRes:
    predictions = theoryPredictionsFor ( expRes, topos )
    if predictions == None:
        continue
    for prediction in predictions:
        prediction.computeStatistics()
        if prediction.likelihood != None:
            likelihoods.append ( prediction )

f=open("predictions.pcl", "wb" )
pickle.dump ( likelihoods, f )
f.close()
