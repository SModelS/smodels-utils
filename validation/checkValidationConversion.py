#!/usr/bin/env python

"""
.. module:: checkValidationConversion
   :synopsis: Compares the validation/T*.py files between
              an old format folder and a new format folder.

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys,os,filecmp,glob,time
sys.path.append('/home/lessa/smodels-utils')
sys.path.append('/home/lessa/smodels')
from smodels.tools.physicsUnits import fb,pb,GeV,TeV
from smodels_utils.dataPreparation.databaseCreation import removeRepeated
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
    
    ignoreList = ['CMS-SUS-13-006', #The on/off-shell splitting in master is inconsistent with the constraints
                  'CMS-SUS-13-007', #The on/off-shell splitting in master is inconsistent with the constraints
                  'ATLAS-SUSY-2013-05',  #Plane assignments are tricky (some planes only have off-shell points) -> Only axes and figureUrl differ
                  'ATLAS-SUSY-2013-15',   #Plane assignments are tricky (on/off-shell) and need to be defiend by hand -> Only axes and figureUrl differ
                  'CMS-SUS-13-013'] #The on/off-shell splitting in master is inconsistent with the constraints
    
    
    for f in sorted(glob.glob(databasePath+'/*/*/*/validation'))[:]:
        
#         if '-eff' in f:
#             print "\033[31m Not checking EM result %s \033[0m" %f.replace('convert.py','')
#             continue  #Skip efficiency map results
        
        ignore = False
        for igF in ignoreList:
            if igF in f:                
                ignore = True
                break
        if ignore:
#             print "\033[31m Not checking %s \033[0m" %f.replace('convert.py','')
            continue
        
        
        t0 = time.time()
        newdir = f
        olddir = f.replace('smodels-database','smodels-database-master')
        
       
        check = checkNewOutput(new=newdir,old=olddir)
        if not check:
            print '\033[31m Error comparing %s \033[0m' %newdir
#             sys.exit()
            
        print "\033[32m %s OK (runtime = %.1f s) \033[0m"%(f,time.time()-t0)
            