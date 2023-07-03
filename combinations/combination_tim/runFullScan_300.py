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
outputFile = 'outputFullScan_300.py'


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
from smodels.theory.exceptions import SModelSTheoryError as SModelSError
import numpy as np

setLogLevel("info")

sigmacut = 0.001*fb
mingap = 5.*GeV
database = 'official'

def main(allPredictions):
    """
    Main program. Displays basic use case.
    """

    retDict = {}

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
        combostr = ''
        for c in bestCombo:
            combostr += c.dataset.globalInfo.id + ','
        combostr = combostr[:-1]
        retDict['bestCombo'] = combostr

        try:
            r_comb_obs = combiner.getRValue()
            retDict['r_obs'] = r_comb_obs
        except:
            print(f'r_comb_obs failed for combination of {combostr}')
            retDict['r_obs'] = None

        try:
            r_comb_exp = combiner.getRValue(expected=True)
            retDict['r_exp'] = r_comb_exp
        except:
            print(f'r_comb_exp failed for combination of {combostr}')
            retDict['r_exp'] = None


    return retDict


if __name__ == '__main__':
    comboDict = {}
    try:
        exec(open(outputFile).read())
        comboDict = comboDict
    except:
        pass
    alreadyDone = [filename for filename in comboDict.keys()]

    # Set the path to the database
    database = Database(database)


    for i,fin in enumerate(glob.glob(slhaFolder+'*')):
        if 200 <= i < 300:
	        filename = os.path.basename(fin)
	        print(f'Processing {i}/9881: {filename}')
	        if filename in alreadyDone:
	            continue
	
	        # print('check if 16-039 and 16-048 are taken into account for -ma5 or -agg, in listOfExpRes and in bestCombo')
	        retDict = {}
	
	        model = Model(BSMparticles=BSMList, SMparticles=SMList)
	        model.updateParticles(inputFile=fin)
	
	        toplist = decomposer.decompose(model, sigmacut=sigmacut, doCompress=True, doInvisible=True, minmassgap=mingap)
	
	        listOfExpRes = database.getExpResults(analysisIDs=['all'], txnames=['TChi*'], dataTypes=['efficiencyMap','combined'])
	        allPredictions = theoryPredictionsFor(listOfExpRes, toplist, combinedResults=False)
	
	        protoCombiner = Combiner()
	        bestCombo,ZCombo,llhdCombo,muhatCombo = protoCombiner.findHighestSignificance(allPredictions,strategy='',expected=True)
	        if len(bestCombo) > 1:
	            allPredictions = theoryPredictionsFor(listOfExpRes, toplist, combinedResults=True)
	            retDict = main(allPredictions=allPredictions)
	
	        comboDict[filename] = retDict
	
	        with open(outputFile,'w') as fout:
	            fout.write('comboDict = ' + str(comboDict))
