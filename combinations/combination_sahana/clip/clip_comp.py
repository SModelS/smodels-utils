#!/usr/bin/env python3
import sys;
import os
sys.path.insert(0, os.path.expanduser("~/git/smodels-utils"))
sys.path.insert(0, os.path.expanduser("~/git/smodels"))
from combinations.combination_sahana.bestCombination import BestCombinationFinder
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
sys.path.append('.')
import glob
import pyslha
import csv
import time
import multiprocessing
from multiprocessing import Process
from multiprocessing import Queue
#rom smodels.base.smodelsLogging import logger
import logging
logger = logging.getLogger(__name__)
#logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
#clip program

'''Note : Before running the program, make sure to enter the path of the parameter.ini file and the outputdir according to the local computer path (in runSmodels function). The program is configured for specific paths only'''

class SModelsOutput(object):
    def __init__(self, inputfiles, queue):
        '''inputfile: slha file for which an smodels output for the best combination is needed'''
        self.inputfiles = inputfiles
        self.database = Database('official')
        self.expresults = self.database.getExpResults(analysisIDs='all', dataTypes=['efficiencyMap','combined'])
        self.combinationMatrix()
        
        for file in self.inputfiles:
            self.file = file
            self.getBestCombination(queue)
            
    def combinationMatrix(self):
        self.allo = {"ATLAS-SUSY-2018-05-ewk":['ATLAS-SUSY-2018-06', 'ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41',
                                  'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08', 'ATLAS-SUSY-2019-09',
                                  'CMS-SUS-20-004', 'CMS-SUS-21-002']}
        self.allo["ATLAS-SUSY-2018-06"] = ['ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2018-32"] = ['ATLAS-SUSY-2016-24', 'ATLAS-SUSY-2017-03','ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-08','ATLAS-SUSY-2019-09','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2018-41"] = ['ATLAS-SUSY-2016-24', 'ATLAS-SUSY-2017-03','ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-32',
                              'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','ATLAS-SUSY-2019-09','CMS-SUS-20-004',
                              'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2019-02"] = ['ATLAS-SUSY-2016-24', 'ATLAS-SUSY-2017-03','ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-08','ATLAS-SUSY-2019-09','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2019-08"] = ['ATLAS-SUSY-2016-24', 'ATLAS-SUSY-2017-03','ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-32',
                              'ATLAS-SUSY-2018-41','ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-09','CMS-SUS-20-004',
                              'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2019-09"] = ['ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','CMS-SUS-20-004', 'CMS-SUS-21-002']

        self.allo["CMS-SUS-20-004"] = ['CMS-SUS-16-039','CMS-SUS-16-048']
        self.allo["CMS-SUS-21-002"] = ['CMS-SUS-16-039','CMS-SUS-16-048']
        
        #8 TeV
        self.allo["ATLAS-SUSY-2013-12"] = ['ATLAS-SUSY-2013-11']
        self.allo["ATLAS-SUSY-2013-11"] = ['ATLAS-SUSY-2013-12']
        self.allo["CMS-SUS-13-012"] = []
        
        #new 13 TeV low lumi
        self.allo["ATLAS-SUSY-2016-24"] = ['ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2017-03"] = ['ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["CMS-SUS-16-039"] = ['CMS-SUS-16-048','CMS-SUS-20-004','CMS-SUS-21-002']
        self.allo["CMS-SUS-16-048"] = ['CMS-SUS-16-039','CMS-SUS-20-004','CMS-SUS-21-002']
        

    
    def getMassFromSlhafile(self,file):
        d = pyslha.read(file)
        
        #EWino Masses
        self.m_n1 = abs(d.blocks['MASS'].get(1000022))            #neutralino_1
        self.m_n2 = abs(d.blocks['MASS'].get(1000023))            #neutralino_2
        self.m_c1 = abs(d.blocks['MASS'].get(1000024))            #chargino_1
        self.m_n3 = abs(d.blocks['MASS'].get(1000025))            #neutralino_3
        self.m_n4 = abs(d.blocks['MASS'].get(1000035))            #neutralino_4
        self.m_c2 = abs(d.blocks['MASS'].get(1000037))            #chargino_2
        
        #EWino Parameters
        self.M1 = abs(d.blocks['EXTPAR'].get(1))                  #M1
        self.M2 = abs(d.blocks['EXTPAR'].get(2))                  #M2
        self.mu = abs(d.blocks['EXTPAR'].get(23))                 #mu
        self.tanb = abs(d.blocks['EXTPAR'].get(25))               #tan_beta
        
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
        #logging.INFO("Theory Predictions computed, finding best combination of theory prediction")
        
        bC = BestCombinationFinder(combination_matrix = self.allo, theoryPredictionList = allPreds, n_top=1)
        bestThPred = bC.findBestCombination()
            
        self.getMassFromSlhafile(self.file)
        filename = self.file.split('/')[-1]
                
                
        if bestThPred == []:
            print("M_C1: ", self.m_c1, "\t M_N1: ", self.m_n1, "\t Combination: None")
            print("Not running SModelS on file as no tp available")
            logging.warning(f"Not running SModelS on {filename} as no tp available")
            
            process_et = time.process_time()
            time_process = time.strftime("%H:%M:%S", time.gmtime(process_et - process_st))
            queue.put([filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2] + ['-1']*7 + [time_process])
            
        
        else:
            print("M_C1: ", self.m_c1, "\t M_N1: ", self.m_n1, "\t Combination: ", bestThPred[0].analysisId())
            self.runSmodels(bestThPred, self.file)
            
            #self.readSModelSFile(self.file)
            self.readPythonFile(self.file)
            
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
        parameterFile=f"{os.path.expanduser('~/git/smodels')}/./parameters.ini"
        parser = modelTester.getParameters(parameterFile)
        
        listOfAna = [ana for ana in self.allo.keys()]
        listOfExpRes = self.database.getExpResults(analysisIDs=listOfAna, dataTypes=['efficiencyMap','combined'])
        
        parser.set('options', 'combineAnas', bestThPred[0].analysisId())
        parser.set('database', 'analyses', bestThPred[0].analysisId())
        
        print("Running SModelS on model point for the best combination")
        #logging.INFO("Running SModelS on %s for the best combination"%(filename))
        
        
        #enter path of output dir below
        outputDir = '/scratch-cbe/users/sahana.narasimha/git/smodels-utils/combinations/combination_sahana/clip/results_2'
        #outputDir = '/users/sahana.narasimha/git/smodels-utils/combinations/combination_sahana/clip/results_2'
        
        #run SModelS with input file:
        output = modelTester.testPoint(file, outputDir, parser, '2.3.0', listOfExpRes)
        
        print("\n Printing output")
        #logging.INFO("Printing output for %s"%(filename))
        
        for x in output.values(): x.flush()
        
        
        
    def readSModelSFile(self, file):
        
        file = file.split('/')[-1]
        self.output_str = ['The highest r value is =', 'CMS analysis with highest available r_expected:', 'ATLAS analysis with highest available r_expected:', 'Combined Analyses:','combined r-value:','combined r-value (expected):']
        self.output_ana = ['Analysis with maximum obs r', 'Analysis with maximum exp r', 'Combined Analyses']
        self.output_r   = [0.0, 0.0, 0.0, 0.0]
        with open(f'results_2/{file}.smodels', 'r') as file:
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
        
   
    def readPythonFile(self, file):
            
        import ast
        
        file = file.split('/')[-1]
        print('\n',file)
        f = open(f'results_2/{file}.py', 'r')
        
        self.output_ana = ['Analysis with maximum obs r', 'Analysis with maximum exp r', 'Combined Analyses']
        self.output_r   = [0.0, 0.0, 0.0, 0.0]
        
        output_result = ast.literal_eval(f.readlines()[0].split('=')[-1])
        self.output_r[0] = sorted(output_result['ExptRes'], key=lambda x:x['r'], reverse=True)[0]['r']
        self.output_r[1] = sorted(output_result['ExptRes'], key=lambda x:x['r_expected'], reverse=True)[0]['r_expected']
        self.output_r[2] = output_result['CombinedRes'][0]['r']
        self.output_r[3] = output_result['CombinedRes'][0]['r_expected']
        
        self.output_ana[0] = sorted(output_result['ExptRes'], key=lambda x:x['r'], reverse=True)[0]['AnalysisID']
        self.output_ana[1] = sorted(output_result['ExptRes'], key=lambda x:x['r_expected'], reverse=True)[0]['AnalysisID']
        self.output_ana[2] = output_result['CombinedRes'][0]['AnalysisID']
        
        print("\n Analysis : ", self.output_ana)
        print("\n R-values : ", self.output_r)

if __name__ == "__main__":
    
    
    import argparse
    

    """ Get the name of input SLHA file and parameter file """
    ap = argparse.ArgumentParser( description=
            "Run SModelS over SLHA/LHE input files." )
    ap.add_argument('-f', '--fileset',
            help='set of 100 SLHA files in 2ndFilter_slha_nlo; 0 -> 0-99, 1->100-199 and so on', required=True)
    ap.add_argument('-s', '--summaryfilename',
            help='name of summary file', required=True)
    
    args = ap.parse_args()
    
    files = glob.glob ( "2ndFilter_slha_nlo/ew*slha" )
    #iles = files[:50]
    fs = int(args.fileset) 
    files = files[fs*100:(fs+1)*100]
    files = [files[0:10],files[10:20],files[20:30],files[30:40],files[40:50],files[50:60],files[60:70],files[70:80],files[80:90],files[90:100]]
    
    #files = files[fs*10:(fs+1)*10]
    #files = [files[0:2],files[2:4],files[4:6],files[6:8],files[8:10]]
    
    #for file in files: print("\n",file)
    #output_name = args.summaryfilename + '.csv'
    #print(output_name)
    
    queue = Queue()

    #sms = [SModelsOutput(file) for file in files]
 
    processes = [Process(target=SModelsOutput, args=(file,queue)) for file in files]
    for process in processes:
        process.start()
        logger.info("Process started")
        
    for process in processes:
        process.join()
        if process.exitcode !=0 : logger.error("Error for model point: ",files[processes.index(process)])
    
  
    #0-50 in results/ summary 50-100 in summary_2 , 100-150 in summary_3 150-200 in summary_4, 200-300 in summary_5
    #0-100 in results_2/ summary
    #summary_6 has the same input files but only python output files to see how long tje pinting process takes
    #size = queue.qsize()
    #print('\n qs ', size)
    #ame = 'summary.csv'
    
    #sm = SModelsOutput(files)
    #output_name = 'summary_array2.csv'
    output_name = args.summaryfilename + '.csv'
    
    with open(f'results_2/{output_name}','w') as out:
        out.write(f'#Has files from {fs * 100} to {(fs + 1) * 100}')
        out.write('\n#SLHA_file\t M_N1\t M_N2\t M_C1\t M_N3\t M_N4\t M_C2\t r_obs(comb)\t r_exp(comb)\t Combination\t max_r_obs\t Most_Constraining_Analysis\t max_r_exp\t Most_sensitive_Analysis\t Time taken')
        for i in range(100):
            item = queue.get()
            print(item)
            out.write(f'\n{item[0]}\t{item[1]}\t{item[2]}\t{item[3]}\t{item[4]}\t{item[5]}\t{item[6]}\t{item[7]}\t{item[8]}\t{item[9]}\t{item[10]}\t{item[11]}\t{item[12]}\t{item[13]}\t{item[14]}')
        
        out.close()
                   
 
            #sm.getBestCombination(file)
    #sm.readSModelSFile('ew_yzyxds4m.slha')
    
    
