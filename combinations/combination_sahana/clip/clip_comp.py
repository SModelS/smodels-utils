#!/usr/bin/env python3
import sys;
import os
sys.path.insert(0, os.path.expanduser("~/git/smodels-utils"))
sys.path.insert(0, os.path.expanduser("~/git/smodels"))
from combinations.combination_sahana.bestCombination import BestCombinationFinder
from smodels.tools import runtime
runtime.modelFile = 'smodels.share.models.mssm'
from smodels.tools.physicsUnits import GeV,fb
from smodels.theory import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor, TheoryPredictionsCombiner
from smodels.experiment.databaseObj import Database
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
from smodels.theory.model import Model
from smodels.installation import installDirectory, version
from smodels.tools import modelTester
from smodels.tools import crashReport
from smodels.tools import smodelsLogging
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
#rom smodels.tools.smodelsLogging import logger
import logging
logger = logging.getLogger(__name__)
#logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
#clip program

'''Note : Before running the program, make sure to enter the path of the parameter.ini file and the outputdir according to the local computer path (in runSmodels function). The program is configured for specific paths only'''

class SModelsOutput(object):
    def __init__(self, inputfiles, queue, clip, path_name):
        '''inputfiles: list of slha files for which an smodels output for the best combination is needed'''
        self.inputfiles = inputfiles
        self.database = Database('official')
        self.expresults = self.database.getExpResults(analysisIDs='all', dataTypes=['efficiencyMap','combined'], txnames=['TChi*'])
        self.combinationMatrix()
        
        #if using clip cluster
        if clip == 'y': self.clip = True
        else: self.clip = False
        
        #path to output_dir
        self.path_name = path_name
        
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

        self.allo["CMS-SUS-20-004"] = ['CMS-SUS-16-039','CMS-SUS-16-039-agg', 'CMS-SUS-16-048']
        self.allo["CMS-SUS-21-002"] = ['CMS-SUS-16-039','CMS-SUS-16-039-agg', 'CMS-SUS-16-048']
        
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
        self.allo["CMS-SUS-16-039-agg"] = ['CMS-SUS-16-048','CMS-SUS-20-004','CMS-SUS-21-002']
        self.allo["CMS-SUS-16-048"] = ['CMS-SUS-16-039', 'CMS-SUS-16-039-agg','CMS-SUS-20-004','CMS-SUS-21-002']
        

    
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
        
        #if (abs(self.m_c1 - self.m_n1) >=5 and abs(self.m_c1 - self.m_n1) <=10) or (abs(self.m_n2 - self.m_n1) >=5 and abs(self.m_c1 - self.m_n1) <=10)
        
    def getBestCombination(self, queue):
        '''main function where you compute the theory pred for the model point and get best combination'''
    
       
        
        sigmacut = 0.001*fb
        mingap = 10.*GeV
        
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
            logging.warning("Not running SModelS on %s as no tp available"%(filename))
            
            #if tp present but not in combination, make a note
            notp_id = [notp.analysisId() for notp in allPreds]
            
            #self.runSmodels(bestThPred, self.file)            
            #self.readSModelSFile(self.file)
            #self.readPythonFile(self.file)
            
            queue.put([filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2] + ['-1']*7 + [self.M1, self.M2, self.mu, self.tanb,notp_id])
            
        
        else:
            print("M_C1: ", self.m_c1, "\t M_N1: ", self.m_n1, "\t Combination: ", bestThPred[0].analysisId())
            self.runSmodels(bestThPred, self.file)
            
            #choose if you want to read smodels or python file
            #self.readSModelSFile(self.file)
            self.readPythonFile(self.file)
            
            queue.put([filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2, self.output_r[2], self.output_r[3], self.output_ana[-1], self.output_r[0], self.output_ana[0], self.output_r[1] ,self.output_ana[1], self.M1, self.M2, self.mu, self.tanb]+['-1'])
            
            #print("Queue worked!")
            #return out
            #self.out.write('\n {}, \t\t {}, \t {}, \t {}, \t {}, \t {}, \t {}, \t {}, \t {}, \t\t\t {}, \t\t\t {}, \t {}, \t {}, \t {}'.format(filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2, self.output_r[2], self.output_r[3], self.output_ana[-1], self.output_r[0], self.output_ana[0], self.output_r[1] ,self.output_ana[1]))
                
        
    def runSmodels(self, bestThPred, file):
        '''run SModelS on the best combination'''
        filename = self.file.split('/')[-1]
        
        #enter path of parameters.ini file
        parameterFile="%s/./parameters.ini"%(os.path.expanduser('~/git/smodels'))
        parser = modelTester.getParameters(parameterFile)
        
        #listOfAna = [ana for ana in self.allo.keys()]
        #listOfExpRes = self.database.getExpResults(analysisIDs=listOfAna, dataTypes=['efficiencyMap','combined'])
        
        #if bestThPred == []: parser.set('options', 'combineAnas', 'False')
        parser.set('options', 'combineAnas', bestThPred[0].analysisId())
        
        print("Running SModelS on model point for the best combination")
        #logging.INFO("Running SModelS on %s for the best combination"%(filename))
        
        
        #enter path of output dir below
        if self.clip: outputDir = '/scratch-cbe/users/sahana.narasimha/git/smodels-utils/combinations/combination_sahana/clip/results_3_10GeV'
        elif '~' in path_name: outputDir = os.path.expanduser('~') + path_name.split('~')[-1] 
        else: outputDir = path_name
        #outputDir = '/users/sahana.narasimha/git/smodels-utils/combinations/combination_sahana/clip/results_2'
        
        #run SModelS with input file:
        output = modelTester.testPoint(file, outputDir, parser, '2.3.0', self.expresults)
        
        print("\n Printing output")
        #logging.INFO("Printing output for %s"%(filename))
        
        for x in output.values(): x.flush()
        
        
        
    def readSModelSFile(self, file):
        
        file = file.split('/')[-1]
        self.output_str = ['The highest r value is =', 'CMS analysis with highest available r_expected:', 'ATLAS analysis with highest available r_expected:', 'Combined Analyses:','combined r-value:','combined r-value (expected):']
        self.output_ana = ['Analysis with maximum obs r', 'Analysis with maximum exp r', 'Combined Analyses']
        self.output_r   = [0.0, 0.0, 0.0, 0.0]
        with open('results_3_10GeV/%s.smodels'%(file), 'r') as file:
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
        f = open('results_3_10GeV/%s.py'%(file), 'r')
        
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
        
        
def getMassFromSlhafile(files):
    
    new_list = []
    for file in files:
        d = pyslha.read(file)
        
    #EWino Masses
        m_n1 = abs(d.blocks['MASS'].get(1000022))            #neutralino_1
        m_n2 = abs(d.blocks['MASS'].get(1000023))            #neutralino_2
        m_c1 = abs(d.blocks['MASS'].get(1000024))            #chargino_1
    
        if ((m_c1 - m_n1) >=5. and (m_c1 - m_n1) <=10.) or ((m_n2 - m_n1) >=5. and (m_n2 - m_n1) <=10.):new_list.append(file)
        
    return new_list
    

