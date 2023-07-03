#!/usr/bin/env python3

from __future__ import print_function
"""
.. module:: Example
   :synopsis: Basic main file example for using SModelS.
   This file must be run under the installation folder.
"""
""" Import basic functions (this file must be executed in the installation folder) """

import sys,os,time,glob,copy

# smodelsPath = '/home/pascal/SModelS/smodels/'
smodelsPath = '/theo/pascal/SModelS/smodels/'
sys.path.append(smodelsPath)

# protomodelsPath = '/home/pascal/SModelS/protomodels'
protomodelsPath = '/theo/pascal/SModelS/protomodels'
sys.path.append(protomodelsPath)
from tester.combiner import Combiner

# slhaFolder = '/home/pascal/SModelS/EWinoData/filter_slha/'
slhaFolder = '/theo/pascal/filter_slha/'
outputFile = 'output100Comb_promptWidth_1e-11.py'

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

sigmacut = 0.005*fb
mingap = 5.*GeV
database = 'official'

def main(allPredictions):
    """
    Main program. Displays basic use case.
    """

    retDict={}

    combosDict = {}
    sideCombosDict = {}
    r_exp_MSA = 0.
    bestResult = None

    predictions = theoryPredictionsFor(listOfExpRes, toplist, combinedResults=True)

    for pred in predictions:
        r_exp = pred.getRValue(expected = True)
        if r_exp > r_exp_MSA:
            r_exp_MSA = r_exp
            bestResult = pred
    retDict['bestAna'] = {'name':bestResult.dataset.globalInfo.id, 'r_exp': r_exp_MSA}

    protoCombiner = Combiner()
    combinables = protoCombiner.findCombinations ( predictions, strategy='' )
    combinations = protoCombiner.sortOutSubsets ( combinables )
    for combo in combinations:
        expIDs = [tp.analysisId() for tp in combo]
        if len(expIDs) != len(set(expIDs)):
            print(f"\nDuplicated results when trying to combine analyses. Combination of {expIDs} will be skipped for file {inputFile}.")
        combostr = ''
        for c in combo:
            combostr += c.dataset.globalInfo.id + ','
        combostr = combostr[:-1]

        l0 = np.array ( [ c.likelihood(0.,expected=True, return_nll=True) for c in combo ], dtype=object )
        LH0 = np.sum ( l0[l0!=None] )
        l1 = np.array ( [ c.likelihood(1.,expected=True, return_nll=True) for c in combo ], dtype=object )
        LH1 = np.sum ( l1[l1!=None] )

        combosDict[combostr] = LH1 - LH0 # -ln(L_BSM/L_SM) -> Want to maximise that
        sideCombosDict[combostr] = {'nllr': LH1 - LH0}

        combiner = TheoryPredictionsCombiner(combo)
        sideCombosDict[combostr]['r_exp'] = combiner.getRValue(expected=True)
        sideCombosDict[combostr]['eµUL'] = combiner.getUpperLimitOnMu(expected=True)

    combosDict = dict(sorted(combosDict.items(), key = lambda x: x[1], reverse=True))
    for i,combo in enumerate(combosDict.keys()):
        retDict.update( { 'combo%s'%i: {'combo':combo, 'nllr': sideCombosDict[combo]['nllr'], 'r_exp': sideCombosDict[combo]['r_exp'], 'eµUL': sideCombosDict[combo]['eµUL']} } )

    return retDict


if __name__ == '__main__':
    outputList = []
    if os.path.exists(outputFile):
        exec(open(outputFile).read())
        outputList = copy.deepcopy(outputList)

    alreadyDone = [output['slhafile'] for output in outputList]

    # Set the path to the database
    database = Database(database)

    count = len([1 for output in outputList if 'combo1' in output.keys()])

    for i,fin in enumerate(glob.glob(slhaFolder+'*')):
        if i <= 5000:
            continue
        if count == 100:
            break
        if os.path.basename(fin) in alreadyDone:
            continue

        print(f'{count}/100')

        retDict = {'slhafile': os.path.basename(fin)}

        model = Model(BSMparticles=BSMList, SMparticles=SMList)

        model.updateParticles(inputFile=fin)

        # Decompose model
        toplist = decomposer.decompose(model, sigmacut=sigmacut, doCompress=True, doInvisible=True, minmassgap=mingap)

        # Load the experimental results to be used.
        # In this case, all results are employed.
        listOfExpRes = database.getExpResults(analysisIDs='all', dataTypes=['efficiencyMap','combined'])

        # Compute the theory predictions for each experimental result and print them:
        allPredictions = theoryPredictionsFor(listOfExpRes, toplist, combinedResults=False)
        if not allPredictions:
            continue

        # Find best combination of analyses among the available theory predictions.
        # Combination matrix is to change in getTimothee() in protomodels/tester/combinationsmatrix.py
        # and/or in protomodels/tester/analysisCombiner.py to replace getTimothee() by getMatrix().
        protoCombiner = Combiner()
        combinables = protoCombiner.findCombinations ( allPredictions, strategy='' )
        combinations = protoCombiner.sortOutSubsets ( combinables )
        if len(combinations) >= 2:
            retDict.update(main(allPredictions))
            count += 1

        outputList.append(retDict)
        with open(outputFile,'w') as fout:
            fout.write('outputList = ' + str(outputList))
