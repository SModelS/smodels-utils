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
from smodels.experiment.databaseObj import Database

try:
    import pathfinder as pf
except ImportError as e:
    # FIXME in the long run the line below should disappear
    sys.path.insert(0, os.path.expanduser("~/PathFinder"))
    sys.path.insert(0, os.path.expanduser("~/git/PathFinder"))
    import pathfinder as pf


class BestCombinationFinder(object):

    def __init__(self, combination_matrix : dict, theoryPredictionList : list[TheoryPrediction] ):
        """
        combination_matrix = dictionary of allowed analyses combination
        theoryPrediction = list of theory prediction objects 
        """
        self.cM = combination_matrix
        self.listoftp = theoryPredictionList
        self.Ana = []                                       #Analysis in tpred List
        self.root_s = []                                    #root_s of analysis in tpred list
        
    def checkCombinable(self, a1, a2):
            
        i1 = self.Ana.index(a1)
        i2 = self.Ana.index(a2)
        expt1 = a1.split('-')[0]                                      #split at - and get 'CMS'/'ATLAS'
        expt2 = a2.split('-')[0]
        if expt1 != expt2: return True                                      #if diff expts return True
        elif str(self.root_s[i1]) != str(self.root_s[i2]) : return True     #if diff sqrts return True
        else: return False
        
        
    def setOrder(self):
        "order Analysis in EM and tpred list based on sqrt_s and analysisId"
        
        Ana_8 = []
        Ana_13 = []
        s_8 = []
        s_13 = []
        tp_list = []
        for tp in self.listoftp:
            ana = tp.dataset.globalInfo.id
            sq_s = tp.dataset.globalInfo.sqrts
            if str(sq_s).split('.')[0] == '8':
                Ana_8.append(ana)
                s_8.append('8')
                print("\n", ana)
            else:
                Ana_13.append(ana)
                s_13.append('13')
                
        Ana_8.sort()
        Ana_13.sort()
        
        
        self.Ana = Ana_8 + Ana_13
        print("\n", self.Ana)
        self.root_s = s_8 + s_13
        
        for ana in self.Ana:
            for tp in self.listoftp:
                if tp.dataset.globalInfo.id == ana:
                    tp_list.append(tp)
        
        self.listoftp =tp_list
        #print(self.listoftp, self.Ana)
        #return self
        
    def createExclusivityMatrix(self) -> np.array:
        """
        create a N by N True/False matrix where N = number of analyses in the tpred list
        """
        self.setOrder()
            
        eM = [[False for i in range(len(self.Ana))] for i in range(len(self.Ana))]  #em has dimensions of the lenght of list of theory predictions
        
        #listOfAna = [ana for ana in self.cM.keys()]   #list of Analysis in the combination dictionary
        
        for ana in self.Ana:
            for combAna in self.Ana:
                
                if not self.cM.get(ana):
                    if self.checkCombinable(combAna, ana): eM[self.Ana.index(ana)][self.Ana.index(combAna)] = True
                
                elif combAna not in self.cM.get(ana):
                    if self.checkCombinable(combAna, ana): eM[self.Ana.index(ana)][self.Ana.index(combAna)] = True
                
                else: eM[self.Ana.index(ana)][self.Ana.index(combAna)] = True
                    
                    
                    
        
        #print(np.array(eM))
        exclMatrix = np.array(eM)
        #print(exclMatrix)
        return exclMatrix
    
    """
    def trimExclusivityMatrix(self, trimEM) -> np.array:
        
        remove analysis from exclMatrix for which there is no theory prediction
        
        all_ana = [ana for ana in self.cM.keys()]
        ana_with_tp = [tp.analysisId() for tp in self.listoftp]
        
        indices = []
        for ana in all_ana:
            if ana not in ana_with_tp:
                indices.append(all_ana.index(ana))
        
        trimEM = np.delete(np.delete(trimEM, indices,0), indices,1)
        return trimEM
    """

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
    
    bC = BestCombinationFinder(combination_matrix = comb_dict, theoryPredictionList = allPreds)
    bestThPred = bC.findBestCombination()
    
    
    if bestThPred is None : print("\n Model Point: ", filename, "  , No predictions")
    else:
        try:
            print("\n Model Point : ", filename, " best combination: ", bestThPred.describe())
        except AttributeError as e:
            print("\n Model Point: ", filename, "  , best theory prediction: ", bestThPred)
    
