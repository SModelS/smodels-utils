#!/usr/bin/evn python
"""
.. module::runplotter
     :synopsis:
     :required modules: 
"""

from plotter import *
import os,sys, ROOT
from ROOT import gROOT
import numpy as np

sys.path.append(os.path.join('/home/abassel/smodels'))
sys.path.append(os.path.join('/home/abassel/smodels-utils'))
from smodels.experiment.databaseObj import Database, ExpResult
#from smodels.tools.physicsUnits import fb, pb, GeV
#from smodels_utils.helper.txDecays import TxDecay # TODO

db = Database('/home/abassel/smodels-database')

####TEST####
Analysis = ['ATLAS-SUSY-2013-11']
txName = ['TSlepSlep']
titlename = ['TEST']
###########

listOfExpRes = db.getExpResults(analysisIDs=Analysis, txnames=txName, dataTypes = ['all'])

ExpRes = listOfExpRes[0]

orig_path = ExpRes.path + '/' + 'orig'

txnameData = ExpRes.getValuesFor('txnameData')[0]

Data = txnameData._data

max_mothermass, min_mothermass, max_daughtermass, min_daughtermass, list_mother_mass, list_daughter_mass = get_masses(Data)

from functionspackage import get_binning
mother_binning = get_binning(list_mother_mass)
daughter_binning = get_binning(list_daughter_mass)

from functionspackage import get_th2f_par
nbinsx, min_mothermass, max_mothermass, nbinsy, min_daughtermass, max_daughtermass = get_th2f_par(max_mothermass, min_mothermass, max_daughtermass, min_daughtermass, mother_binning, daughter_binning)

all_eff, nonz_eff = ext_eff(ExpRes, txName, mp=[min_mothermass, max_mothermass, mother_binning+1], dp=[min_daughtermass, max_daughtermass, daughter_binning+1])

low_lim, up_lim = set_palette_lim(nonz_eff)

canvas, pad, leg = set_canvas()

mymap = call_histo([[nbinsx, min_mothermass, max_mothermass], list_mother_mass], [[nbinsy, min_daughtermass, max_daughtermass], list_daughter_mass], all_eff)

set_style()

set_histo(mymap, [max_mothermass, max_daughtermass], [min_mothermass, min_daughtermass], [low_lim, up_lim], title='title in set_histo')

set_exline(orig_path)

set_text()

save_map(canvas)
'''
#print listOfExpRes
#myRes = listOfExpRes[0]
#print 'myRes is', myRes
#myTx = myRes.getTxnameWith({'txName':txName[0]})
#print 'myTx is', myTx
for ExpRes in listOfExpRes:
    #print ExpRes
    #Tx = ExpRes.getTxnameWith({'txName':txName[0]})
    #Tx = ExpRes.getTxnameWith({'txName':txName[0]})
    #listTxNames = ExpRes.getTxNames()
    #for TxName in listTxNames:
    #Tx=TxName.txName
    #print Tx
    #input()
    #Eff = Tx.getEfficiencyFor(Mass_Point[0])
    orig_path = ExpRes.path + '/' + 'orig'
    listtxnameData = ExpRes.getValuesFor('txnameData')
    for txnameData in listtxnameData:
        Data = txnameData._data
	#print Data
        max_mothermass, min_mothermass, max_daughtermass, min_daughtermass, list_mother_mass, list_daughter_mass = get_masses(Data)
	mother_binning = get_binning(list_mother_mass)
#	print mother_binning
	daughter_binning = get_binning(list_daughter_mass)
#	print daughter_binning
        nbinsx, min_mothermass, max_mothermass, nbinsy, min_daughtermass, max_daughtermass = get_th2f_par(max_mothermass, min_mothermass, max_daughtermass, min_daughtermass, mother_binning, daughter_binning)
        all_eff, nonz_eff = ext_eff(ExpRes, txName, mp=[min_mothermass, max_mothermass, mother_binning+1], dp=[min_daughtermass, max_daughtermass, daughter_binning+1])
 #       low_lim, up_lim = set_palette_lim(nonz_eff)
  #      canvas, pad, leg = set_canvas()
   #     mymap = call_histo([[nbinsx, min_mothermass, max_mothermass], list_mother_mass], [[nbinsy, min_daughtermass, max_daughtermass], list_daughter_mass], all_eff)
    #    set_style()
     #   set_histo(mymap, [max_mothermass, max_daughtermass], [min_mothermass, min_daughtermass], [low_lim, up_lim], title='title in set_histo')
      #  set_exline(orig_path)
       # set_text()
        #save_map(canvas)
'''
