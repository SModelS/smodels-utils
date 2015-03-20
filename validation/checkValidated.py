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
not_checked = []
for expRes in database.getExpResults(datasetIDs=[None]):
    for txname in expRes.getTxNames():
        if 'assigned' in txname.getInfo('constraint'): continue
        if txname.getInfo('validated') is True: validated.append([txname,expRes])  
        elif txname.getInfo('validated') is False: not_validated.append([txname,expRes])
        elif txname.getInfo('validated') is None: not_checked.append([txname,expRes])
        else: print "Unknown field %s",txname.getInfo('validated')
        

check = validated + not_validated + not_checked
ans = raw_input("Open plots? (y/n) \n")
if ans.lower() == 'y':
    showPlots = True
    ans2 = raw_input("Check: \n (a) all plots \n (b) not checked and not validated\
     \n (c) not checked \n (d) not validated \n (e) validated \n")
    if ans2.lower() == 'a': check = validated + not_validated + not_checked
    elif ans2.lower() == 'b': check = not_validated + not_checked
    elif ans2.lower() == 'c': check = not_checked
    elif ans2.lower() == 'd': check = not_validated
    elif ans2.lower() == 'e': check = validated
else: showPlots = False


print '# Validated Txnames =',len(validated)

print '# Not Validated Txnames =',len(not_validated)

print '# Not Checked Txnames =',len(not_checked)

miss_plots = []
for txname,expRes in check:    
    print expRes.getValuesFor('id'),txname.txname    
    expDir = expRes.path
    valDir = os.path.join(expDir,'validation')
    #Check the plots
    plots = []    
    for fig in glob.glob(valDir+"/"+txname.txname+"_*.pdf"):
        if showPlots: plots.append(subprocess.Popen(['evince','--preview',fig]))
        else: plots.append(fig)
    if glob.glob(valDir+"/"+txname.txname+"_*.comment"):
        print '== Comment file found =='
    axes = txname.getInfo('axes')
    if not isinstance(axes,list): axes = [axes]
    print '***',len(plots),'PLOT(S) FOUND for %i axes***' %len(axes)
    if len(axes) != len(plots) and plots: print '------>',len(axes)-len(plots),'plot(s) missing'
    if not plots:
        miss_plots.append([txname,expRes])
        continue      
    if showPlots:      
        val = raw_input("TxName is validated? (y/n/i) \n")
        if val.lower() == 'y': validated = True
        elif val.lower() == 'n': validated = False
        else: validated = None
        #Rewrite txname.txt file with validation result
        txfile = txname.getInfo('txnameFile')
        tf = open(txfile,'r')
        tdata = ""
        for l in tf.readlines():
            if 'validated:' in l:
                l = 'validated: '+str(validated)+'\n'
            tdata += l
        tf.close()
        tf = open(txfile,'w')
        tf.write(tdata)
        tf.close()
        for plot in plots:
            plot.terminate()
            plot.kill()

if miss_plots:        
    print '\n\n MISSING PLOTS FOR:'
    for txname,expRes in miss_plots: print expRes.getValuesFor('id'),txname.txname    

    