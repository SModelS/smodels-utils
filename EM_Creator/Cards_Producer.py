"""
.. module:: Cards_Producer.
        :synopsis: This module produces the cards used as input by MG5 and MA5

.. moduleauthor:: Federico Ambrogi <federico.ambrogi88@gmail.com>
"""

from EM_Ingredients import *
import os, sys


'''
This module creates:
- the MG5 run card, from the template card and the MG5_parameters the dictionary of MG5 params&values that can be choosen (listed in the EM_Ingredients.py) 
If the parameter is not listed in the card, it gives a warning
- the MA5 (Delphes + Analyses) cards to run MadAnalysis5
- the MG5 and MA5 txt files containing the commands to launch the MG5 process
'''

def MG5_Pythia_cards_producer(MG5Pythia_paramDic = '', MG5dir = '', templ_dir='' , proc = ''):
    os.system('rm '+ MG5dir+'/'+proc+'/Cards/run_card.dat')            # remove previous run card
    mg5card_out      = open(MG5dir+'/'+proc+'/Cards/run_card.dat','w') # complete path of the Cards folder relative to this process name
    mg5card_template = open(templ_dir+'/template_run_card.dat','r')  	 # here it goes the path of the template cards, once it is fixed
    lines = mg5card_template.read()
    lines = lines.split('\n')
    for line in lines:
        for param in MG5Pythia_paramDic:
           if (param != 'qcut' and param != 'MG5_Processes'):
            if not any( param in line for line in lines):                  # checks that the parameters listed are valid ones i.e. contained in the template file
               print 'ERROR! The parameter ', param, 'is not a valid MG5 run_card.dat parameter! Re-Run!'
               sys.exit()   

            if param in line:
               print 'Subsituting the parameter ', param , MG5Pythia_paramDic[param] , 'in the MadGraph run card'
               line = line.replace(param, MG5Pythia_paramDic[param])
        mg5card_out.write(line+' \n')
    mg5card_out.close()

    os.system('rm '+ MG5dir+'/'+proc+'/Cards/pythia_card.dat')               # remove previous run card
    pythiacard_out      = open(MG5dir+'/'+proc+'/Cards/pythia_card.dat','w') # complete path of the Cards folder relative to this process name
    pythiacard_template = open(templ_dir+'/template_pythia_card.dat','r')  # here it goes the path of the template cards, once it is fixed
    lines = pythiacard_template.read()
    lines = lines.split('\n')
    for line in lines:
         if 'qcut' in line:
             print 'Subsituting the QCUT in the Pythia template card with',  MG5Pythia_paramDic['qcut']
             line = line.replace('qcut', MG5Pythia_paramDic['qcut'])
         pythiacard_out.write(line+' \n')
    pythiacard_out.close()

def MG5_commands_producer(process=''):
    MG5_comm = open('MG5_commands_file.txt','w')
    MG5_comm.write('launch '+ process+'\n')
    MG5_comm.write('pythia=ON\n')
    MG5_comm.write('madspin=OFF\n')
    MG5_comm.write('0\n')
    MG5_comm.write('0\n')
    return 'MG5_commands_file.txt'

def MA5_commands_producer(input_file='', MA5_path = ''):
    MG5_comm = open('MA5_commands_file.txt','w')
    MG5_comm.write('set main.recast = on\n')
    MG5_comm.write('set main.recast.card_path = '+ MA5_path+'/recasting_card.dat\n')    
    MG5_comm.write('import '+input_file+'\n')
    MG5_comm.write('submit'+'\n')
    return 'MA5_commands_file.txt'

def CM_commands_producer(input_file='', xsec, err):
    #xsec and err should be given in PB
    CM_comm = open("CM_commands_file.txt",'w')
    CM_comm.write("[Mandatory Parameters]\n")
    CM_comm.write("Name: EM_baking\n")
    CM_comm.write("Analyses: atlas\n")
    CM_comm.write("[Optional Parameters]\n")
    CM_comm.write("eff_tab = True\n")
    CM_comm.write("TempMode = True\n")
    CM_comm.write("[evts]\n")
    CM_comm.write("XSect: %s*PB\n" %str(xsec))
    CM_comm.write("XSectErr: %s*PB\n" %str(err))
    CM_comm.write("Events: %s" %input_file)
    return 'CM_commands_file.txt'

def CM_answer_producer():
  CM_answers = open('CM_answers.txt','w')
  CM_answers.write("y\n")
  return 'CM_answers.txt'
























