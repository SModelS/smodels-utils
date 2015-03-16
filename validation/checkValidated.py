#!/usr/bin/env python

import sys,os
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))

from smodels.experiment.databaseObjects import DataBase
import subprocess
import glob

database = DataBase(os.path.join(os.path.expanduser("~"),"smodels-database/"))

validated = []
not_validated = []
for expRes in database.getExpResults(datasetIDs=[None]):
    for txname in expRes.getTxNames():
        if 'assigned' in txname.getInfo('constraint'): continue
        if txname.getInfo('validated'): validated.append([txname,expRes])  
        else: not_validated.append([txname,expRes])

ans = raw_input("Open plots? (y/n) \n")
if ans.lower() == 'y':
    showPlots = True
    ans2 = raw_input("Check only not validated plots? (y/n) \n")
    if ans2.lower() == 'y': check = not_validated
    else:  check = validated + not_validated 
else: showPlots = False


print '# Validated Txnames =',len(validated)

print '# Not Validated Txnames =',len(not_validated)

for txname,expRes in check:    
    print expRes.getValuesFor('id'),txname.txname    
    expDir = expRes.path
    valDir = os.path.join(expDir,'validation')
    #Check the plots
    if showPlots:
        plots = []    
        for fig in glob.glob(valDir+"/"+txname.txname+"*.png"):
            plots.append(subprocess.Popen(['eog',fig]))
        print '***',len(plots),'PLOT(S) FOUND***'
        if not plots: continue        
        val = raw_input("TxName is validated? (y/n) \n")
        if val.lower() == 'y': validated = True
        else: validated = False
        #Rewrite txname.txt file with validation result
        txfile = txname.getInfo('txnameFile')
        tf = open(txfile,'r')
        tdata = ""
        for l in tf.readlines():
            if 'validated:' in l:
                l = 'validated: '+str(validated)+'\n'
            tdata += l
        tf.close()
#         tf = open(txfile,'w')
#         tf.write(tdata)
#         tf.close()
        for plot in plots:
            plot.terminate()
            plot.kill()
        
    

    