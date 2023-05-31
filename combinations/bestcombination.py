#!/usr/bin/env python3

"""
.. module:: bestcombination
   :synposis: wraps Jamie Yellen's pathfinder for SModelS

.. moduleauthor: Sahana Narasimha <sahana.narasimha@oeaw.ac.at>

"""

__all__ = [ "BestCombinationFinder" ]

import numpy as np
import sys, os
from smodels.tools import runtime
from smodels.theory.theoryPrediction import theoryPredictionsFor, TheoryPrediction, TheoryPredictionsCombiner

'''
try:
    from codes.Full_SR_Ranking.pathfinder.path_finder import PathFinder
except ImportError as e:
    # FIXME in the long run the line below should disappear
    sys.path.insert(0, os.path.expanduser("~/taco_code"))
    sys.path.insert(0, os.path.expanduser("~/git/taco_code"))
    from codes.Full_SR_Ranking.pathfinder.path_finder import PathFinder
'''
try:
    import pathfinder as pf
except ImportError as e:
    # FIXME in the long run the line below should disappear
    sys.path.insert(0, os.path.expanduser("~/PathFinder"))
    sys.path.insert(0, os.path.expanduser("~/git/PathFinder"))
    import pathfinder as pf


class BestCombinationFinder(object):

    def __init__(self, combination_matrix : dict, theoryPrediction : TheoryPrediction ):
        """
        combination_matrix = dictionary of allowed analyses combination
        theoryPrediction = list of theory prediction objects for each expResult
        """
        self.cM = combination_matrix
        self.listoftp = theoryPrediction

    def createExclusivityMatrix(self) -> np.array:
        """
        create a N by N True/False matrix where N = number of analyses in the dict
        """
        eM = [[True for i in range(len(self.cM))] for i in range(len(self.cM))]

        listOfAna = [ana for ana in self.cM.keys()]

        for ana in self.cM.keys():
            for notcombAna in listOfAna:
                if notcombAna not in self.cM.get(ana):
                    eM[listOfAna.index(ana)][listOfAna.index(notcombAna)] = False
        
        exclMatrix = self.trimExclusivityMatrix(np.array(eM))
        return exclMatrix
        
    def trimExclusivityMatrix(self, trimEM) -> np.array:
        """
        remove analysis from exclMatrix for which there is no theory prediction
        """
        all_ana = [ana for ana in self.cM.keys()]
        ana_with_tp = [tp.analysisId() for tp in self.listoftp]
        
        indices = []
        for ana in all_ana:
            if ana not in ana_with_tp:
                print("\n Indices = ", all_ana.index(ana))
                indices.append(all_ana.index(ana))
        
        trimEM = np.delete(np.delete(trimEM, indices,0), indices,1)
        return trimEM


    def findBestCombination(self, expected : bool = True):
        """ the actual best combination finder """

        weight_vector = []
        EMatrix = self.createExclusivityMatrix()
        
        for preds in self.listoftp:
            if expected:   #get expected llhd
                lbsm = preds.likelihood(expected=True)
                lsm = preds.lsm(expected=True)
                weight = -np.log(lbsm/lsm)  #returning nll ratio
                weight_vector.append(weight)
            else:          #get observed llhd
                lbsm = preds.likelihood()
                lsm = preds.lsm()
                weight = -np.log(lbsm/lsm)  #returning nll ratio
                weight_vector.append(weight)
        
        #Create Binary Acceptance Matrix
        bam = pf.BinaryAcceptance(EMatrix, weights=np.array(weight_vector))
        
        #Get the allowed list of combinations with decreasing weights
        whdfs = pf.WHDFS(bam, top=5)
        whdfs.find_paths()
        
        top_path = whdfs.get_paths[0]  #how many top paths?

        #return list of theory predictions for which the combination has max weight
        best_comb = [self.listoftp[i] for i in top_path]
        
        combiner = TheoryPredictionsCombiner(best_comb)
        return combiner

if __name__ == "__main__":
    from smodels.experiment.databaseObj import Database
    db = Database ( "official" )
    print ( db )
