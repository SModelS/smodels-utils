#!/usr/bin/env python3
from smodels.tools import runtime
runtime.modelFile = 'smodels.share.models.mssm'
from smodels.base.physicsUnits import GeV,fb
from smodels.theory import decomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor, TheoryPredictionsCombiner
from smodels.experiment.databaseObj import Database
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
from smodels.theory.model import Model
from combinations.combination_sahana.bestCombination import BestCombinationFinder
import glob
import pyslha
import sys; sys.path.append('.')
import os
from smodels.installation import installDirectory, version
from smodels.tools import modelTester
from smodels.tools import crashReport
from smodels.tools import smodelsLogging
from smodels.tools import runtime
from smodels import particlesLoader
from importlib import reload
import csv
import multiprocessing
from multiprocessing import Process
from multiprocessing import Queue
import time

'''Note : Before running the program, make sure to enter the path of the parameter.ini file and the outputdir according to the local computer path (in runSmodels function). The program is configured for specific paths only'''


class SModelsOutput(object):
    def __init__(self, inputfiles, queue):
        '''inputfiles: slha files for which an smodels output for the best combination is needed'''
        
        #list of inputfiles
        self.inputfiles = inputfiles
        self.database = Database('official')
        self.expresults = self.database.getExpResults(analysisIDs='all', dataTypes=['efficiencyMap','combined'])
        
        #define combination matrix
        self.combinationMatrix()
       
        
        #loop over inputfiles
        for file in self.inputfiles:
            self.file = file
            self.getBestCombination(queue)
        

        
    def combinationMatrix(self):
        '''define combination matrix'''
        
        #automatically combines with 8 TeV and 13 Tev CMS
        self.allo = {"ATLAS-SUSY-2018-05-ewk":['ATLAS-SUSY-2018-06', 'ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41',
                                  'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08', 'ATLAS-SUSY-2019-09',
                                  'CMS-SUS-20-004', 'CMS-SUS-21-002']}
        self.allo["ATLAS-SUSY-2018-06"] = ['ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2018-32"] = ['ATLAS-SUSY-2016-24', 'ATLAS-SUSY-2017-03', 'ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-08','ATLAS-SUSY-2019-09','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2018-41"] = ['ATLAS-SUSY-2016-24', 'ATLAS-SUSY-2017-03','ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-32',
                              'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','ATLAS-SUSY-2019-09','CMS-SUS-20-004',
                              'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2019-02"] = ['ATLAS-SUSY-2016-24', 'ATLAS-SUSY-2017-03', 'ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-08','ATLAS-SUSY-2019-09','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2019-08"] = ['ATLAS-SUSY-2016-24', 'ATLAS-SUSY-2017-03', 'ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-06','ATLAS-SUSY-2018-32',
                              'ATLAS-SUSY-2018-41','ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-09','CMS-SUS-20-004',
                              'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2019-09"] = ['ATLAS-SUSY-2018-05-ewk', 'ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41',
                              'ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','CMS-SUS-20-004', 'CMS-SUS-21-002']
        
        #automatically combines with 8 TeV and 13 Tev ATLAS
        self.allo["CMS-SUS-20-004"] = ['CMS-SUS-16-039', 'CMS-SUS-16-048']
        self.allo["CMS-SUS-21-002"] = ['CMS-SUS-16-039', 'CMS-SUS-16-048']
        
        #8 TeV
        self.allo["ATLAS-SUSY-2013-12"] = ['ATLAS-SUSY-2013-11']            #automatically combines with 13 TeV and 8 Tev CMS
        self.allo["ATLAS-SUSY-2013-11"] = ['ATLAS-SUSY-2013-12']
        self.allo["CMS-SUS-13-012"] = []                                    #automatically combines with 13 TeV and 8 Tev ATLAS
        
        #new 13 TeV low lumi
        #automatically combines with 8 TeV and 13 Tev CMS
        self.allo["ATLAS-SUSY-2016-24"] = ['ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41','ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','CMS-SUS-20-004', 'CMS-SUS-21-002']
        self.allo["ATLAS-SUSY-2017-03"] = ['ATLAS-SUSY-2018-32','ATLAS-SUSY-2018-41','ATLAS-SUSY-2019-02','ATLAS-SUSY-2019-08','CMS-SUS-20-004', 'CMS-SUS-21-002']
        
        #automatically combines with 8 TeV and 13 Tev ATLAS
        self.allo["CMS-SUS-16-039"] = ['CMS-SUS-16-048', 'CMS-SUS-20-004','CMS-SUS-21-002']
        self.allo["CMS-SUS-16-048"] = ['CMS-SUS-16-039', 'CMS-SUS-20-004','CMS-SUS-21-002']
        
        
    
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
    def getBestCombination(self,queue):
    
        '''main function where you compute the theory pred for the model point and get best combination'''
        
        #define start time
        process_st = time.process_time()
        
        sigmacut = 0.005*fb
        mingap = 5.*GeV
        model = Model(BSMparticles = BSMList, SMparticles = SMList)
        slhafile = self.file
        model.updateParticles(inputFile = slhafile)
        toplist = decomposer.decompose(model, sigmacut, doCompress=True, doInvisible=True, minmassgap=mingap)
        allPreds = theoryPredictionsFor(self.expresults, toplist, combinedResults=True)                         #TPred List object
        print("\n Theory Predictions computed, finding best combination of theory prediction")
        
        #get the best combination
        bC = BestCombinationFinder(combination_matrix = self.allo, theoryPredictionList = allPreds, n_top=1)
        bestThPred = bC.findBestCombination()
            
        #get masses of bsm particles from slha file
        self.getMassFromSlhafile(self.file)
        filename = self.file.split('/')[-1]
                
        #if there are no tp
        if bestThPred == []:
            print("M_C1: ", self.m_c1, "\t M_N1: ", self.m_n1, "\t Combination: None")
            print("Not running SModelS on file as no tp available")
            process_et = time.process_time()
            time_process = time.strftime("%H:%M:%S", time.gmtime(process_et - process_st))
            
            #put values for columns according to summary ouptput
            queue.put([filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2] + ['N/A']*7 + [time_process])
            #print("Queue worked!")
            #return out
            #self.out.write('\n {}, \t\t {}, \t {}, \t {}, \t {}, \t {}, \t {},  \t N/A, \t \t \t N/A, \t\t\t N/A, \t N/A, \t N/A, \t N/A, \t N/A'.format(filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2))
        
        else:
            print("M_C1: ", self.m_c1, "\t M_N1: ", self.m_n1, "\t Combination: ", bestThPred[0].analysisId())
            
            #run SModelS on best combination of tp
            self.runSmodels(bestThPred, self.file)
            
            '''depends which file you want to read'''
            #self.readSModelSFile(self.file)
            self.readPythonFile(self.file)
            
            process_et = time.process_time()
            time_process = time.strftime("%H:%M:%S", time.gmtime(process_et - process_st))
            
            #put values for columns according to summary ouptput
            queue.put([filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2, self.output_r[2], self.output_r[3], self.output_ana[-1], self.output_r[0], self.output_ana[0], self.output_r[1] ,self.output_ana[1], time_process])
            
            #print("Queue worked!")
            #return out
            #self.out.write('\n {}, \t\t {}, \t {}, \t {}, \t {}, \t {}, \t {}, \t {}, \t {}, \t\t\t {}, \t\t\t {}, \t {}, \t {}, \t {}'.format(filename, self.m_n1, self.m_n2,self.m_c1, self.m_n3, self.m_n4, self.m_c2, self.output_r[2], self.output_r[3], self.output_ana[-1], self.output_r[0], self.output_ana[0], self.output_r[1] ,self.output_ana[1]))
                
        
    def runSmodels(self, bestThPred, file):
        '''run SModelS on the best combination using parameter.ini '''

        parameterFile="%s/./parameters.ini"%(os.path.expanduser('~/smodels'))
        parser = modelTester.getParameters(parameterFile)
        
        #list of analyses present in combination dictionary
        listOfAna = [ana for ana in self.allo.keys()]
        listOfExpRes = self.database.getExpResults(analysisIDs=listOfAna, dataTypes=['efficiencyMap','combined'])
        #listOfExpRes = modelTester.loadDatabaseResults(parser, self.database)
        
        #set parser options for combineAnas
        parser.set('options', 'combineAnas', bestThPred[0].analysisId())
        parser.set('database', 'analyses', bestThPred[0].analysisId())
        
        print("Running SModelS on model point for the best combination of analyses")
        
        filename = file
        outputDir = '%s/combinations/combination_sahana/results'%(os.path.expanduser('~/smodels-utils'))
        
        #run SModelS with input file:
        output = modelTester.testPoint(filename, outputDir, parser, '2.3.0', listOfExpRes)
        
        print("\n Printing output")
        for x in output.values(): x.flush()
        
        
        
    def readSModelSFile(self, file):
        
        file = file.split('/')[-1]
        self.output_str = ['The highest r value is =', 'CMS analysis with highest available r_expected:', 'ATLAS analysis with highest available r_expected:', 'Combined Analyses:','combined r-value:','combined r-value (expected):']
        self.output_ana = ['Analysis with maximum obs r', 'Analysis with maximum exp r', 'Combined Analyses']
        
        #r = [max_r_obs, max_r_exp, comb_r_obs, comb_r_exp]
        self.output_r   = [0.0, 0.0, 0.0, 0.0]
        
        with open('results/%s.smodels'%(file), 'r') as file:
            csvreader = csv.reader(file)
            for row in csvreader:
                if row == []:continue
                elif self.output_str[0] in row[0]:                      #analysis with max r_obs
                    self.output_r[0] = row[0].split(' ')[6]
                    self.output_ana[0] = row[0].split(' ')[8]
                elif self.output_str[1] in row[0]:                      #cms analysis with max r_exp
                    expr = row[1].split('=')[-1]
                    if float(expr) > float(self.output_r[1]):           #check whether r_exp is max_r_exp
                        self.output_r[1] = expr
                        self.output_ana[1] = row[0].split(' ')[-1]
                elif self.output_str[2] in row[0]:                      #atlas analysis with max r_exp
                    expr = row[1].split('=')[-1]
                    if float(expr) > float(self.output_r[1]):           #check whether r_exp is max_r_exp
                        self.output_r[1] = expr
                        self.output_ana[1] = row[0].split(' ')[-1]
                elif self.output_str[3] in row[0]: self.output_ana[2] = [row[0].split(' ')[-1]] + row[1:]           #Analyses in combination
                elif self.output_str[4] in row[0]: self.output_r[2] = row[0].split(' ')[-1]                         #comb_r_obs
                elif self.output_str[5] in row[0]: self.output_r[3] = row[0].split(' ')[-1]                         #comb_r_exp
                    
        print("\n Analysis : ", self.output_ana)
        print("\n R-values : ", self.output_r)
        
    
    def readPythonFile(self, file):
            
        import ast
        
        file = file.split('/')[-1]
        f = open('results/%s.py'%(file), 'r')
        
        self.output_ana = ['Analysis with maximum obs r', 'Analysis with maximum exp r', 'Combined Analyses']
        
        #r = [max_r_obs, max_r_exp, comb_r_obs, comb_r_exp]
        self.output_r   = [0.0, 0.0, 0.0, 0.0]
        
        output_result = ast.literal_eval(f.readlines()[0].split('=')[-1])
        self.output_r[0] = sorted(output_result['ExptRes'], key=lambda x:x['r'], reverse=True)[0]['r']                      #get max_r_obs by sorting analysis acc to r_obs in decreasing order
        self.output_r[1] = sorted(output_result['ExptRes'], key=lambda x:x['r_expected'], reverse=True)[0]['r_expected']    #get max_r_exp by sorting analysis acc to r_exp in decreasing order
        self.output_r[2] = output_result['CombinedRes'][0]['r']                                                             #combined r_obs
        self.output_r[3] = output_result['CombinedRes'][0]['r_expected']                                                    #combined r_exp
        
        self.output_ana[0] = sorted(output_result['ExptRes'], key=lambda x:x['r'], reverse=True)[0]['AnalysisID']           #get ana with max r_obs
        self.output_ana[1] = sorted(output_result['ExptRes'], key=lambda x:x['r_expected'], reverse=True)[0]['AnalysisID']  #get ana with max_r_exp
        self.output_ana[2] = output_result['CombinedRes'][0]['AnalysisID']                                                  #get analysess in combination
        
        print("\n Analysis : ", self.output_ana)
        print("\n R-values : ", self.output_r)
        
        #print("\n All obs r values: ", [ l['r'] for l in sorted(output_result['ExptRes'], key=lambda x:x['r'], reverse=True)] )
        #print("\n All exp r values: ", [ l['r_expected'] for l in sorted(output_result['ExptRes'], key=lambda x:x['r_expected'], reverse=True)] )
        #print("\n Expt result :" ,output_result['ExptRes'])

        
        
            

