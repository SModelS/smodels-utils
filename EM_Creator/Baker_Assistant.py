"""
.. module:: Baker_Assistant.
        :synopsis: this module contains the main functions called by EM_baking
                   in order to produce Efficiency Maps

.. moduleauthor:: Federico Ambrogi <federico.ambrogi88@gmail.com>
"""

import argparse, datetime, sys, os , subprocess, pprint, shutil
from subprocess import call
from sys import stderr
from EM_Ingredients import * 
from Cards_Producer import *
import shutil
from shutil         import *
import datetime, sys, os


'''
This function simply looks for slha files contained in a certain directory.
'''
def SLHA_List_Creator(slhaDir):
    SLHA_List = []
    files_in_SLHAdirectory = os.listdir(slhaDir)
    for SLHA in files_in_SLHAdirectory:
       if '.slha' in SLHA and '~' not in SLHA:                        # TODO incude pyslha checker 
          SLHA_List.append(SLHA)
    SLHA_List.sort()
    return SLHA_List


'''
This function checks if the input directory containing the existing SLHA files is existing or not
'''
def NoSLHAInput_Breaker(slhaDir = ''):
    if not slhaDir:
       print 'The SLHA input folder is not correct! Please run again providing a valid directory!'
       sys.exit()
'''
This function checks if the file exists or not, and if not it continues to the next slha
''' 
def NoFile_Continue(File = ''):
    if (os.path.exists(File)):
       return True
    else :
       print 'The directory ' , File , ' is not correct! Will continue with the next SLHA'
       return False 

'''
This function takes as argument the "complete adress + name" of the folder you want to create.
First it checks is the directory exists; if it does, it renames it as the old name + the current time, in order to save it (--> might not be necessary)
'''
def Folder_Creator_Saver(out_dir = ''):
    now = datetime.datetime.now()
    now = str(now.month)+':'+str(now.day)+':'+str(now.year)+'_'+str(now.hour)+':'+str(now.minute)+':'+str(now.second)
    if (os.path.exists(out_dir) ):
       print 'The folder ',out_dir, ' already exists! Renaming the old existing directory'
       os.system('mv '+out_dir + ' ' + out_dir + '_'+ now )
       os.makedirs(out_dir)      
    elif not os.path.exists(out_dir):
       os.makedirs(out_dir)

def Folder_Creator(out_dir = ''):
    if not os.path.exists(out_dir):
       os.makedirs(out_dir)

'''
Mg5 Running
This function calls MG5; it requires the SLHA file that you want to process and the dictionary of parameters used by MG5 and Pythia (in EM_Ingredients.py).
The first step is the building of the MG5 process given as an input
The function checks if the process folder is already present in the user MG5 directory;
if not, the process is built brand new
Then the function 
1) Produces the txt file file to launch the tool  [" ./mg5 commands_file "]
2) copy the SLHA inside the folder Cards as a 'param_card.dat' (it requires the complete path of the SLHA)
3) produce the 'run_card' and 'pythia_card' from the input parameters
It will rename the run_01 folder as the name of the SLHA that it has used
'''

'''
This function retunrs the name of the MG5 process associated to the SLHA file.
By default it assumes the generation of one extra ISR
'''
def MG5_detProcess(slha='', extraISR ='1jet', homeDir= Home_Dir):
    txName = slha.split('_')[0]
    return txName+'_'+extraISR 

def Run_MG5( MG5Pythia_paramDic = '', slha_file = '', MG5dir = '' , templ_dir ='' , proc = ''):
    os.chdir(MG5dir)
    if (not os.path.isfile(templ_dir+'/MG5_Process_Cards/'+proc+'.txt') ):
       print 'The process card', proc, ' does not exists in the MG5 proc input folder!'
    if (not os.path.isdir(proc) ): 
       os.system('./bin/mg5 '+ templ_dir+'/MG5_Process_Cards/'+proc+'.txt')
    commands_file = MG5_commands_producer(proc)                             
    copyfile(slha_file , proc+'/Cards/param_card.dat' )                              
    MG5_Pythia_cards_producer(MG5Pythia_paramDic= MG5Pythia_paramDic, MG5dir= MG5dir, proc= proc, templ_dir= templ_dir )   # ext funct creating the run_card from the templ 
    if (os.path.isdir(proc+'/Events/run_01')):
       shutil.rmtree(proc+'/Events/run_01')
    os.system("./bin/mg5 "+commands_file)          

