#!/usr/bin/env python3

"""
.. module:: convert.py
   :synopsis: used to create info.txt and the <txname>.txt files.

"""
import sys
import os
import argparse

argparser = argparse.ArgumentParser(description =
    'create info.txt, txname.txt, twiki.txt and sms.py')
argparser.add_argument ('-utilsPath', '--utilsPath',
    help = 'path to the package smodels_utils',\
    type = str)
argparser.add_argument ('-smodelsPath', '--smodelsPath',
    help = 'path to the package smodels_utils',\
    type = str)
argparser.add_argument ('-no', '--noUpdate',
    help = 'do not update the lastUpdate field.',\
    action= "store_true" )
argparser.add_argument ('-t', '--ntoys',
    help = 'number of toys to throw [100000]',\
    type = int, default=200000  )
args = argparser.parse_args()

if args.noUpdate:
    os.environ["SMODELS_NOUPDATE"]="1"

if args.utilsPath:
    utilsPath = args.utilsPath
else:
    databaseRoot = '../../../'
    sys.path.append(os.path.abspath(databaseRoot))
    from utilsPath import utilsPath
    utilsPath = databaseRoot + utilsPath
if args.smodelsPath:
    sys.path.append(os.path.abspath(args.smodelsPath))

sys.path.append(os.path.abspath(utilsPath))
from smodels_utils.dataPreparation.inputObjects import MetaInfoInput,DataSetInput
from smodels_utils.dataPreparation.databaseCreation import databaseCreator
from smodels_utils.dataPreparation.massPlaneObjects import x, y, z

DataSetInput.ntoys = args.ntoys

#+++++++ global info block ++++++++++++++
info = MetaInfoInput('ATLAS-SUSY-2013-02')
info.comment = 'The recast maps	have only 10 out of 15 SRs, ATLAS official have 15. So for the recast T2,T5,TGQ we have 5 less SR wrt the official T1.We recast the T2 to cover the compressed squark-LSP region'
info.sqrts = '8.0'
info.private = False
info.lumi = '20.3'
info.publication = 'http://link.springer.com/article/10.1007/JHEP09%282014%29176'
info.url = 'https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/SUSY-2013-02/'
info.arxiv = 'http://arxiv.org/abs/1405.7875'
info.prettyName =  "jets and met"
info.supersedes = 'ATLAS-CONF-2013-047'




### T1: official maps from ATLAS (they provide 15 SRs , but in the recast (MA5) we have only 10 )

#+++++++ dataset block ++++++++++++++
dataset = DataSetInput("SR6jm")
dataset.setInfo(dataType = 'efficiencyMap', dataId = "SR6jm", observedN = 39, expectedBG = 33 , bgError = 6, upperLimit = '1.1173E+00*fb', expectedUpperLimit = '8.6116E-01*fb')

def add ( dataset ):

    dataset_n = dataset._name.replace('SR','').replace('6jt+','6jtp').replace('4jl-','4jlm')

    #### T2
    T2 = dataset.addTxName('T2')
    T2.checked =''
    T2.constraint ="[[['jet']],[['jet']]]"
    T2.conditionDescription ="None"
    T2.condition ="None"
    T2.source = 'SModelS'
    #+++++++ next mass plane block ++++++++++++++
    t2FigureUrls = { "6jt": "28b", "6jl": "26b", "3j": "19b", "4jl": "22b", "4jt": "24b", "5j": "25b", "4jlm": "23b", "2jm": "16b", "2jt": "17b" }
    T2qq = T2.addMassPlane([[x,y]]*2)
    T2qq.figure    = None
    if dataset_n in t2FigureUrls.keys():
        T2qq.figureUrl = "https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/SUSY-2013-02/figaux_%s.png" % t2FigureUrls[dataset_n]
    T2qq.dataUrl   = None
    T2qq.addSource('obsExclusion',"orig/exclusion_T2.txt", "txt")
    #T2qq.addSource('efficiencyMap',"orig/T2/MA5_EM_T2_Results_%s.dat"% dataset_n, "txt" , objectName ="None", index = None)
    T2qq.addSource('efficiencyMap',"orig/T2.embaked", "embaked" , objectName = dataset_n, index = None)

# commented SRs do not have the recast implementation so they are skipped

datasets = { "SR6jl" : ( 121,111 ,11 , '1.9230E+00*fb', '1.5312E+00*fb'),
             #"SR6jm": (39,36,3      , upperLimit = '1.1173E+00*fb', expectedUpperLimit = '8.6116E-01*fb'),
             #"SR2jW": ( 0 , 2.3 , 1.4 , upperLimit = '1.4709E-01*fb', expectedUpperLimit = '2.5070E-01*fb'),
             #"SR4jW": (14 , 14 , 4 , upperLimit = '6.7961E-01*fb', expectedUpperLimit = '5.9339E-01*fb'),
             #"SR2jl" : (12315 , 13000 , 1000 , upperLimit = '7.7800E+01*fb', expectedUpperLimit = '9.7112E+01*fb'),
             "SR6jtp": (6 , 4.9 , 1.6 , '3.9922E-01*fb', '3.0218E-01*fb'),
             "SR2jt" : (133, 125 , 10, '1.8181E+00*fb',   '1.5124E+00*fb'),
             "SR5j"  : (121, 126, 13 , '1.5429E+00*fb',   '1.7138E+00*fb'),
             "SR4jt" : (0, 2.5, 1.0 , '1.4949E-01*fb',    '2.4033E-01*fb'),
             "SR2jm" : (715,760,50, '4.2419E+00*fb',      '5.5524E+00*fb'),
             "SR4jlm": (2169, 2120, 110, '1.3292E+01*fb', '1.1561E+01*fb'),
             "SR4jl" : (608 , 630, 50, '4.7487E+00*fb',   '5.4345E+00*fb'),
             #"SR4jm" : (24, 37, 6 , upperLimit = '5.0301E-01*fb', expectedUpperLimit = '8.8617E-01*fb'),
             "SR3j": (7 , 5 , 1.2 ,  '4.3344E-01*fb', '3.3172E-01*fb'),
             "SR6jt": (5 , 5.2 , 1.4 , '3.3159E-01*fb', '3.3330E-01*fb')

             }

dses = {}

for name, numbers in datasets.items():
    #+++++++ dataset block ++++++++++++++
    dataset = DataSetInput( name )
    dses[name] = dataset
    name = name.replace('SR_','')
    dataset.setInfo(dataType = 'efficiencyMap', dataId = name,
                    observedN = numbers[0], expectedBG = numbers[1], bgError = numbers[2],
                    upperLimit = numbers[3] , expectedUpperLimit = numbers[4] )
    add ( dataset )

databaseCreator.create()
