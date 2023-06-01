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
                indices.append(all_ana.index(ana))
        
        trimEM = np.delete(np.delete(trimEM, indices,0), indices,1)
        return trimEM


    def findBestCombination(self, expected : bool = True):
        """ the actual best combination finder """
        
        if len(self.listoftp) == 0:     #no theory prediction
            return None
            
        if len(self.listoftp) == 1:     #just 1 tp, no need for combining
            return self.listoftp
            
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
        
        if len(best_comb) == 1:     #just 1 best tp, no need for combining
            return best_comb
            
        combiner = TheoryPredictionsCombiner(best_comb)         #combine tp
        return combiner

if __name__ == "__main__":
    from smodels.experiment.databaseObj import Database
    from smodels.theory.model import Model
    from smodels.share.models.mssm import BSMList
    from smodels.share.models.SMparticles import SMList
    from smodels.tools.physicsUnits import fb, GeV
    from smodels.theory import decomposer
    
    filename = "gluino_squarks.slha"
    
    model = Model(BSMparticles = BSMList, SMparticles = SMList)
    model.updateParticles(inputFile = filename)
    toplist = decomposer.decompose(model, 0.005*fb, doCompress=True, doInvisible=True, minmassgap=5.*GeV)
    
    listOfAna = ['ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41','ATLAS-SUSY-2019-02']
    comb_dict = {"ATLAS-SUSY-2018-32":['ATLAS-SUSY-2018-41'], "ATLAS-SUSY-2018-41":['ATLAS-SUSY-2018-32', 'ATLAS-SUSY-2019-02'], "ATLAS-SUSY-2019-02":['ATLAS-SUSY-2018-41']}
    db = Database ( "official" )
    expresults = db.getExpResults(analysisIDs=listOfAna, dataTypes=['efficiencyMap','combined'])
    
    allPreds = theoryPredictionsFor(expresults, toplist, combinedResults=True)
    
    bC = BestCombinationFinder(combination_matrix = comb_dict, theoryPrediction = allPreds)
    bestThPred = bC.findBestCombination()
    
    
    if bestThPred is None : print("\n Model Point: ", filename, "  , No predictions")
    else:
        try:
            print("\n Model Point : ", filename, " best combination: ", bestThPred.describe())
        except AttributeError as e:
            print("\n Model Point: ", filename, "  , best theory prediction: ", bestThPred)
    
