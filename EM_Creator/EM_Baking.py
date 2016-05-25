""":
.. module:: EM_Baking.
        :synopsis: This module loops over SLHA files and creates EM in a SModelS
                    friendly format

.. moduleauthor:: Federico Ambrogi <federico.ambrogi88@gmail.com>
"""


import argparse, datetime, sys, os , subprocess, pprint, shutil
from subprocess import call
from sys import stderr
from EM_Ingredients  		import *
from Baker_Assistant 		import *
from Cards_Producer  		import *
from shutil 			import *
from Softwares_Installator 	import *

#TODO Run as 'python EM_Baking.py '

print '\n***** EM_Baking: ready to produce Efficiency Maps ***** \n'
os.system("echo $HOSTNAME")

author = ''
while ( not author):
      author = raw_input('*** Please enter your name *** : ')

NoSLHAInput_Breaker(slhaDir = SLHA_InputDir)            # this simply breaks the run if no correct SLHA files are found inside the SLHA folder given 

Output_Folder = os.getcwd() + '/' + Output_Dir          # complete path of the output folder where all the results will be stored
Folder_Creator_Saver(out_dir = Output_Folder)           # creates the output folder given the name chosen by the user; if already existing the old one will be renamed 

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Software Installations
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
MG5_Dir , MA5_Dir = Install_MG5_MA5(MG5_tar, MA5_tar, install_switch = Installation_Switch )    # Install MG5+MA5 or use the local install; returns the softwares paths

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Starting MG5 Generation and Analysis
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

SLHA_List = SLHA_List_Creator(SLHA_InputDir)

# TODO : I will make it like runSmodels i.e. I want to externalize the loop on the slha from the whole chain
for slha in SLHA_List:

    SLHA_path = SLHA_InputDir + '/' + slha
    SLHA_name = slha.split('.slha')[0]
    TxName    = slha.split('_')[0]

    MG5_Process = MG5_detProcess(slha, extraISR = '0jet')       # this extracts the correct MG5 process from the txName TODO extraISR = '2jet' is the def option
    if (not NoFile_Continue(Home_Dir+'/Input/MG5_Process_Cards/'+MG5_Process+'.txt') ):   # checks if the MG5 proc card is present
       	print 'MAG Process Card not found! I will continue with next SLHA'
       	continue

    OutputFolder_TxName_dir = Output_Folder +'/'+ TxName
    Folder_Creator(out_dir = OutputFolder_TxName_dir)            # Create a folder for each Mg5 process inside the output folder just created

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Running MadGraph and Pythia
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# The files produced and stored int he folder run_01 will be moved inside the output folder
# For each Mg5 process there will be a folder inside the Output dir ;
# inside each process folder there will be a folder called as the SLHA file                          ----> 'OutputFolder_Mg5Process_SLHA_dir' 
# Inside each SLHA folder, there will be one folder containing the Mg5 output and the MA5 root file  ----> 'OutputFolder_Mg5Process_SLHA_Mg5Folder_dir'
    Run_MG5 (MG5Pythia_paramDic= MG5_Pythia_Params, slha_file= SLHA_path, MG5dir= MG5_Dir, templ_dir= Templates_Folder , proc = MG5_Process) 
    OutputFolder_TxName_SLHA_dir= OutputFolder_TxName_dir +'/'+SLHA_name           # Output folder for each differen SLHA
    MG5_Output_Relocator (mg5Out= MG5_Dir+'/'+MG5_Process+'/Events/run_01', MG5_OutputDir = OutputFolder_TxName_SLHA_dir  ) 

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Running MadAnalysis (Delphes + Analyzer)
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # NOTE this part is independent of MA5, also neede for Delphes
    input_HEP = OutputFolder_TxName_SLHA_dir+'/MG5Output/tag_1_pythia_events.hep.gz'             # Complete path of the HEP file inside the Output folder
    print input_HEP
    if ( not NoFile_Continue(input_HEP) ): 
       print 'The HEP file is missing! I will continue with the next SLHA'
       continue
#    if (not os.path.isfile(input_HEP) ):
#       print 'No HEP file found! Moving to next SLHA'
#       continue
    os.system("gunzip "+input_HEP) 
    input_HEP = OutputFolder_TxName_SLHA_dir+'/MG5Output/tag_1_pythia_events.hep'

    #FIXME now choose between MA5 and CheckMate (ideally run one after the other?)

    if ma5:
    	os.chdir(Home_Dir)
    	ReInstall_PAD(MA5_Dir)  

    	Run_MA5(ma5Dir = MA5_Dir, inputHEP = input_HEP)  
    	if (not NoFile_Continue(MA5_Dir + '/ANALYSIS_0') ): 
       		print 'MA5 Output not found! I will continue with next SLHA'
       		continue

    	MA5_Output_Relocator(ma5Dir = MA5_Dir, MA5_OutputDir = OutputFolder_TxName_SLHA_dir)

    else: # run CheckMate instead
    	# FIXME installation of checkmate?
        Run_CM(cmDir = CM_Dir, inputHEP=input_HEP)
        CM_Output_Relocator(cmDir = CM_Dir, CM_OutputDir = OutputFolder_TxName_SLHA_dir)


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creating Efficiency Maps
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------   
    #FIXME again, choose between MA5 and CM (do import outside the loop?)
    from MA5_Output_parser import * #FIXME maybe just call this Output_parser, use for MA5 and CM ?
    if ma5: Analyses_List = MA5_Analyses_List
    else: Analyses_List = CM_Analyses_List 
    EM_Creator(ana_list= Analyses_List, global_txNameDir= OutputFolder_TxName_dir, slha_name= SLHA_name, ma5 = ma5 , cm_data_dir=CM_Data  )

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Saving Intermediate Outputs
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------  
    PartialOutput_Saver(switch= Save_PartialOutput_Switch, outFolder= OutputFolder_TxName_SLHA_dir)

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Saving the EM_Ingredients and Production Parameters
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Info_Saver(author= author, outDir= Output_Folder )         # Saving a recap file








