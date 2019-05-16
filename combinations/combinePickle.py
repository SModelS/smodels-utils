#!/usr/bin/env python3

""" Try out combinations from pickle file. """

from smodels.theory import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.share.models.SMparticles import SMList
from smodels.particlesLoader import BSMList
from smodels.tools.physicsUnits import fb, GeV
from smodels.experiment.databaseObj import Database
from smodels.theory.model import Model
import pickle
import IPython

f=open("predictions.pcl", "rb" )
predictions = pickle.load ( f )
f.close()

def getExperimentName ( pred ):
    """ returns name of experiment of exp result """
    if "CMS" in pred.expResult.globalInfo.id:
        return "CMS"
    if "ATLAS" in pred.expResult.globalInfo.id:
        return "ATLAS"
    return "???"

def canCombine ( predA, predB ):
    """ method that defines what we allow to combine """
    if predA.expResult.globalInfo.sqrts != predB.expResult.globalInfo.sqrts:
        return True
    if getExperimentName(predA) != getExperimentName(predB):
        return True
    return False

print ( "%d predictions" % len(predictions) )
for iA,predA in enumerate(predictions):
    for iB,predB in enumerate(predictions):
        if iA==iB:
            continue

# IPython.embed()
