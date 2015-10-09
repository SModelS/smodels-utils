#!/usr/bin/env python

"""
.. module:: convert
   :synopsis: used to create info.txt, txname.txt, twiki.txt and sms.py.

.. moduleauthor: Wolfgang Waltenberger

"""
import sys
import os
import argparse
import types

argparser = argparse.ArgumentParser(description = \
'create info.txt, txname.txt, twiki.txt and sms.py')
argparser.add_argument ('-utilsPath', '--utilsPath', \
help = 'path to the package smodels_utils',\
type = types.StringType)
args = argparser.parse_args()

if args.utilsPath:
    utilsPath = args.utilsPath
else:
    databaseRoot = '../../../'
    sys.path.append(os.path.abspath(databaseRoot))
    from utilsPath import utilsPath
    utilsPath = databaseRoot + utilsPath

sys.path.append(os.path.abspath(utilsPath))
from smodels_utils.dataPreparation.inputObjects import TxNameInput, MetaInfoInput
from smodels_utils.dataPreparation.databaseCreation import databaseCreator
from smodels_utils.dataPreparation.origPlotObjects import x, y


#+++++++ global info block ++++++++++++++

import os, glob
dir=os.getcwd()                                                                                                                 
expid=dir.replace("-eff","")                                                                                                    
pos=expid.find("ATLAS/")                                                                                                        
expid=expid[pos+6:] 

info = MetaInfoInput(expid)
info.url ='https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/CONFNOTES/%s/' % expid 
info.sqrts = 8
info.lumi = @@@LUMI@@@
info.prettyname = ''
info.private = True
info.arxiv = ''
info.contact ='fastlim'
info.publication = ''
info.comment = 'created from fastlim-1.0'
info.superseded_by = ''
info.implemented_by = ''

databaseCreator.create()
