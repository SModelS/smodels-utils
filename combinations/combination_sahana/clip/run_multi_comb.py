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
from smodels.installation import installDirectory, version
from smodels.matching import modelTester
from smodels.tools import crashReport
from smodels.base import smodelsLogging
from smodels.tools import runtime
from smodels import particlesLoader
from importlib import reload
import sys; sys.path.append('.')
import os
import glob
import pyslha
import csv
import logging
import time
import multiprocessing
from multiprocessing import Process
from multiprocessing import Queue
logger = logging.getLogger(__name__)

'''extra/different for clip'''
sys.path.insert(0, os.path.expanduser("~/git/smodels"))
from bestCombination import BestCombinationFinder

'''Note : Before running the program, make sure to enter the path of the parameter.ini file and the outputdir according to the local computer path (in runSmodels function). The program is configured for specific paths only'''

class SModelsOutput(object):
    def __init__(self, inputfile):
        '''inputfile: slha file for which an smodels output for the best combination is needed'''
        self.file = inputfile
        self.database = Database('official')
        self.expresults = self.database.getExpResults(analysisIDs='all', dataTypes=['efficiencyMap','combined'])
        self.combinationMatrix()
        
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
    def getBestCombination(self, queue):
        '''main function where you compute the theory pred for the model point and get best combination'''
    
        process_st = time.process_time()
        
        sigmacut = 0.005*fb
        mingap = 5.*GeV
        
        model = Model(BSMparticles = BSMList, SMparticles = SMList)
        slhafile = self.file
        model.updateParticles(inputFile = slhafile)
        toplist = decomposer.decompose(model, sigmacut, doCompress=True, doInvisible=True, minmassgap=mingap)
        allPreds = theoryPredictionsFor(self.expresults, toplist, combinedResults=True)
        print("\n Theory Predictions computed, finding best combination of theory prediction")
        
        bC = BestCombinationFinder(combination_matrix = self.allo, theoryPredictionList = allPreds, n_top=1)
        bestThPred = bC.findBestCombination()
            
        self.getMassFromSlhafile(self.file)
        filename = self.file.split('/')[-1]
                
                #make python output too
        if bestThPred == []:
            print("M_C1: ", self.m_c1, "\t M_N1: ", self.m_n1, "\t Combination: None")
            print("Not running SModelS on file as no tp available")
            logger.info("Not running SModelS on %s as no tp available"%(filename))
            
            process_et = time.process_time()
            time_process = time.strftime("%H:%M:%S", time.gmtime(process_et - process_st))
            queue.put([filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2] + ['N/A']*7 + [time_process])
            #print("Queue worked!")
            #return out
            #self.out.write('\n {}, \t\t {}, \t {}, \t {}, \t {}, \t {}, \t {},  \t N/A, \t \t \t N/A, \t\t\t N/A, \t N/A, \t N/A, \t N/A, \t N/A'.format(filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2))
        
        else:
            print("M_C1: ", self.m_c1, "\t M_N1: ", self.m_n1, "\t Combination: ", bestThPred[0].analysisId())
            self.runSmodels(bestThPred, self.file)
            self.readSModelSFile(self.file)
            
            process_et = time.process_time()
            time_process = time.strftime("%H:%M:%S", time.gmtime(process_et - process_st))
            queue.put([filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2, self.output_r[2], self.output_r[3], self.output_ana[-1], self.output_r[0], self.output_ana[0], self.output_r[1] ,self.output_ana[1], time_process])
            
            #print("Queue worked!")
            #return out
            #self.out.write('\n {}, \t\t {}, \t {}, \t {}, \t {}, \t {}, \t {}, \t {}, \t {}, \t\t\t {}, \t\t\t {}, \t {}, \t {}, \t {}'.format(filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2, self.output_r[2], self.output_r[3], self.output_ana[-1], self.output_r[0], self.output_ana[0], self.output_r[1] ,self.output_ana[1]))
                
        
    def runSmodels(self, bestThPred, file):
        '''run SModelS on the best combination'''
        filename = self.file.split('/')[-1]
        
        #enter path of parameters.ini file
        parameterFile="%s/./parameters.ini"%(os.path.expanduser('~/git/smodels'))
        parser = modelTester.getParameters(parameterFile)
        
        listOfAna = [ana for ana in self.allo.keys()]
        listOfExpRes = self.database.getExpResults(analysisIDs=listOfAna, dataTypes=['efficiencyMap','combined'])
        
        parser.set('options', 'combineAnas', bestThPred[0].analysisId())
        parser.set('database', 'analyses', bestThPred[0].analysisId())
        
        print("Running SModelS on model point for the best combination")
        logger.info("Running SModelS on %s for the best combination"%(filename))
        
        
        #enter path of output dir below
        outputDir = '/scratch-cbe/users/sahana.narasimha/git/smodels-utils/combinations/combination_sahana/clip/results'
        #run SModelS with input file:
        output = modelTester.testPoint(file, outputDir, parser, '2.3.0', listOfExpRes)
        
        print("\n Printing output")
        logger.info("Printing output for %s"%(filename))
        
        for x in output.values(): x.flush()
        
        
        
    def readSModelSFile(self, file):
        
        file = file.split('/')[-1]
        self.output_str = ['The highest r value is =', 'CMS analysis with highest available r_expected:', 'ATLAS analysis with highest available r_expected:', 'Combined Analyses:','combined r-value:','combined r-value (expected):']
        self.output_ana = ['Analysis with maximum obs r', 'Analysis with maximum exp r', 'Combined Analyses']
        self.output_r   = [0.0, 0.0, 0.0, 0.0]
        with open('results/%s.smodels'%(file), 'r') as file:
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

    files = glob.glob ( "filter_slha/ew*slha" )
    #iles = files[:50]
    files = files[50:100]
    queue = Queue()

    sms = [SModelsOutput(file) for file in files]
 
    processes = [Process(target=sm.getBestCombination, args=(queue,)) for sm in sms]
    for process in processes:
        process.start()
        logger.info("Process started")
        
    for process in processes:
        process.join()
        if process.exitcode !=0 : logger.error("Error for model point: ",files[processes.index(process)])
    
    #size = queue.qsize()
    #print('\n qs ', size)
    #ame = 'summary.csv'
    name = 'summary_2.csv'
    with open('results/summary_2.csv','w') as out:
        out.write('#SLHA_file \t M_N1 \t M_N2 \t M_C1 \t M_N3 \t M_N4 \t M_C2 \t r_obs(comb) \t r_exp(comb) \t Combination \t max_r_obs \t Analysis \t max_r_exp \t Analysis \t Time taken')
        for i in range(len(files)):
            item = queue.get()
            print(item)
            out.write('\n {} \t {} \t {} \t {} \t {} \t {} \t {} \t {} \t {} \t {} \t {} \t {} \t {} \t {} \t {}'.format(item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7],item[8],item[9],item[10],item[11],item[12],item[13],item[14]))
                      
                   
 
            #sm.getBestCombination(file)
    #sm.readSModelSFile('ew_yzyxds4m.slha')
    
    
