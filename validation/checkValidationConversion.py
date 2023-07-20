#!/usr/bin/env python

"""
.. module:: checkValidationConversion
   :synopsis: Compares the validation/T*.py files between
              an old format folder and a new format folder.

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys,os,glob,time
sys.path.append('/home/lessa/smodels-utils')
sys.path.append('/home/lessa/smodels')
from smodels.base.physicsUnits import fb,pb,GeV,TeV
import logging
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)


def checkValue(value,oldValue,reps):
    
    if oldValue == value:
        return True
    
    if type(oldValue) != type(value):        
        return False
    
    if isinstance(value,str):
        if value.strip() != oldValue.strip():
            logger.error('New value = %s \nOld value = %s' %(value,oldValue))
            return False
    elif isinstance(value,list):
        value = sorted(value)
        oldValue = sorted(oldValue)
        if len(value) != len(oldValue):
            logger.error('\nNew value length = %i \nOld value length = %i' %(len(value),len(oldValue)))
            return False
        for i,v in enumerate(value):
            c = checkValue(v,oldValue[i],reps)
            if not c:
                if len(oldValue) < 4:
                    logger.error("Old: %s \nNew: %s" %(oldValue,value))
                return False
    elif isinstance(value,dict):
        if sorted(value.keys()) != sorted(oldValue.keys()):
            logger.error('\nNew value keys = %s \nOld value keys = %s' %(value.keys(),oldValue.keys()))
            return False
        for k,v in value.items():
            if k == 'CLs':
                continue
            c = checkValue(v,oldValue[k],reps)
            if not c:
                logger.error("Difference in %s\nOld: %s \nNew: %s" %(k,oldValue,value))
                return False
    else:
        vdiff = abs(value-oldValue)/(abs(value+oldValue))
        if vdiff > reps:
            logger.error('New value = %s \nOld value = %s' %(value,oldValue))
            return False                
    
    return True

def checkNewOutput(new,old):
    """
    Check the files in the new folder and the old folder.
    If setValidated = True and both folders are equal, replace the
    validation field in the new folder to the same one in the old folder.
    
    :param new: full path to the new experimental result validation folder
    :param old: full path to the corresponding old experimental result validation folder
    
    :return: True if both folders are equivalent, False otherwise.
    """
    
    #Check number of plots:
    if len(glob.glob(new+'/*.py')) != len(glob.glob(old+'/*.py')):
        print '\033[31m Number of files differ in %s \033[0m' %new
        return False
    
    #Check if plots agree:
    for f in glob.glob(new+'/*.py'):
        fold = os.path.join(old,os.path.basename(f))
        fold = fold.replace('MassA','mother')
        fold = fold.replace('massA','mother')
        fold = fold.replace('__','+')
        if 'MassC' in f:
            fold = fold.replace('MassB','inter0').replace('MassC','lsp')
            fold = fold.replace('massB','inter0').replace('massC','lsp')
        else:
            fold = fold.replace('MassB','lsp')
            fold = fold.replace('massB','lsp')
            
        if not os.path.isfile(fold):
            if '150.0' in fold:
                fold = fold.replace('150.0','1.5e+2')
            elif '180.0' in fold:
                fold = fold.replace('180.0','1.8e+2')
            elif '60.0' in fold:
                fold =  fold.replace('60.0','60.')
            elif '300.0_' in fold:
                fold = fold.replace('300.0_','300.000000000000_')
            elif 'inter02y' in fold:
                fold = fold.replace('inter02y','inter02.0y')
            if not os.path.isfile(fold):
                print '\033[31m File %s not found \033[0m' %fold
                return False
                
        fnew = open(f,'r')
        newData = eval(fnew.read().replace('\n','').split('=')[1])
        fnew.close()
        fold = open(fold,'r')
        oldData = eval(fold.read().replace('\n','').split('=')[1])
        fold.close()
        
        #Make sure the same points get compared:
        newData = sorted(newData, key = lambda pt: pt['slhafile'])
        oldData = sorted(oldData, key = lambda pt: pt['slhafile'])
        
        if len(newData) != len(oldData):
            newfiles = set([pt['slhafile'] for pt in newData])
            oldfiles = set([pt['slhafile'] for pt in oldData])
            logger.error('Length of new data (%i) and old data (%i) differ in %s' %(len(newData),len(oldData),f))
            newfiles.symmetric_difference_update(oldfiles)
            print 'Missing files:',newfiles
            return False
        
        for i,pt in enumerate(newData):
            if not checkValue(pt,oldData[i],reps=0.01):
                return False
 
     
    
    return True



if __name__ == "__main__":
    
    
    databasePath = '/home/lessa/smodels-database'
    
    ignoreList = ['ATLAS-SUSY-2013-15', #Duplicated points removed
                  'CMS-SUS-13-006', #The on/off-shell splitting for TChiWZ in master is inconsistent with the constraints
                  'CMS-SUS-13-007', #There is no fully off-shell region for T5tttt (the result in master is inconsistent)
                  'CMS-SUS-13-013', #The on/off-shell splitting for T6ttWW in master is inconsistent with the constraints
                  'ATLAS-SUSY-2013-04-eff', #The T5ZZ validation plots in master are fake (no exclusion curves)
                  'ATLAS-SUSY-2013-15-eff', #The rounding on the dataInfo fields results in small changes of SR selection
                  'CMS-SUS-13-007-eff' #The rounding on the dataInfo fields results in small changes of SR selection
                  ]   

    
    for f in sorted(glob.glob(databasePath+'/*/*/*/validation'))[:]:
        
#         if not '-eff' in f:
#             print "\033[31m Not checking EM result %s \033[0m" %f.replace('convert.py','')
#             continue  #Skip efficiency map results
        
        ignore = False
        for igF in ignoreList:
            if igF in f:
                if '-eff' in igF and not '-eff' in  f:
                    continue
                if '-eff' in f and not '-eff' in igF:
                    continue
                ignore = True
                break
        if ignore:
            print "\033[31m Not checking %s \033[0m" %os.path.dirname(f)
            continue
        
        
        t0 = time.time()
        newdir = f
        olddir = f.replace('smodels-database','smodels-database-master')
        
       
        check = checkNewOutput(new=newdir,old=olddir)
        if not check:
            print '\033[31m Error comparing %s \033[0m' %newdir
#             sys.exit()
        else:    
            print "\033[32m %s OK (runtime = %.1f s) \033[0m"%(f,time.time()-t0)
            