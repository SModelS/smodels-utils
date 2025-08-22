#!/usr/bin/env python3

"""
.. module:: bestcombination
   :synposis: wraps Jamie Yellen's pathfinder for SModelS

.. moduleauthor: Sahana Narasimha <sahana.narasimha@oeaw.ac.at>

"""

#write check for most sensitive analysis
__all__ = [ "BestCombinationFinder" ]

import numpy as np
import sys, os
import logging
logger = logging.getLogger(__name__)

from smodels.tools import runtime
from smodels.matching.theoryPrediction import theoryPredictionsFor, TheoryPrediction, TheoryPredictionsCombiner
from smodels.experiment.databaseObj import Database

#try:
#    import pathfinder as pf
#except ImportError as e:
    # FIXME in the long run the line below should disappear
  #  sys.path.insert(0, os.path.expanduser("~/PathFinder"))
sys.path.insert(0, os.path.expanduser("~/git/PathFinder"))
import pathfinder as pf


class BestCombinationFinder(object):

    def __init__(self, combination_matrix : dict, theoryPredictionList : list[TheoryPrediction], useAnalysisFromDict = True, n_top = 1):
        """
        combination_matrix = dictionary of allowed analyses combination
        theoryPredictionList = list of theory prediction objects
        useAnalysisFromDict = True : If False, allow tp for analyses which is not specified in the combination matrix dictionary
        """
        self.cM = combination_matrix
        self.listoftp = theoryPredictionList
        
        self.use_dict = True
        if not useAnalysisFromDict: self.use_dict = False
        
        self.ntop = n_top
        self.Ana = []                                       #Analysis in tpred List
        self.root_s = []                                    #root_s of analysis in tpred list
        
        self.combiner_list=[]
    
    def checkCombinable(self, a1, a2):
        "Check if two analyses are combinable if not specified in combination dictionary"
        
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
        notp_list = []
        #split tp into 2 lists - 8 and 13 TeV
        for tp in self.listoftp:
            if not tp: continue                             #if tp = None
            ana = tp.dataset.globalInfo.id
            if ana not in self.cM.keys():
                if self.use_dict:
                    notp_list.append(tp)
                    #self.listoftp.pop(self.listoftp.index(tp))
                    continue
                else: logger.error(' There is a theory prediction for an analysis not mentioned in combination matrix. Will proceed for now.')
            sq_s = tp.dataset.globalInfo.sqrts
            if str(sq_s).split('.')[0] == '8':
                Ana_8.append(ana)
                s_8.append('8')
            else:
                Ana_13.append(ana)
                s_13.append('13')
                
        Ana_8.sort()
        Ana_13.sort()
        
        self.Ana = Ana_8 + Ana_13
        self.root_s = s_8 + s_13
        
        tp_list = []
        for ana in self.Ana:
            for tp in self.listoftp:
                if tp.dataset.globalInfo.id == ana and tp not in notp_list:
                    tp_list.append(tp)
        
        self.listoftp = tp_list
        
        
    def createExclusivityMatrix(self) -> np.array:
        """
        create a N by N True/False matrix where N = number of analyses in the tpred list
        """
        self.setOrder()
        
        eM = [[False for i in range(len(self.Ana))] for i in range(len(self.Ana))]  #em has dimensions of the length of list of analysis in comb_matrix (list of tp) for True(False)
        
        for ana in self.Ana:
            for combAna in self.Ana:
                if not self.use_dict and ana not in self.cM.keys():
                    if self.checkCombinable(combAna, ana): eM[self.Ana.index(ana)][self.Ana.index(combAna)] = True
                elif not self.cM.get(ana):
                    if self.checkCombinable(combAna, ana): eM[self.Ana.index(ana)][self.Ana.index(combAna)] = True
                elif combAna not in self.cM.get(ana):
                    if self.checkCombinable(combAna, ana): eM[self.Ana.index(ana)][self.Ana.index(combAna)] = True
                else: eM[self.Ana.index(ana)][self.Ana.index(combAna)] = True

        exclMatrix = np.array(eM)
        #print(exclMatrix)
        #print(self.Ana)
        return exclMatrix
    

    def findBestCombination(self, expected : bool = True):
        """ the actual best combination finder """
        
        if len(self.listoftp) == 0:     #no theory prediction
            print("No theory Prediction")
            return []
            
        if len(self.listoftp) == 1:
            if self.listoftp[0].analysisId() in self.cM.keys():     #just 1 tp, no need for combining
                print("1 theory Prediction ", self.listoftp[0].analysisId())
                return self.listoftp
            else:
                print("1 theory Prediction but not present in combination dictionary: ", self.listoftp[0].analysisId())
                return []
            
        weight_vector = []
        EMatrix = self.createExclusivityMatrix()
        
        if not EMatrix.size:              #EMatrix is empty
            print("Theory Prediction available but none are present in combination dictionary.")
            return []
        
        if len(self.listoftp) == 1:     #just 1 tp, no need for combining
            print(">1 theory Prediction but only 1 present in the combination dictionary ", self.listoftp[0].analysisId())
            return self.listoftp
        
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
        whdfs = pf.WHDFS(bam, top=self.ntop)
        whdfs.find_paths()
        
        if self.ntop > 1:
            top_path = [path for path in whdfs.get_paths]
            listofbestcomb = [[self.listoftp[i] for i in path] for path in top_path]
            #print("\n List of best combinations = ", listofbestcomb)
            self.combiner_list = []
            for best_comb in listofbestcomb:
                if best_comb == []: self.combiner_list.append(None)
                else: self.combiner_list.append(TheoryPredictionsCombiner(best_comb))
            for comb in self.combiner_list:
                if comb: print(f"\n {int(self.combiner_list.index(comb) + 1)} : ", comb.analysisId())
                else: print(f"\n {int(self.combiner_list.index(comb) + 1)} : ", comb)
            return self.combiner_list
        
        #return list of theory predictions for which the combination has max weight
        top_path = whdfs.get_paths[0]  # gets indices of analyses which are best combinable
        best_comb = [self.listoftp[i] for i in top_path]
        
        if len(best_comb) == 1:     #just 1 best tp, no need for combining
            #print("\n Best Combination ", best_comb[0].analysisId())
            return best_comb
            
        self.combiner_list = [TheoryPredictionsCombiner(best_comb)]                     #combine tp
        #print("\n Best Combination ", self.combiner_list[0].analysisId())
        return self.combiner_list
        
        
    def checkSensitive(self):
        
        if self.combiner_list == []:
            if len(self.listoftp) == 1 and self.listoftp[0].analysisId() in self.cM.keys():
                r = self.listoftp[0].getRValue(expected = True)
                print(f"\n R-value of analysis {self.listoftp[0].analysisId()} is ", r )
                return r
            else: return 0
            
        tp_rvalues = [tp.getRValue(expected=True) for tp in self.listoftp]
        rmax = max(tp_rvalues)
        bestResult = self.listoftp[tp_rvalues.index(rmax)].analysisId()
        '''
        for tp in self.listoftp:
            if not tp: continue
            r = tp.getRValue(expected = True)
            if r>rmax:
                rmax = r
                bestResult = tp.analysisId()
        '''
        self.ntop = 3
        #comb = self.findBestCombination()
        comb_rvalues = []
        for c in self.combiner_list:
            if c: comb_rvalues.append(c.getRValue(expected = True))
        print("\n R-Values of top combinations ", comb_rvalues, f" and R-value of most sensitive analysis {bestResult} is ", rmax)
        if comb_rvalues[0] >= rmax:
            if comb_rvalues[0] == max(comb_rvalues):
                if bestResult in self.combiner_list[0].analysisId(): return comb_rvalues[0]
                else:
                    logger.error("most sensitive analysis is not included in the best combination")
                    return 0
                    
            else:
                logger.error(f"sensitivity of best combination is lower than that of the combination ranked {int(comb_rvalues.index(max(comb_rvalues)) + 1)} ")
                return 0
        else:
            logger.error(f"sensitivity of best combination is lower than that of the most sensitive analysis: {bestResult}")
            return 0
            
        


