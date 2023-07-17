#!/usr/bin/env python

"""
.. module:: checkConversion
   :synopsis: Compares the globalInfo.txt, dataInfo.txt and txname.txt files between
              an old format folder and a new format folder.

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

from __future__ import print_function

import sys,os,filecmp
import glob,time
sys.path.append('/home/lessa/smodels-utils')
sys.path.append('/home/lessa/smodels')
from smodels.base.physicsUnits import fb,pb,GeV,TeV
from smodels_utils.dataPreparation.databaseCreation import removeRepeated
import logging
FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

databasePath = '/home/lessa/smodels-database'

def compareLines(new,old,ignore=['#']):
    """
    Compare the lines of two files irrespective of their order
    Ignore lines which start with strings given by ignore.
    
    :param new: path to new file
    :param old: path to old file
    :param ignore: List of strings to be ignored
    
    :return: True/False
    """
    
    fnew = open(new,'r')
    newLines = sorted(fnew.readlines())
    fnew.close()
    fold = open(old,'r')
    oldLines = sorted(fold.readlines())
    fold.close()
    
    #Remove ignored lines:
    for fLines in [newLines,oldLines]:
        for i,l in enumerate(fLines):
            if not l:
                continue
            if not l.strip().replace('\n',''): #Remove empty lines
                fLines[i] = None
                continue        
            for ig in ignore:
                if l.lstrip()[:len(ig)] == ig:
                    fLines[i] = None
                    break
        while fLines.count(None):
            fLines.remove(None)
        
        
    if len(newLines) != len(oldLines):
        logger.debug('Number of lines in %s and %s differ' %(new,old))
        return False
    
    for i,l in enumerate(newLines):
        if l != oldLines[i]:
            logger.debug('Line %i in %s and %s differ:\n\t %s\n\t %s' %(i,new,old,l,oldLines[i]))
            return False
    
    return True
        

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
        if len(value) != len(oldValue):
            logger.error('\nNew value length = %i \nOld value length = %i' %(len(value),len(oldValue)))
            return False
        for i,v in enumerate(value):
            c = checkValue(v,oldValue[i],reps)
            if not c:
                if len(oldValue) < 4:
                    logger.error("Old: %s \nNew: %s" %(oldValue,value))
                return False
    else:
        vdiff = abs(value-oldValue)/(abs(value+oldValue))
        if vdiff > reps:
            logger.error('New value = %s \nOld value = %s' %(value,oldValue))
            return False                
    
    return True


def compareFields(new,old,ignoreFields=['susyProcess'],skipFields=[],reps=0.01):
    """
    Compare the fields and their values
    for two files. Ignore lines which start with strings given by ignore.
    For floats, compare their relative difference up to reps
    
    :param new: path to new file
    :param old: path to old file
    :param ignoreFields: List of tag strings to be completely ignored
    :param skipFields: List of tag strings for which the values should be ignored
                     (but they should be present in new if and only if present in old)
    :param reps: allowed relative difference for floats:
    
    :return: True/False
    """
    
    fnew = open(new,'r')
    fold = open(old,'r')    
    newLines = fnew.readlines()
    oldLines = fold.readlines()
    fnew.close()
    fold.close()

    allFields = []    
    for fLines in [newLines,oldLines]:
        fields = {}
        for l in fLines:
            l = l.replace('\n','')
            if not l.strip():
                continue  #Skip empty lines
            if ':' in l:
                field = l.split(':')[0].strip()
                value = "".join(l.split(':')[1:]).strip()
                if field in ignoreFields:
                    continue  #Skip fields to be ignored
                fields[field] = value
                lastField = l.split(':')[0].strip()
            else:
                fields[lastField] += l.strip()
        for key,value in fields.items():
            try:
                fields[key] = eval(value,{'fb' : fb, 
                                          'GeV' : GeV, 
                                          'pb' : pb, 
                                          'TeV' : TeV})
            except:
                pass
        allFields.append(fields)
    
    newFields,oldFields = allFields

    #Check fields:
    if len(newFields) != len(oldFields):
        logger.error("Number of fields in %s differ" %new)
        for key in set(newFields.keys()).symmetric_difference(set(oldFields.keys())):
            if key in newFields:
                print ( 'Missing in old:',key )
            else:
                print ( 'Missing in new:',key )
        return False
    if sorted(newFields.keys()) != sorted(oldFields.keys()):
        logger.error("Fields in %s differ" %new)
        return False

    
    for key,value in newFields.items():
        oldValue = oldFields[key]
        if key in skipFields:
            continue
        if key == 'upperLimits' or key == 'expectedUpperLimits' or key == 'efficiencyMap':
            oldValue  = removeRepeated(oldValue)
        if not checkValue(value, oldValue, reps):
            logger.error("Field %s value differ in %s:\n old = %s ...\n new = %s ..." %(key,new,str(oldValue)[:80],str(value)[:80]))
            return False

    return True
    
    
def replaceValidated(new,old):
    """
    Replace validated field in the new file by the value in the old one
    
    :param new: full path to the new experimental result folder
    :param old: full path to the corresponding old experimental result folder
    """
    
    fold = open(old,'r') 
    oldLines = fold.readlines()
    fold.close()
    valLine = None   
    for l in oldLines:
        if 'validated:' in l.replace(" ",""):
            valLine = l
            break
    if not valLine:
        return
    
    
    fnew = open(new,'r')
    newLines = fnew.readlines()
    fnew.close()
    fnew = open(new,'w')
    for l in newLines:
        if 'validated:' in l.replace(" ",""):
            fnew.write(valLine)
        else:
            fnew.write(l)
    fnew.close()
               

def checkNewOutput(new,old,setValidated=True):
    """
    Check the files in the new folder and the old folder.
    If setValidated = True and both folders are equal, replace the
    validation field in the new folder to the same one in the old folder.
    
    :param new: full path to the new experimental result folder
    :param old: full path to the corresponding old experimental result folder
    :param setValidated: If True, replace the validation field in the new folder
                         by the same value present in the old one.
    
    :return: True if both folders are equivalent, False otherwise.
    """
    
    
    #Check if folders have the same required structure:
    newOrigFolders = ['data-cut%i-orig'%i for i in range(20)]
    ignoreFiles = ['convertNew.py','convertNew.py~','convert.py~','convertNew_template.py']
    ignoreFiles += newOrigFolders
    comp = filecmp.dircmp(new,old,ignoreFiles)
    if comp.left_only:
        logger.warning('Only in new: %s' %comp.left_only)
    if comp.right_only:
        logger.warning('Only in old: %s' %comp.right_only)

    for f in comp.diff_files:
        if f == 'sms.root':
            continue #Ignore the ROOT file (will be tested later in validation)        
        fnew = os.path.join(new,f)
        fold = os.path.join(old,f)
        if not compareLines(fnew,fold):
            if '.txt' in f:
                if compareFields(fnew,fold,ignoreFields=[]):
                    continue            
            logger.error('File %s differ' %f)
            return False
    
    for subdir in comp.subdirs:
        if subdir in ['orig','validation']:
            continue
        sdir = comp.subdirs[subdir]
        if sdir.left_only:
            logger.warning('Only in new: %s/%s' %(subdir,sdir.left_only))
        if sdir.right_only:
            logger.warning('Only in old: %s/%s' %(subdir,sdir.right_only))

        for f in sdir.diff_files:
            if f == 'sms.root':
                continue #Ignore the ROOT file (will be tested later in validation)
  
            fnew = os.path.join(new,os.path.join(subdir,f))
            fold = os.path.join(old,os.path.join(subdir,f))
            if setValidated:
                replaceValidated(fnew,fold)                     
            if not compareLines(fnew,fold,ignore=['#']):
                if not compareFields(fnew,fold,ignoreFields=['susyProcess','source','publishedData','dataUrl','finalState'],
                                     skipFields=['axes']):
                
                    return False
    
    
    return True
        


    
if __name__ == "__main__":
    
      
    ignoreList = ['CMS-SUS-13-006', #The on/off-shell splitting in master is inconsistent with the constraints
                  'CMS-SUS-13-007', #The on/off-shell splitting in master is inconsistent with the constraints
                  'ATLAS-SUSY-2013-05',  #Plane assignments are tricky (some planes only have off-shell points) -> Only axes and figureUrl differ
                  'ATLAS-SUSY-2013-15',   #Plane assignments are tricky (on/off-shell) and need to be defiend by hand -> Only axes and figureUrl differ
                  'CMS-SUS-13-013'] #The on/off-shell splitting in master is inconsistent with the constraints
    
    for f in sorted(glob.glob(databasePath+'/*/*/*/convertNew.py'))[:]:               
        
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
            print ( "\033[31m Not checking %s \033[0m" %os.path.dirname(f) )
            continue


        t0 = time.time()        
        rdir = f.replace(os.path.basename(f),'')        
        oldir = rdir.replace(databasePath,'/home/lessa/smodels-database-master')
        check = checkNewOutput(new=rdir,old=oldir,setValidated=False)
        if not check:
            print ( '\033[31m Error comparing %s \033[0m' %rdir )
            
        print ( "\033[32m %s OK (runtime = %.1f s) \033[0m"%(f,time.time()-t0) )
        
