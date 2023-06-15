#!/usr/bin/env python3

from __future__ import print_function
"""
.. module:: Example
   :synopsis: Basic main file example for using SModelS.
   This file must be run under the installation folder.
"""
""" Import basic functions (this file must be executed in the installation folder) """

import sys,os,time,glob

protomodelsPath = '/home/pascal/SModelS/protomodels'
sys.path.append(protomodelsPath)
from tester.combiner import Combiner

slhaFolder = '/home/pascal/SModelS/EWinoData/filter_slha/'
outputFile = 'outputSpecificModels.py'

smodelsPath = '/home/pascal/SModelS/smodels/'
sys.path.append(smodelsPath)
from smodels.tools import runtime
# Define your model (list of BSM particles)
runtime.modelFile = 'smodels.share.models.mssm'
# runtime.modelFile = 'mssmQNumbers.slha'
from smodels.theory import decomposer
from smodels.tools.physicsUnits import fb, GeV, TeV
from smodels.theory.theoryPrediction import theoryPredictionsFor, TheoryPredictionsCombiner, TheoryPredictionList
from smodels.experiment.databaseObj import Database
from smodels.tools import coverage
from smodels.tools.smodelsLogging import setLogLevel
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
from smodels.theory.model import Model
import numpy as np

setLogLevel("info")

def main(inputFile='./ew_bvrs3m3v.slha', sigmacut=0.005*fb, mingap = 5.*GeV, database='official'):
    """
    Main program. Displays basic use case.
    """

    retList = []

    # Set the path to the database
    database = Database(database)

    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    # Path to input file (either a SLHA or LHE file)
    slhafile = inputFile
    model.updateParticles(inputFile=slhafile)

    # Decompose model
    toplist = decomposer.decompose(model, sigmacut, doCompress=True, doInvisible=True, minmassgap=mingap)

    # Load the experimental results to be used.
    # In this case, all results are employed.
    listOfExpRes = database.getExpResults(analysisIDs='all', dataTypes=['efficiencyMap','combined'])
    allPredictions = theoryPredictionsFor(listOfExpRes, toplist, combinedResults=False)

    for theoryPrediction in allPredictions:
        if theoryPrediction.dataset.getType() not in ['efficiencyMap','combined'] :
            print(f'Wrong type for analysis {theoryPrediction.dataset.globalInfo.id}: {theoryPrediction.dataset.getType()}')
        if 'ATLAS-SUSY-2016-07' in theoryPrediction.dataset.globalInfo.id:
            retList.append('ATLAS-SUSY-2016-07')
        elif 'CMS-SUS-19-006' in theoryPrediction.dataset.globalInfo.id:
            retList.append('CMS-SUS-19-006')
        elif 'CMS-SUS-13-012' in theoryPrediction.dataset.globalInfo.id:
            retList.append('CMS-SUS-13-012')
        elif 'CMS-PAS-SUS-19-052' in theoryPrediction.dataset.globalInfo.id:
            retList.append('CMS-PAS-SUS-16-052')

    return retList


if __name__ == '__main__':
    outputDict = {}

    for i,fin in enumerate(glob.glob(slhaFolder+'*')):
        print(f'Processing {i}/18557')

        retList = main(inputFile=fin)

        for ana in retList:
            if ana in outputDict.keys():
                outputDict[ana].append(os.path.basename(fin))
            else:
                outputDict[ana] = [os.path.basename(fin)]
        with open(outputFile,'w') as fout:
            fout.write('outputDict = ' + str(outputDict))
