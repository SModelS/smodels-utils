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
# Define your model (list of BSM particles)
from smodels.theory.theoryPrediction import theoryPredictionsFor, TheoryPrediction

try:
    from codes.Full_SR_Ranking.pathfinder.path_finder import PathFinder
except ImportError as e:
    # FIXME in the long run the line below should disappear
    sys.path.insert(0, os.path.expanduser("~/taco_code"))
    sys.path.insert(0, os.path.expanduser("~/git/taco_code"))
    from codes.Full_SR_Ranking.pathfinder.path_finder import PathFinder

class BestCombinationFinder(object):
    def __init__(self, combination_matrix : dict,
            theoryPrediction : TheoryPrediction ):

        self.cM = combination_matrix
        #self.weight_vector = []
        #self.exclMatrix = []
        self.listoftp = theoryPrediction
        print ( "yes" )

    def createExclusivityMatrix(self) -> np.array:
        """
        create a n by n True matrix where n = number of analyses in the dict
        """

        eM = [[True for i in range(len(self.cM))] for i in range(len(self.cM))]

        listOfAna = [ana for ana in self.cM.keys()]

        for ana in self.cM.keys():
            for notcombAna in listOfAna:
                if notcombAna not in self.cM.get(ana):
                    eM[listOfAna.index(ana)][listOfAna.index(notcombAna)] = False

        return np.array(eM)

    def findBestCombination(self, expected : bool = True):
        """ the actual best combination finder """

        #comb_matrix = dictionary of allowed analyses combination
        #theoryPrediction = list of theory prediction objects for each expResult
        #print ( "no" )
        weight_vector = []
        #print ( "yes" )
        EMatrix = self.createExclusivityMatrix()
        #print ( "no" )
        for tp in self.listoftp:
            #print ( "type", type(tp) )
            if not tp:
                weight_vector.append(None)
                continue
            #get expected llhd
            for preds in tp:
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

        #Get index of analyses for which theoryPrediction is None
        indices = []
        for i in range(len(weight_vector)):
            if not weight_vector[i]:
                indices.append(i)

        #Remove analysis from exclMatrix and weight_vector for which theoryPrediction is None
        weight = np.array(weight_vector)
        weight = np.delete(weight, indices)

        EMatrix = np.delete(np.delete(EMatrix, indices,0), indices,1)

        no_tp = [self.listoftp[i] for i in indices]
        for tp in no_tp: self.listoftp.remove(tp)

        #Get the allowed list of combinations with decreasing weights
        pf = PathFinder(np.array(~EMatrix, dtype=int), weights=weight, ignore_subset=True)
        top_paths = pf.find_path(top=5)   #how many top paths?

        #return list of theory predictions for which the combination has max weight
        best_comb = [self.listoftp[i] for i in top_paths[0]['path']]

        return best_comb

if __name__ == "__main__":
    from smodels.experiment.databaseObj import Database
    db = Database ( "official" )
    print ( db )
