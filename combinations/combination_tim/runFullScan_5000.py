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
outputFile = 'outputFullScan_5000.py'

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

    retDict = {}

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
    allPredictions = theoryPredictionsFor(listOfExpRes, toplist, combinedResults=True)

    # Find best combination of analyses among the available theory predictions.
    # Combination matrix is to change in getTimothee() in protomodels/tester/combinationsmatrix.py
    # and/or in protomodels/tester/analysisCombiner.py to replace getTimothee() by getMatrix().
    protoCombiner = Combiner()
    bestCombo,ZCombo,llhdCombo,muhatCombo = protoCombiner.findHighestSignificance(allPredictions,strategy='',expected=True)

    # Make sure each analysis appears only once:
    expIDs = [tp.analysisId() for tp in bestCombo]
    if len(expIDs) != len(set(expIDs)):
        print(f"\nDuplicated results when trying to combine analyses. Combination will be skipped for file {inputFile}.")
    # Only compute combination if at least two results were selected
    elif len(bestCombo) > 1:
        combiner = TheoryPredictionsCombiner(bestCombo)
        r_comb_obs = combiner.getRValue()
        r_comb_exp = combiner.getRValue(expected=True)

        combostr = ''
        for c in bestCombo:
            combostr += c.dataset.globalInfo.id + ','
        combostr = combostr[:-1]

        retDict['bestCombo'] = combostr
        retDict['r_obs'] = r_comb_obs
        retDict['r_exp'] = r_comb_exp

    return retDict


if __name__ == '__main__':
    comboDict = {}

    for i,fin in enumerate(glob.glob(slhaFolder+'*')):
        if 4000 <= i < 5000:
            print(f'Processing {i}/18557')

            retDict = main(inputFile=fin)
            if retDict:
                comboDict[os.path.basename(fin)] = retDict

            with open(outputFile,'w') as fout:
                fout.write('comboDict = ' + str(comboDict))
