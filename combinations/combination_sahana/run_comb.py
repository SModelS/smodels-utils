#!/usr/bin/env python3
from smodels.tools import runtime
runtime.modelFile = 'smodels.share.models.mssm'
from smodels.base.physicsUnits import GeV,fb
from smodels.decomposition import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor, TheoryPredictionsCombiner
from smodels.experiment.databaseObj import Database
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
from smodels.theory.model import Model
from combinations.bestCombination import BestCombinationFinder
import glob
import pyslha
import sys; sys.path.append('.')
from smodels.installation import installDirectory, version
from smodels.matching import modelTester
from smodels.tools import crashReport
from smodels.base import smodelsLogging
from smodels.tools import runtime
from smodels import particlesLoader
from importlib import reload
import csv

class SModelsOutput(object):
    def __init__(self):
        self.files = []
        
        
    def combinationMatrix(self):
        self.allo = {"ATLAS-SUSY-2018-05-ewk":['ATLAS-SUSY-2018-06', 'ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41',
                                  'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08', 'ATLAS-SUSY-2019-09',
                                  'CMS-SUS-20-004', 'CMS-SUS-21-002']}
        self.allo["ATLAS-SUSY-2018-06"] = ['ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2018-32"] = ['ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-08','ATLAS-SUSY-2019-09','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2018-41"] = ['ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-32',
                              'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','ATLAS-SUSY-2019-09','CMS-SUS-20-004',
                              'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2019-02"] = ['ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-08','ATLAS-SUSY-2019-09','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2019-08"] = ['ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-32',
                              'ATLAS-SUSY-2018-41','ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-09','CMS-SUS-20-004',
                              'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2019-09"] = ['ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','CMS-SUS-20-004', 'CMS-SUS-21-002']

        self.allo["CMS-SUS-20-004"] = []
        self.allo["CMS-SUS-21-002"] = []
        self.allo["ATLAS-SUSY-2013-12"] = []

    def readSlhafile(self):
        files = glob.glob ( "filter_slha/ew*slha" )
        self.files = files[:10]
    
    def getMassFromSlhafile(self,file):
        d = pyslha.read(file)
        self.m_n1 = abs(d.blocks['MASS'].get(1000022))             #neutralino_1
        self.m_n2 = abs(d.blocks['MASS'].get(1000023))            #neutralino_2
        self.m_c1 = abs(d.blocks['MASS'].get(1000024))            #chargino_1
        self.m_n3 = abs(d.blocks['MASS'].get(1000025))            #neutralino_3
        self.m_n4 = abs(d.blocks['MASS'].get(1000035))            #neutralino_4
        self.m_c2 = abs(d.blocks['MASS'].get(1000037))            #chargino_2
        '''
        if abs(self.m_nlsp - self.m_lsp) < 10.0:
            if abs(abs(d.blocks['MASS'].get(1000024)) - self.m_lsp) >= 10.0:
                self.m_nlsp = abs(d.blocks['MASS'].get(1000024))     #chargino_1
            else:
                self.m_nlsp = abs(d.blocks['MASS'].get(1000025))     #neutralino_3
        '''
    def getBestCombination(self):
    
        sigmacut = 0.005*fb
        mingap = 5.*GeV
        self.database = Database('official')
        expresults = self.database.getExpResults(analysisIDs='all', dataTypes=['efficiencyMap','combined'])
    
        self.combinationMatrix()
        self.readSlhafile()
        
        name = 'summary.csv'
        with open('results/summary.csv','w') as out:
            out.write('#SLHA_file \t\t M_N1 \t M_N2 \t M_C1 \t M_N3 \t M_N4 \t M_C2 \t r_obs(comb) \t r_exp(comb) \t\t\t Combination \t\t\t  \t max_r_obs \t Analysis \t max_r_exp \t Analysis')
    
            for file in self.files:
                model = Model(BSMparticles = BSMList, SMparticles = SMList)
                slhafile = file
                model.updateParticles(inputFile = slhafile)
                toplist = decomposer.decompose(model, sigmacut, doCompress=True, doInvisible=True, minmassgap=mingap)
                allPreds = theoryPredictionsFor(expresults, toplist, combinedResults=True)
                print("\n Theory Predictions computed, finding best combination of theory prediction")
        
                bC = BestCombinationFinder(combination_matrix = self.allo, theoryPredictionList = allPreds, n_top=1)
                bestThPred = bC.findBestCombination()
            
                self.getMassFromSlhafile(file)
                filename = file.split('/')[-1]
                
                #make python output too
                if bestThPred == []:
                    print("\n M_C1: ", self.m_c1, "\t M_N1: ", self.m_n1, "\t Combination: None")
                    print("\n Not running SModelS on file as no tp available")
                    out.write(f'\n {filename}, \t\t {self.m_n1}, \t {self.m_n2}, \t {self.m_c1}, \t {self.m_n3}, \t {self.m_n4}, \t {self.m_c2},  \t N/A, \t \t \t N/A, \t\t\t N/A, \t N/A, \t N/A, \t N/A, \t N/A')
        
                else:
                    print("\n M_C1: ", self.m_c1, "\t M_N1: ", self.m_n1, "\t Combination: ", bestThPred[0].analysisId())
                    self.runSmodels(bestThPred, file)
                    self.readSModelSFile(file)
                    out.write(f'\n {filename}, \t\t {self.m_n1}, \t {self.m_n2}, \t {self.m_c1}, \t {self.m_n3}, \t {self.m_n4}, \t {self.m_c2}, \t {self.output_r[2]}, \t {self.output_r[3]}, \t\t\t {self.output_ana[-1]}, \t\t\t {self.output_r[0]}, \t {self.output_ana[0]}, \t {self.output_r[1]}, \t {self.output_ana[1]}')
                
        
    def runSmodels(self, bestThPred, file):
        parameterFile="/Users/sahananarasimha/smodels/./parameters.ini"
        parser = modelTester.getParameters(parameterFile)
        
        #database, databaseVersion = modelTester.loadDatabase(parser,db=None)
        listOfAna = [ana for ana in self.allo.keys()]
        listOfExpRes = self.database.getExpResults(analysisIDs=listOfAna, dataTypes=['efficiencyMap','combined'])
        #listOfExpRes = modelTester.loadDatabaseResults(parser, self.database)
        
        parser.set('options', 'combineAnas', bestThPred[0].analysisId())
        parser.set('database', 'analyses', bestThPred[0].analysisId())
        
        print("\n Running SModelS on model point for the combination")
        
        filename = file
        outputDir = '/Users/sahananarasimha/smodels-utils/combinations/results'
        #run SModelS with input file:
        output = modelTester.testPoint(filename, outputDir, parser, '2.3.0', listOfExpRes)
        
        print("\n Printing output")
        for x in output.values(): x.flush()
        
        
        
    def readSModelSFile(self, file):
        
        file = file.split('/')[-1]
        self.output_str = ['The highest r value is =', 'CMS analysis with highest available r_expected:', 'ATLAS analysis with highest available r_expected:', 'Combined Analyses:','combined r-value:','combined r-value (expected):']
        self.output_ana = ['Analysis with maximum obs r', 'Analysis with maximum exp r', 'Combined Analyses']
        self.output_r   = [0.0, 0.0, 0.0, 0.0]
        with open(f'results/{file}.smodels', 'r') as file:
            csvreader = csv.reader(file)
            for row in csvreader:
                if row == []:continue
                elif self.output_str[0] in row[0]:
                    self.output_r[0] = row[0].split(' ')[6]
                    self.output_ana[0] = row[0].split(' ')[8]
                elif self.output_str[1] in row[0]:
                    expr = row[1].split('=')[-1]
                    if float(expr) > float(self.output_r[1]):
                        self.output_r[1] = expr
                        self.output_ana[1] = row[0].split(' ')[-1]
                elif self.output_str[2] in row[0]:
                    expr = row[1].split('=')[-1]
                    if float(expr) > float(self.output_r[1]):
                        self.output_r[1] = expr
                        self.output_ana[1] = row[0].split(' ')[-1]
                elif self.output_str[3] in row[0]: self.output_ana[2] = [row[0].split(' ')[-1]] + row[1:]
                elif self.output_str[4] in row[0]: self.output_r[2] = row[0].split(' ')[-1]
                elif self.output_str[5] in row[0]: self.output_r[3] = row[0].split(' ')[-1]
                    
        print("\n Analysis : ", self.output_ana)
        print("\n R-values : ", self.output_r)

if __name__ == "__main__":
        
    sm = SModelsOutput()
    sm.getBestCombination()
    #sm.readSModelSFile('ew_yzyxds4m.slha')
    
    