if __name__ == "__main__":
    
    
    #can remove some parameters if you want, if you already have a list of inputfiles in mind
    import argparse
    ap = argparse.ArgumentParser( description=
            "Run SModelS over SLHA/LHE input files." )
    ap.add_argument('-n', '--num_of_files', help='number of SLHA files to run, number should be multiple of 10; default=100', default = 100, type = int)
    ap.add_argument('-f', '--filebatch',
            help='batch number of SLHA files in 2ndFilter_slha_nlo; If num_of_files=100, 0 -> 0-99, 1->100-199 and so on', required=True, type=int)
    ap.add_argument('-s', '--summaryfilename',
            help='name of output summary file; default=summary', default='summary', type=str)
    ap.add_argument('-p', '--path_to_outputdir',
            help='path to outputdir; default = ~/git/smodels-utils/combinations/combination_sahana/results', default='~/git/smodels-utils/combinations/combination_sahana/results', type=str)
    ap.add_argument('-c', '--clip_cluster',
            help='if using clip cluster, type \'y\'; default=n', default='n', type=str)
    
    args = ap.parse_args()
    fs = args.filebatch 
    numf = args.num_of_files
    output_name = args.summaryfilename + '.csv'
    path_name = args.path_to_outputdir
    clip = args.clip_cluster
    
    files = glob.glob ( "2ndFilter_slha_nlo/ew*slha" )
    #new_files = getMassFromSlhafile(files)
    #files = new_files
    #print(new_files)
    #print(len(new_files))
    
    
    #files = files[fs*100:(fs+1)*100]
    #files = [files[0:10],files[10:20],files[20:30],files[30:40],files[40:50],files[50:60],files[60:70],files[70:80],files[80:90],files[90:100]]
    #files should be a list of files, can input the files that you want here
    files = files[fs*numf:(fs+1)*numf]
    
    #split list of files into 10 lists - 
    #can modify this if you want. BE CAREFUL IF YOU ARE RUNNING WITH LESS THAN 10 FILES or number not a multiple of ten, change step acccordingly
    step = int(numf/10)
    files = [files[x:(x+step)] for x in range(0,numf,step)]
    #Example: for 20 files: files = [files[0:2],files[2:4],files[4:6],files[6:8],files[8:10],files[10:12],files[12:14],files[14:16],files[16:18],files[18:20]
    
    #queue to share info between diff processes
    queue = Queue()

    #time taken for the whole program to run 
    process_st = time.process_time()
    
    #num of processes = num of list of files in files
    processes = [Process(target=SModelsOutput, args=(file,queue,clip,path_name)) for file in files]
    for process in processes:
        process.start()
        logger.info("Process started")
        
    for process in processes:
        process.join()
        if process.exitcode !=0 : 
            new_files = files[processes.index(process)]
            new_process = [Process(target=SModelsOutput, args=([file],queue,clip,path_name)) for file in new_files]
            for np in new_process: np.start()
            for np in new_process:
                np.join()
                if np.exitcode !=0:
                    logger.error("Error for model point: %s"%(new_files[new_process.index(np)]))
                    queue.put([new_files[new_process.index(np)]]+['Error']*19)
                    
                
    
    
    logger.warning("All Processes done")
    
    process_et = time.process_time()
    time_process = time.strftime("%H:%M:%S", time.gmtime(process_et - process_st))
    
    with open('results_3_10GeV/%s'%(output_name),'w') as out:
        out.write('#SLHA_file\tm_N1\tm_N2\tm_C1\tm_N3\tm_N4\tm_C2\tr_obs(comb)\tr_exp(comb)\tCombination\tmax_r_obs\tMost_Constraining_Analysis\tmax_r_exp\tMost_sensitive_Analysis\tM1\tM2\tMu\tTan_Beta\tTp_not_included_in_combination')
        for i in range(numf):
            item = queue.get()
            print(item)
            out.write('\n{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7],item[8],item[9],item[10],item[11],item[12],item[13],item[14],item[15],item[16],item[17],item[18]))
        
        out.write('\n#Has_files_from_%s_to_%s; Time taken %s'%(fs*numf,(fs+1)*numf,time_process))
        out.close()
        
    logger.warning("Summary file written")
    
           
    
    
