import os,sys
'''
This Module contains all the Input Parameters that are used by MadGraph5+Pythia and MadAnalysis5+Delphes
'''

Home_Dir = os.getcwd()


Output_Dir = 'Output_T2bb'      

SLHA_InputDir   	  = Home_Dir + '/Input/slha' # TODO this can also be hard coded directly in the functions once we fix the structure of the script/folder 
Templates_Folder 	  = Home_Dir + '/Input/' 
Save_PartialOutput_Switch = 'OFF' # set to 'OFF' if you don't want to save the partial Output files

ma5 = False # set False to run checkmate instead, FIXME change code to run both..

Installation_Switch = 'OFF'   #Select if MG5 and MA5 will be installed; If OFF, select the paths and versions of your installations. Otherwise, it will proceed to the installation
'''
MadAnalysis5 and MadGraph tarballs if installation is set to ON 
'''
MA5_tar      = 'ma5_v1.4beta.tar'
MG5_tar      = 'MG5_aMC_v2.3.3.tar'
		       
'''
MadAnalysis5 and MadGraph dir and versions if the installation is set to OFF 
'''
MG5_Dir         = '/theo/uschi/MG5_aMC_v2_2_3'                  # Absolute path of the directory where MG5 is installed (user's local configuration)
MG5_Version     = 'v2_2_3'
Pythia_Version  = 'Pythia6'           # pythia-pgs version included in the standard Mg5 installation 

MA5_Dir		= '/theo/uschi/madanalysis5'                  # Absolute path of the directory where MA5 is located (user's local configuration)
MA5_Version     = '1.1.11'

CM_Dir          = '/theo/uschi/CheckMATE-1.2.2'
CM_Version      = '1.2.2'
CM_Data         = CM_Dir+'/data' # this is where information about Obs, Bkg events is stored

'''
MA5 Input Parameters
'''
MA5_Analyses_List = ['cms_sus_14_001_TopTag','atlas_susy_2013_21','cms_sus_13_016'] # TODO it will be used to create the recasting card in MA5 (when it works...)

'''
CheckMATE Input Parameters
'''
CM_Analyses_List = ['atlas_conf_2013_024', 'atlas_conf_2013_049'] # TODO now hard coded to run over all available atlas analyses, this is list of results to be extracted
#FIXME there should be a switch to run over atlas or cms analyses, mabye also both (requires running twice because of delphes settings)
#FIXME maybe this should not used at all, instead could provide option here to choose either cms or atlas analyses

'''
MadGraph5 Pythia Input Parameters
'''                                                      
MG5_Pythia_Params		= { 'EBEAM'   	 		: '4000' 		, # Single Beam Energy expressed in GeV
                                    'NEVENTS'	   		: '10000'		,			 
			   	    'MAXJETFLAVOR' 		: '5'			,
                                    'PDFLABEL'     		: 'cteq6l1'		,
                                    'XQCUT'        		: '50'			, 
				    'qcut'         		: '90' }
