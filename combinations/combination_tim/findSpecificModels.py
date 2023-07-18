#!/usr/bin/env python3

from __future__ import print_function
"""
.. module:: Example
   :synopsis: Basic main file example for using SModelS.
   This file must be run under the installation folder.
"""
""" Import basic functions (this file must be executed in the installation folder) """

import sys,os,time,glob

# smodelsPath = '/home/pascal/SModelS/smodels/'
smodelsPath = '/theo/pascal/SModelS/smodels/'
sys.path.append(smodelsPath)

# protomodelsPath = '/home/pascal/SModelS/protomodels'
protomodelsPath = '/theo/pascal/SModelS/protomodels'
sys.path.append(protomodelsPath)
from tester.combiner import Combiner

# slhaFolder = '/home/pascal/SModelS/EWinoData/filter_slha/'
slhaFolder = '/theo/pascal/filter_slha/'
outputFile = 'outputSpecificModels.py'

from smodels.tools import runtime
# Define your model (list of BSM particles)
runtime.modelFile = 'smodels.share.models.mssm'
# runtime.modelFile = 'mssmQNumbers.slha'
from smodels.decomposition import decomposer
from smodels.base.physicsUnits import fb, GeV, TeV
from smodels.theory.theoryPrediction import theoryPredictionsFor, TheoryPredictionsCombiner, TheoryPredictionList
from smodels.experiment.databaseObj import Database
from smodels.tools import coverage
from smodels.base.smodelsLogging import setLogLevel
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
from smodels.theory.model import Model
import numpy as np

setLogLevel("info")
sigmacut = 0.001*fb
mingap = 5.*GeV

def main(allPredictions):
    """
    Main program. Displays basic use case.
    """

    retListAna, retListTopo = [], []

    for theoryPrediction in allPredictions:
        if theoryPrediction.dataset.getType() not in ['efficiencyMap','combined'] :
            print(f'Wrong type for analysis {theoryPrediction.dataset.globalInfo.id}: {theoryPrediction.dataset.getType()}')
        retListAna.append(theoryPrediction.dataset.globalInfo.id)
        retListTopo += [str(txname) for txname in theoryPrediction.txnames]
        # if 'ATLAS-SUSY-2016-07' in theoryPrediction.dataset.globalInfo.id:
        #     retList.append('ATLAS-SUSY-2016-07')
        # elif 'CMS-SUS-19-006' in theoryPrediction.dataset.globalInfo.id:
        #     retList.append('CMS-SUS-19-006')
        # elif 'CMS-SUS-13-012' in theoryPrediction.dataset.globalInfo.id:
        #     retList.append('CMS-SUS-13-012')
        # elif 'CMS-PAS-SUS-16-052-agg' in theoryPrediction.dataset.globalInfo.id:
        #     retList.append('CMS-PAS-SUS-16-052')

    retListTopo = list(set(retListTopo))
    return retListAna, retListTopo


if __name__ == '__main__':
    outputDictAna, outputDictTopo = {}, {}

    # Set the path to the database
    database = Database('official')

    for i,fin in enumerate(glob.glob(slhaFolder+'*')):
        print(f'Processing {i}/18557')

        model = Model(BSMparticles=BSMList, SMparticles=SMList)
        # Path to input file (either a SLHA or LHE file)
        model.updateParticles(inputFile=fin)

        # Decompose model
        toplist = decomposer.decompose(model, sigmacut=sigmacut, doCompress=True, doInvisible=True, minmassgap=mingap)

        # Load the experimental results to be used.
        # In this case, all results are employed.
        listOfExpRes = database.getExpResults(analysisIDs='all', dataTypes=['efficiencyMap','combined'])
        allPredictions = theoryPredictionsFor(listOfExpRes, toplist, combinedResults=False)

        retListAna, retListTopo = main(allPredictions)

        for ana in retListAna:
            if ana in outputDictAna.keys():
                outputDictAna[ana].append(os.path.basename(fin))
            else:
                outputDictAna[ana] = [os.path.basename(fin)]

        for topo in retListTopo:
            if topo in outputDictTopo.keys():
                outputDictTopo[topo].append(os.path.basename(fin))
            else:
                outputDictTopo[topo] = [os.path.basename(fin)]

        with open(outputFile,'w') as fout:
            fout.write('outputDictAna = ' + str(outputDictAna) + '\noutputDictTopo = ' + str(outputDictTopo))