if __name__ == "__main__":
    from smodels.experiment.databaseObj import Database
    from smodels.theory.model import Model
    from smodels.share.models.mssm import BSMList
    from smodels.share.models.SMparticles import SMList
    from smodels.base.physicsUnits import fb, GeV
    from smodels.decomposition import decomposer
    
    filename = "gluino_squarks.slha"
    
    model = Model(BSMparticles = BSMList, SMparticles = SMList)
    model.updateParticles(inputFile = filename)
    toplist = decomposer.decompose(model, 0.005*fb, doCompress=True, doInvisible=True, minmassgap=5.*GeV)
    
    listOfAna = ['ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41','ATLAS-SUSY-2019-02']
    listOfAna = ['all']
    comb_dict = {"ATLAS-SUSY-2018-32":['ATLAS-SUSY-2018-41'], "ATLAS-SUSY-2018-41":['ATLAS-SUSY-2018-32', 'ATLAS-SUSY-2019-02'], "ATLAS-SUSY-2019-02":['ATLAS-SUSY-2018-41']}
    db = Database ( "official" )
    expresults = db.getExpResults(analysisIDs=listOfAna, dataTypes=['efficiencyMap','combined'])
    
    allPreds = theoryPredictionsFor(expresults, toplist, combinedResults=True)
    
    bC = BestCombinationFinder(combination_matrix = comb_dict, theoryPredictionList = allPreds, n_top = 1)
    bestThPred = bC.findBestCombination()
    
    
    if bestThPred is None : print("\n Model Point: ", filename, "  , No predictions")
    elif type(bestThPred) is list:
        i = 1
        for tp in bestThPred:
            try:print("\n Model Point : ", filename,  i, " rank combination: ", tp.describe())
            except AttributeError as e: print("\n Model Point: ", filename, i , "   rank combination: ", tp)
            i = i+1
    else:
        try:
            print("\n Model Point : ", filename, " best combination: ", bestThPred.describe())
        except AttributeError as e:
            print("\n Model Point: ", filename, "  , best theory prediction: ", bestThPred)
    
