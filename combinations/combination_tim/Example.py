#!/usr/bin/env python3

from __future__ import print_function
"""
.. module:: Example
   :synopsis: Basic main file example for using SModelS.
   This file must be run under the installation folder.
"""
""" Import basic functions (this file must be executed in the installation folder) """

import sys,os,time

protomodelsPath = '/home/pascal/SModelS/protomodels/'
sys.path.append(protomodelsPath)
from tester.combiner import Combiner

smodelsPath = '/home/pascal/SModelS/smodels/'
sys.path.append(smodelsPath)
from smodels.tools import runtime
# Define your model (list of BSM particles)
runtime.modelFile = 'smodels.share.models.mssm'
# runtime.modelFile = 'mssmQNumbers.slha'
from smodels.decomposition import decomposer
from smodels.base.physicsUnits import fb, GeV, TeV
from smodels.matching.theoryPrediction import theoryPredictionsFor, TheoryPredictionsCombiner, TheoryPredictionList
from smodels.experiment.databaseObj import Database
from smodels.tools import coverage
from smodels.base.smodelsLogging import setLogLevel
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
from smodels.base.model import Model
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
            if theoryPrediction.dataset.getType() not in ['efficiencyMap','combined'] :
                print(f'Wrong type for analysis {theoryPrediction.dataset.globalInfo.id}: {theoryPrediction.dataset.getType()}')
            r_exp = theoryPrediction.getRValue(expected = True)
            if r_exp > r_exp_MSA:
                r_exp_MSA = r_exp
                bestResult = theoryPrediction
            allPredictions.append(theoryPrediction)

    retDict['bestAna'] = {'name':bestResult.dataset.globalInfo.id, 'r_exp': r_exp_MSA}
    # Print the most constraining experimental result
    # print("\n ",allPredictions)
    print(f"\n The most sensitive analysis is {bestResult.dataset.globalInfo.id} with an expected r-value of {r_exp_MSA:1.3E}")

    print(f"\n Theory Predictions done in {time.time() - t0:1.2f}s\n")
    t0 = time.time()

    # Find best combination of analyses among the available theory predictions.
    # Combination matrix is to change in getTimothee() in protomodels/tester/combinationsmatrix.py
    # and/or in protomodels/tester/analysisCombiner.py to replace getTimothee() by getMatrix().
    protoCombiner = Combiner()

    bestCombo,ZCombo,llhdCombo,muhatCombo = protoCombiner.findHighestSignificance(allPredictions,strategy='',expected=True)

    print(f"\n Best combination of analyses found in {time.time() - t0:1.2f}s")
    # t0 = time.time()

    # Make sure each analysis appears only once:
    expIDs = [tp.analysisId() for tp in bestCombo]
    if len(expIDs) != len(set(expIDs)):
        print(f"\nDuplicated results when trying to combine analyses. Combination will be skipped for file {inputFile}.")
    # Only compute combination if at least two results were selected
    elif len(bestCombo) > 1:
        combiner = TheoryPredictionsCombiner(bestCombo)
        print("\n Best combination of analyses:", combiner.describe())
        # combiner.computeStatistics()
        # llhd = combiner.likelihood()
        # lmax = combiner.lmax()
        # lsm = combiner.lsm()
        r_comb_obs = combiner.getRValue()
        r_comb_exp = combiner.getRValue(expected=True)
        print(f"\n Combined r value: {r_comb_obs:1.3E}\n")
        print(f"\n Combined r value (expected): {r_comb_exp:1.3E}")
        # print("Likelihoods: L, L_max, L_SM = %10.3E, %10.3E, %10.3E\n" % (llhd, lmax, lsm))

    print(f"\n Combination of analyses done in {time.time() - t0:1.2f}s")
    t0 = time.time()
    # Find out missing topologies for sqrts=13*TeV:
    uncovered = coverage.Uncovered(toplist, sqrts=13.*TeV)
    print(f"\n Coverage done in {time.time() - t0:1.2f}s")
    # First sort coverage groups by label
    groups = sorted(uncovered.groups[:], key=lambda g: g.label)
    # Print uncovered cross-sections:
    for group in groups:
        print(f"\nTotal cross-section for {group.description} (fb): {group.getTotalXSec():10.3E}\n")

    missingTopos = uncovered.getGroup('missing (prompt)')
    # Print some of the missing topologies:
    if missingTopos.generalElements:
        print('Missing topologies (up to 3):')
        for genEl in missingTopos.generalElements[:3]:
            print('Element:', genEl)
            print('\tcross-section (fb):', genEl.missingX)
    else:
        print("No missing topologies found\n")

    missingDisplaced = uncovered.getGroup('missing (displaced)')
    # Print elements with displaced decays:
    if missingDisplaced.generalElements:
        print('\nElements with displaced vertices (up to 2):')
        for genEl in missingDisplaced.generalElements[:2]:
            print('Element:', genEl)
            print('\tcross-section (fb):', genEl.missingX)
    else:
        print("\nNo displaced decays")

    return retDict, 'combo1' in retDict.keys()


if __name__ == '__main__':
    main()
