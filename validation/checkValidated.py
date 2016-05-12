#!/usr/bin/env python

import sys,os
#Local smodels and database paths:
smodelsPath = '/home/lessa/smodels/'
databasePath = '/home/lessa/smodels-database/'
sys.path.append(smodelsPath)

from smodels.experiment.databaseObj import Database
import subprocess
import glob

database = Database(databasePath, force_load = 'txt')
expResList = sorted(database.getExpResults(), key=lambda exp: exp.globalInfo.id)

validated = []
not_validated = []
not_checked = []
for expRes in database.getExpResults(datasetIDs=[None]):
    txnamesList = sorted(expRes.getTxNames(), key=lambda tx: tx.txName)
    for txname in txnamesList:
#         if 'assigned' in txname.getInfo('constraint'): continue        
        if txname.validated is True: validated.append([txname,expRes])  
        elif txname.validated is False: not_validated.append([txname,expRes])
        elif txname.validated is None: not_checked.append([txname,expRes])
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
    print expRes.getValuesFor('id'),txname.txName    
    expDir = expRes.path
    valDir = os.path.join(expDir,'validation')
    #Check the plots
    plots = []    
    for fig in glob.glob(valDir+"/"+txname.txName+"_*.pdf"):
        if showPlots:
            try:
                plots.append(subprocess.Popen(['evince','--preview',fig]))
            except:
                plots.append(subprocess.Popen(['open',fig]))                
        else: plots.append(fig)
    if glob.glob(valDir+"/"+txname.txName+".comment"):
        print '== Comment file found: =='
        for cfile in glob.glob(valDir+"/"+txname.txName+"*comment"):
            cf = open(cfile,'r')
            print cf.read()
            cf.close()
    axes = txname.getInfo('axes')
    if not isinstance(axes,list): axes = [axes]
    print '***',len(plots),'PLOT(S) FOUND for %i axes***' %len(axes)
    if len(axes) != len(plots) and plots: print '------>',len(axes)-len(plots),'plot(s) missing'
    if not plots:
        miss_plots.append([txname,expRes])
        continue      
    if showPlots: 
        val = raw_input("TxName is validated? \n Yes/No/None/Skip (y/n/i/s) \n")
        if val.lower() == 'y': validated = True
        elif val.lower() == 'n': validated = False
        else: validated = None
        for plot in plots:
            plot.terminate()
            plot.kill()        
        
        if val.lower() == 's': continue
        #Rewrite txname.txt file with validation result
        txfile = txname.getInfo('txnameFile')
        if not os.path.isfile(txfile):
            print '\n\n ******\n ERROR: %s NOT FOUND!!! \n**** \n\n' %(txfile)
            continue
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


if miss_plots:        
    print '\n\n MISSING PLOTS FOR:'
    for txname,expRes in miss_plots: print expRes.getValuesFor('id'),txname.txName    

    