'''
Running MA5:
Ma5 takes the HEP file complete path as an input, and then runs the Delphes simulator to produce the ROOT files used for the Ma5 analyses
'''
def Run_MA5(ma5Dir ='', inputHEP=''):   
    shutil.copyfile(Home_Dir+'/Input/recasting_card.dat',ma5Dir+'/recasting_card.dat')   
    os.chdir(ma5Dir)
    MA5_commands_producer(inputHEP, MA5_path = ma5Dir)
    if (os.path.isdir('ANALYSIS_0')):   # Renaming the folder ANALYSIS_0 if it exists (so the data inside is not lost) TODO or actually remove it completely
       now = datetime.datetime.now()
       print 'The folder ANALYSIS_0 existed already; renamed it as Saved_ANALYSIS_0_' + str(now.month)+':'+str(now.day)+':'+str(now.year)+'_'+str(now.hour)+':'+str(now.minute) 
       shutil.move('ANALYSIS_0',  'Saved_ANALYSIS_0_' + str(now.month)+':'+str(now.day)+':'+str(now.year)+'_'+str(now.hour)+':'+str(now.minute) ) 
    os.system('./bin/ma5 -R -s MA5_commands_file.txt')

'''
Utilities to relocate the output from MG5 and MA5 - the (MG5+MA5 root files will be completely removed after the testing phase - only the MA5 analyses output will be stored)
'''
def MA5_Output_Relocator(ma5Dir = '', MA5_OutputDir = '' ):
    rootFile_path   = ma5Dir + '/ANALYSIS_0/Events'             # contains al the Delpheized root files
    ma5Output_Path  = ma5Dir + '/ANALYSIS_0/Output/defaultset'  # contains the MA5 analyses output
    if (os.path.isdir(MA5_OutputDir) ):			        # further check that the directory exists
       shutil.move(rootFile_path  , MA5_OutputDir+'/MA5_Delphes_RootFiles')
       shutil.move(ma5Output_Path , MA5_OutputDir+'/MA5_Analyses_Results') 
    if (os.path.isdir( MA5_Dir+'/ANALYSIS_0') ):                # removing the MA5 output after the relocation
       shutil.rmtree(MA5_Dir+'/ANALYSIS_0')

def MG5_Output_Relocator(mg5Out = '', MG5_OutputDir = ''):
    Folder_Creator(out_dir = MG5_OutputDir) 
    shutil.move(mg5Out, MG5_OutputDir+'/MG5Output') 

'''
This utility simply saves the EM_Ingredients.py used for the production;
this allows to retrive the information and parameters used to re-produce the EM
'''
def Info_Saver(author= '', outDir= '' , homeDir = Home_Dir ):
    now = datetime.datetime.now()
    now = str(now.month)+':'+str(now.day)+':'+str(now.year)+'_'+str(now.hour)+':'+str(now.minute) 
    logFile = open(outDir+'/EM_Baking_LogFile.txt','a')
    logFile.write('\n***** New Efficiency Map Production Log File *****\n')
    logFile.write('The EM production was made by: ' + author + ' , on ' + now + '\n')
    logFile.write('Copy of the EM_Ingredients.py used: \n')
    Ingredients = open(Home_Dir+'/EM_Ingredients.py','r')
    for line in Ingredients:
        logFile.write(line)
    logFile.write('\n\n\n***** End of the Report ***** \n\n\n')
    logFile.close()  

'''
Info saver: is the Save_PartialOutput_Switch is not set to 'ON', it will erase all the partial MG5 and MA5 output.
The only output saved will the the MA5 analyses output and the MG5 banner card.
'''
def PartialOutput_Saver(switch = 'OFF', outFolder= '' ):
    if (switch != 'ON'):
       for File in os.listdir(outFolder+'/MG5Output'):
           if 'banner' not in File:
              os.remove(outFolder +'/MG5Output/'+ File)
       if os.path.isdir(outFolder+'/MA5_Delphes_RootFiles'): shutil.rmtree(outFolder+'/MA5_Delphes_RootFiles' )
       
'''
Below new facilities to run CheckMate
'''
def Run_CM(cmDir ='', inputHEP=''):
    os.chdir(cmDir)
    CM_commands_producer(inputHEP, 0.025, 0.004) #FIXME dummy cross section and error, not strictly needed for efficiency!
    CM_answer_producer()
    if (os.path.isdir('results/EM_baking')):   # Renaming the folder EM_baking if it exists (so the data inside is not lost) TODO or actually remove it completely
       now = datetime.datetime.now()
       print 'The folder EM_baking existed already; renamed it as Saved_EM_baking_' + str(now.month)+':'+str(now.day)+':'+str(now.year)+'_'+str(now.hour)+':'+str(now.minute)
       shutil.move('results/EM_baking',  'results/Saved_EM_baking_' + str(now.month)+':'+str(now.day)+':'+str(now.year)+'_'+str(now.hour)+':'+str(now.minute) )
    os.system('./bin/CheckMATE CM_commands_file.txt < CM_answers.txt')

def CM_Output_Relocator(cmDir = '', CM_OutputDir = '' ):
    cmOutput_Path  = cmDir + '/results/EM_baking'  # contains the MA5 analyses output
    if (os.path.isdir(CM_OutputDir) ):                         # further check that the directory exists
       shutil.move(cmOutput_Path , CM_OutputDir+'/CM_Results')
    else: print "ERROR: %s does not exist, cannot relocate output"























