"""
.. module:: MA5_Output_parser.
        :synopsis: This module convert and parse the MA5 EM output (called CLs_output.saf)
                   into a SModelS friendly format (txt files with columns separated by blank spaces)

.. moduleauthor:: Federico Ambrogi <federico.ambrogi88@gmail.com>

"""

import os,sys
from Baker_Assistant import Folder_Creator
from analyses_info import *

# It is a list of dictionaries, one dic for each MA5 analysis included in the Pad.
# Each Dictionary contains two keys:  name of the analysis and a sub-dictionary { Ma5_name , Official_name + numbers of evenets needed for the Bkg, Obs event, Error } 
# This dictionary will be read by the Eff Map creator, and used to create the lines needed from the convert.py 
# I need to do this because we need a mapping between the SR names used in Ma5 and the official ones

# My idea is to give also as a txt output the lines that need to be included inside the convert.py for building the Eff.Map
# The user will have to copy and paste, I do not want to modify the convert.py itself,
# but at least it will save a lot of time finding the numbers and replacing the path to the EM file.
# These lines in fact depend only on the TxName, name of the SR, name of the file containing the produced map and the event-bkg-error numbers



'''
Saf_Input = 'CLs_output.saf'
Analyses = []

# Loop over the analyses:
for analysis in Analyses:
    for line in Lines[1:]:
           if analysis in line and (analysis == 'cms_sus_14_001_TopTag' ):
              
        
              print analysis # returns the name od the analysis as in Ma5 CLs output
'''         

'''
These two functions read the CLs_Input file from MA5; according to the analysis name,
they extract the correct EM value for the region specified.
It is meant to be used in a loop over all the regions from the MA5_Analyses_Dicts above.
The output are txt files containing the EM , for example ' Mother Interm   Daughter  Eff. ' 
'''

#FIXME it will be better to read the file only once and store the efficiencies
#FIXME no check on the error at the moment??
def EM_Value_Extractor(EM_output = '', analysis = '', region = '', ma5=True):
    if ma5: return EM_Value_Extractor_MA5(MA5_EM_OutputSaf = EM_output, analysis = analysis, region = region)
    return EM_Value_Extractor_CM(EM_output, analyisis, region)

def EM_Value_Extractor_MA5(MA5_EM_OutputSaf = '', analysis = '', region = ''):
    EM_Value = [] #FIXME why is this a list if only one value is returned, break loop with return s[5] instead of append?
    if (not os.path.exists(MA5_EM_OutputSaf)):
         print 'MA5 Efficiency Maps Output not found! Terminating Execution'
         sys.exit()        
     
    elif (os.path.exists(MA5_EM_OutputSaf)):        
       Lines = open(MA5_EM_OutputSaf,'r').readlines() 
       for line in Lines[1:]:
           if analysis in line and region in line:   # checks analysis and region
              s = [x for x in line.split('  ') if x != '']
              EM_Value.append(s[5])
    return EM_Value[0]

def EM_Value_Extractor_CM(EM_output='', analyisis='', region=''):
    effFile = EM_output+"/%s_eff_tab.txt" %analysis
    if (not os.path.exists(effFile)):
    	print 'CM Efficiency Maps Output not found in %s! Terminating Execution' %effFile
        sys.exit()
    for l in open(effFile):
        if "Signal_Region" in l: continue
        l = l.strip().split()
        if region == l[0]: return l[1]
    print "Signal region %s not found for %s." %(region, analysis)
    return None
           
  

def EM_Creator(ana_list = '', global_txNameDir = '' , slha_name= '', ma5=True, cm_data_dir=''): # general_OutDir contains all the different txNames folders
    if ma5: ana_dics_all = MA5_Analyses_Dicts
    else: ana_dicts_all = get_CM_Analyses_Dict(cm_data_dir) 
    txname = slha_name.split('_')[0]
    slha_split = slha_name.split('_')


    for analysis in ana_list:                        # looping over all the selected analyses
        analysis_EM_folder = global_txNameDir +'/'+txname+'_EfficiencyMaps/'+analysis+'_EM'
        if (not os.path.isdir(analysis_EM_folder) ): # this folder will contain the EM maps produced
           os.makedirs(analysis_EM_folder)

        for dic in ana_dics_all:                     # looping over all the analyses in the dictionary (should contain the info of the complete set of implemented MA5 analyses) 
            if dic['Name'] == analysis:              # matching the correct dictionary
               for SR_dic in dic['SR_Dict_List']:    # looping over all the SRs
                   if ma5: saf_file = global_txNameDir + '/' + slha_name + '/MA5_Analyses_Results/CLs_output.saf'
                   else: saf_file = global_txNameDir + '/' + slha_name + '/CM_Results/evaluation'  #FIXME call this as saf file now, but this is actually directory of eff maps, change name for ma5 and CM both ?
                   OutEM_Name = analysis_EM_folder+'/MA5_EM_'+SR_dic['Official_SR_Name']+'.dat'
                   if (not os.path.isdir(OutEM_Name) ):
                      
                      EM_Out   = open(OutEM_Name,'a+')
                      header = '#MA5 EffMap for txName: ' + txname + ' , Analysis: ' + analysis + ' , SR: ' + SR_dic['Official_SR_Name'] +'\n'
                      if (header not in EM_Out.readlines() ):
                         EM_Out.write('#MA5 EffMap for txName: ' + txname + ' , Analysis: ' + analysis + ' , SR: ' + SR_dic['Official_SR_Name'] +'\n' )
                      EM_Out.close()
                 

           	   if  (len(slha_split) == 4 ):      # Determine if it is a direct decay or 1 step cascade decay from the txName 
                       EM_Out = open(OutEM_Name,'a+')
                       if ( len(EM_Out.readlines() ) == 1):
                          EM_Out.write('# Mother Interm   Daughter  Eff. \n')                       
              	       mother_1 = (slha_split[1])
              	       interm_1 = (slha_split[2])
              	       daught_1 = (slha_split[3])
              	       Eff_Value = EM_Value_Extractor(EM_Output = saf_file , analysis = analysis, region = SR_dic['MA5_SR_Name'], ma5)
                       EM_Out.write(str(mother_1) + '   ' +str(interm_1) + '   ' + str(daught_1)+'   '+  str(Eff_Value) + '\n') 
                       EM_Out.close()

              	   elif (len(slha_split) == 3 ): 
                       EM_Out = open(OutEM_Name,'a+')
                       if ( len(EM_Out.readlines() ) == 1) :
                          EM_Out.write('# Mother  Daughter  Eff. \n')
              	       mother_1 = (slha_split[1])
              	       daught_1 = (slha_split[2])
              	       Eff_Value = EM_Value_Extractor(EM_Output = saf_file , analysis = analysis, region = SR_dic['MA5_SR_Name'], ma5 )
                       EM_Out.write(str(mother_1) + '   ' + str(daught_1)+'   '+  str(Eff_Value) + '\n')  
                       EM_Out.close()







