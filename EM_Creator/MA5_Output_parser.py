"""
.. module:: MA5_Output_parser.
        :synopsis: This module convert and parse the MA5 EM output (called CLs_output.saf)
                   into a SModelS friendly format (txt files with columns separated by blank spaces)

.. moduleauthor:: Federico Ambrogi <federico.ambrogi88@gmail.com>

"""

import os,sys
from Baker_Assistant import Folder_Creator


# It is a list of dictionaries, one dic for each MA5 analysis included in the Pad.
# Each Dictionary contains two keys:  name of the analysis and a sub-dictionary { Ma5_name , Official_name + numbers of evenets needed for the Bkg, Obs event, Error } 
# This dictionary will be read by the Eff Map creator, and used to create the lines needed from the convert.py 
# I need to do this because we need a mapping between the SR names used in Ma5 and the official ones

# My idea is to give also as a txt output the lines that need to be included inside the convert.py for building the Eff.Map
# The user will have to copy and paste, I do not want to modify the convert.py itself,
# but at least it will save a lot of time finding the numbers and replacing the path to the EM file.
# These lines in fact depend only on the TxName, name of the SR, name of the file containing the produced map and the event-bkg-error numbers
MA5_Analyses_Dicts = [
{'Name'        : 'cms_sus_14_001_TopTag' , 
 'SR_Dict_List' : [ { 'MA5_SR_Name' : 'MET200-350__Nbjets=1' ,          'Official_SR_Name' : 'Official_region1' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MET>350__Nbjets=1' ,             'Official_SR_Name' : 'Official_region2' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },                                           
                    { 'MA5_SR_Name' : 'MET200-350__Nbjets>1' ,          'Official_SR_Name' : 'Official_region3' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MET>350__Nbjets>1' ,             'Official_SR_Name' : 'Official_region4' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 }   
               ] 
},

{'Name'        : 'atlas_susy_2013_21' , 
 'SR_Dict_List' : [ { 'MA5_SR_Name' : 'M1' ,                           'Official_SR_Name' : 'Official_region1' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'M2' ,           		       'Official_SR_Name' : 'Official_region2' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },                                           
                    { 'MA5_SR_Name' : 'M3' ,           		       'Official_SR_Name' : 'Official_region3' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },  
               ] 
},

{'Name'        : 'cms_sus_13_016' , 
 'SR_Dict_List' : [ { 'MA5_SR_Name' : 'Gluino_to_TT_neutralino' ,      'Official_SR_Name' : 'Official_region1' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 }, 
               ] 
},


# TODO the above numbers are not real, only the ones for these following two analyses are correct


{'Name'        : 'atlas_sus_13_05' , 
 'SR_Dict_List' : [ { 'MA5_SR_Name' : 'SRA, HighDeltaM, MET > 150, MCT > 150' ,      'Official_SR_Name' : 'SRA-mCT150' , 'Obs': 102 , 'Bkg': 94 ,   'Err': 13 }, 
                    { 'MA5_SR_Name' : 'SRA, HighDeltaM, MET > 150, MCT > 200' ,      'Official_SR_Name' : 'SRA-mCT200' , 'Obs': 48  , 'Bkg': 39 ,   'Err': 6 }, 
                    { 'MA5_SR_Name' : 'SRA, HighDeltaM, MET > 150, MCT > 250' ,      'Official_SR_Name' : 'SRA-mCT250' , 'Obs': 14  , 'Bkg': 15.8 , 'Err': 2.8 }, 
                    { 'MA5_SR_Name' : 'SRA, HighDeltaM, MET > 150, MCT > 300' ,      'Official_SR_Name' : 'SRA-mCT300' , 'Obs': 7   , 'Bkg': 5.9 ,  'Err': 1.1 }, 
                    { 'MA5_SR_Name' : 'SRA, HighDeltaM, MET > 150, MCT > 350' ,      'Official_SR_Name' : 'SRA-mCT350' , 'Obs': 3   , 'Bkg': 2.5  , 'Err': 0.6 }, 
                    { 'MA5_SR_Name' : 'SRB, LowDeltaM, MET > 250'             ,      'Official_SR_Name' : 'SRB'         , 'Obs': 65  , 'Bkg': 64   , 'Err': 10 }, 

               ] 
},

{'Name'        : 'atlas_susy_2013_11' ,
 'SR_Dict_List' : [ { 'MA5_SR_Name' : 'MT2-90 ee;MT2-90 mumu' ,         'Official_SR_Name' : 'mT2-90-SF'      , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MT2-90 emu' ,                    'Official_SR_Name' : 'mT2-90-DF'      , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MT2-120 ee;MT2-120 mumu' ,       'Official_SR_Name' : 'mT2-120-SF'    , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MT2-120 emu' ,                   'Official_SR_Name' : 'mT2-120-DF'    , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MT2-150 ee;MT2-150 mumu' ,       'Official_SR_Name' : 'mT2-150-SF'    , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MT2-150 emu' ,                   'Official_SR_Name' : 'mT2-150-DF'     , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWa ee;WWa mumu' ,               'Official_SR_Name' : 'WWa-SF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWa emu' ,                       'Official_SR_Name' : 'WWa-DF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWb ee;WWb mumu' ,               'Official_SR_Name' : 'WWb-SF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWb emu' ,                       'Official_SR_Name' : 'WWb-DF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWc ee;WWc mumu' ,               'Official_SR_Name' : 'WWc-SF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWc emu' ,                       'Official_SR_Name' : 'WWc-DF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'Zjets ee;Zjets mumu' ,           'Official_SR_Name' : 'Zjets'          , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 }
                   
                   ]
                      },

]


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
def EM_Value_Extractor(MA5_EM_OutputSaf = '', analysis = '', region = ''):
    EM_Value = []
    if (not os.path.exists(MA5_EM_OutputSaf)):
         print 'MA5 Efficiency Maps Output not found! Terminating Execution'
         sys.exit()        
     
    elif (os.path.exists(MA5_EM_OutputSaf)):        
       Lines = open(MA5_EM_OutputSaf,'r').readlines() 
       for line in Lines[1:]:
           if analysis in line and region in line:   # checks analysis and region
              split = [x for x in line.split('  ') if x != '']
              EM_Value.append(split[5])

    return EM_Value[0]
  

def EM_Creator(ana_list = '', ana_dics_all = MA5_Analyses_Dicts , global_txNameDir = '' , slha_name= ''): # general_OutDir contains all the different txNames folders
    txname = slha_name.split('_')[0]
    slha_split = slha_name.split('_')

    for analysis in ana_list:                        # looping over all the selected analyses
        analysis_EM_folder = global_txNameDir +'/'+txname+'_EfficiencyMaps/'+analysis+'_EM'
        if (not os.path.isdir(analysis_EM_folder) ): # this folder will contain the EM maps produced
           os.makedirs(analysis_EM_folder)

        for dic in ana_dics_all:                     # looping over all the analyses in the dictionary (should contain the info of the complete set of implemented MA5 analyses) 
            if dic['Name'] == analysis:              # matching the correct dictionary
               for SR_dic in dic['SR_Dict_List']:    # looping over all the SRs
                   saf_file = global_txNameDir + '/' + slha_name + '/MA5_Analyses_Results/CLs_output.saf'
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
              	       Eff_Value = EM_Value_Extractor(MA5_EM_OutputSaf = saf_file , analysis = analysis, region = SR_dic['MA5_SR_Name'] )
                       EM_Out.write(str(mother_1) + '   ' +str(interm_1) + '   ' + str(daught_1)+'   '+  str(Eff_Value) + '\n') 
                       EM_Out.close()

              	   elif (len(slha_split) == 3 ): 
                       EM_Out = open(OutEM_Name,'a+')
                       if ( len(EM_Out.readlines() ) == 1) :
                          EM_Out.write('# Mother  Daughter  Eff. \n')
              	       mother_1 = (slha_split[1])
              	       daught_1 = (slha_split[2])
              	       Eff_Value = EM_Value_Extractor(MA5_EM_OutputSaf = saf_file , analysis = analysis, region = SR_dic['MA5_SR_Name'] )
                       EM_Out.write(str(mother_1) + '   ' + str(daught_1)+'   '+  str(Eff_Value) + '\n')  
                       EM_Out.close()








