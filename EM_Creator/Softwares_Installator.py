"""
.. module:: Softwares_Installators
        :synopsis: This module installs MG5(+Pythia) and MA5(+Delphes)

.. moduleauthor:: Federico Ambrogi <federico.ambrogi88@gmail.com>

"""


import os,sys
from shutil         import *
from EM_Ingredients import MA5_tar, MG5_tar, MG5_Dir, MA5_Dir, Home_Dir
from subprocess     import Popen, PIPE


'''
This utilies builds MG5 and MA5 by extracting the tools from the respective tarballs and making the relevant installations
mg5 and ma5 are the name of the respective tarballs i.e. MA5_tar = 'MadAnalysis5_v1.3.tar.gz' , MG5_tar = 'MG5_aMC_v2.3.3.tar'
'''
prog_dir     = 'Programs_Installation' 
folder_containing_tar = os.getcwd()+'/' + prog_dir  # TODO this will be fixed and hard-coded in the final version on the script

def Install_MA5(ma5):
    os.chdir(folder_containing_tar)
    os.system("tar -xf " + ma5)
    os.chdir(folder_containing_tar + '/madanalysis5')

    os.system('./bin/ma5 -s ../MA5_Install_delphesMA5tune.txt') 
    os.system('./bin/ma5 -s ../MA5_Install_PADForMA5tune.txt') 
    os.system('./bin/ma5 -s ../Test_MA5.txt > check.txt')
    check = open('check.txt','r')
    lines = check.readlines()
    res = []
    for line in lines:           
        if 'Delphes-MA5tune' in line and 'OK' in line:
            print 'MA5 tune correctly installed'
            res.append(line)
        else:
            continue
    if(len(res) == 0):  
       print 'MA5 installation unsuccesful! Please run again!'
    else: 
       return os.getcwd() 

def ReInstall_PAD(ma5_path):
    os.chdir(ma5_path)
    os.system('./bin/ma5 -s ../MA5_Install_PADForMA5tune.txt')

def Install_MG5(mg5): 
    os.chdir(folder_containing_tar)
    os.system("tar -xf " + mg5)
    mg5_home = folder_containing_tar + '/MG5_aMC_v2_3_3'
    os.chdir(mg5_home)
    copyfile(Home_Dir+'/Input/mg5_configuration.txt', mg5_home+'/input/mg5_configuration.txt') # to avoid annoying opening of the web browser
    copyfile(folder_containing_tar+'/pythia-pgs.tgz', mg5_home+'/pythia-pgs.tgz')
    os.system('tar -xf pythia-pgs.tgz')
    os.chdir('pythia-pgs/src')
    os.system('make')
    if (not os.path.exists(mg5_home +'/pythia-pgs') ):
       print 'MG5 pythia installation was unsuccesful! Please run again!'
       sys.exit()   
    os.chdir(mg5_home)
    return os.getcwd() 

'''
This function install MG5 and MA5 if the switch option is not set to OFF;
by default it is set to 'ON'
It returns the directory where the two installed softwares are located
It checks if the installations were succesfull
'''
def Install_MG5_MA5(mg5, ma5, install_switch = 'ON', mg5UserDir = MG5_Dir , ma5UserDir = MA5_Dir ):
    mg5_ma5_paths = []
    if (install_switch != 'OFF' or(not os.path.isdir(mg5UserDir) ) or (not os.path.isdir(ma5UserDir) )   ):
       print 'Proceeding with a new MG5 and MA5 installation'
       mg5_ma5_paths.append(Install_MG5(mg5))
       mg5_ma5_paths.append(Install_MA5(ma5))
       mg5_dir = mg5_ma5_paths[0]
       ma5_dir = mg5_ma5_paths[1]
       if (os.path.isdir(folder_containing_tar +'/MG5_aMC_v2_3_3') and os.path.isdir(folder_containing_tar +'/madanalysis5') ): # checks if the installation was correct
          return mg5_dir , ma5_dir
    else:
          return MG5_Dir , MA5_Dir


