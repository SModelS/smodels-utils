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
outputFile = 'outputtest.py'

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

    print(f'Processing file {inputFile}')

    retDict = {'slhafile': os.path.basename(inputFile)}

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

    t0 = time.time()

    # Compute the theory predictions for each experimental result and print them:
    r_exp_MSA = 0.
    bestResult = None
    allPredictions = TheoryPredictionList()
    for expResult in listOfExpRes:
        predictions = theoryPredictionsFor(expResult, toplist, combinedResults=True)
        if not predictions:
            continue  # Skip if there are no constraints from this result
        for theoryPrediction in predictions:
            if theoryPrediction is None:
                print(f'theoryPrediction is None for {inputFile}')
                return {}, False
            if theoryPrediction.dataset.getType() not in ['efficiencyMap','combined'] :
                print(f'Wrong type for analysis {theoryPrediction.dataset.globalInfo.id}: {theoryPrediction.dataset.getType()}')
            r_exp = theoryPrediction.getRValue(expected = True)
            if r_exp > r_exp_MSA:
                r_exp_MSA = r_exp
                bestResult = theoryPrediction
            allPredictions.append(theoryPrediction)

    if not allPredictions:
        return {}, False
    retDict['bestAna'] = {'name':bestResult.dataset.globalInfo.id, 'r_exp': r_exp_MSA}

    # Find best combination of analyses among the available theory predictions.
    # Combination matrix is to change in getTimothee() in protomodels/tester/combinationsmatrix.py
    # and/or in protomodels/tester/analysisCombiner.py to replace getTimothee() by getMatrix().
    protoCombiner = Combiner()
    combinables = protoCombiner.findCombinations ( allPredictions, strategy='' )
    combinations = protoCombiner.sortOutSubsets ( combinables )
    combosDict = {}
    sideCombosDict = {}
    if len(combinations) >= 2:
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

    return retDict, 'combo1' in retDict.keys()


if __name__ == '__main__':
    outputList = []
    exec(open(outputFile).read())
    outputList = copy.deepcopy(outputList)
    alreadyDone = [output['slhafile'] for output in outputList]
    for fin in glob.glob(slhaFolder+'*'):
        if os.path.basename(fin) in alreadyDone:
            continue
        print(f'{len(outputList)}/100')
        if len(outputList) == 100:
            break
        retDict,add = main(inputFile=fin)
        if add:
            outputList.append(retDict)
            with open(outputFile,'w') as fout:
                fout.write('outputList = ' + str(outputList))