if __name__ == "__main__":

    #Input file
    files = glob.glob ( "filter_slha/ew*slha" )
    
    #Select input files
    
    #Here list of list of files if you want to use multiprocess; otherwise can write 'files = files[:10]'
    files = [files[:2],files[2:4],files[4:6],files[6:8],files[8:10]]
    
    #Multiprocessing queue
    queue = Queue()

    #Without multiprocess you can run for single file or multiple files with
    #   sms = SModelsOutput(files,queue)
    #if running with single file, make sure to send the file as a list
    #u can uncomment the process lines if you dont want
    '''
    from multiprocessing import Pool
    
    pool_try = multiprocessing.Pool(processes = 5)
    
    pros = []
    for file in files:
        pro = pool_try.apply_async(SModelsOutput, args=(file,queue))
        pros.append(pro)
        
    print("pool started")
    pool_try.close()
    
    while True:
        done = sum([p.ready() for p in pros])
        if done == len(pros):break
        time.sleep(2)
    #pool_try.join()
    '''
    #define number of processes -> for now processes = 5
    #files contains list of multiple files to be sent to SModels
    
    
    
    processes = [Process(target=SModelsOutput, args=(file,queue)) for file in files]
    for process in processes:
        process.start()
        print("process started")
        
    for process in processes:
        process.join()
        if process.exitcode !=0 : print("Error for file: " ,files[processes.index(process)])
    
    #size = queue.qsize()
    #print('\n qs ', size)
    name = 'summary.csv'
    with open('results/summary.csv','w') as out:
        out.write('#SLHA_file\t M_N1\t M_N2\t M_C1\t M_N3\t M_N4\t M_C2\t r_obs(comb)\t r_exp(comb)\t Combination_of_Analyses\t max_r_obs\t Most_Constraining_Analysis\t max_r_exp\t Most_Senitive_Analysis\t Time Taken')
        
        #range -> total files in files/ queue size , here 10
        for i in range(10):
            item = queue.get()
            print(item)
            out.write('\n{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7],item[8],item[9],item[10],item[11],item[12],item[13], item[14]))


    
