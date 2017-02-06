#!/usr/bin/env python

"""
.. module:: convertToNewFormat
   :synopsis: Tries to create convertNew.py (allowing the new format) from convert.py

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""


import sys,glob,os,time
from subprocess import Popen,PIPE
sys.path.append('/home/lessa/smodels-utils')
sys.path.append('/home/lessa/smodels')
from smodels_utils.dataPreparation.inputObjects import TxNameInput
from smodels_utils.dataPreparation.checkConversion import checkNewOutput
from removeDocStrings import  rmDocStrings


databasePath = '/home/lessa/smodels-database'

    
    
def getObjectNames(f,objType):
    """
    Reads the file and get the names of all objects of the type objType
    
    :param f: file object
    :param objType: Object type (e.g. MetaInfoInput, TxNameInput,...)
    
    :return: list with object names in file f
    """    
    
    if isinstance(f,list):
        lines = f
    else:
        f.seek(0,0)
        lines = f.readlines()

    objects = []
    for l in lines:
        if l.lstrip() and l.lstrip()[0] == '#':
            continue
        
        if objType+'(' in l:            
            objName = l.split('=')[0].strip() #Store name of objType instance
            if objName:
                objects.append(objName)        
                
    return objects

def getObjectLines(f,objName,objType=None):
    """
    Reads f and collects all lines (beginning with one with objName = objType 
    and have objName.xxx. Stops searching when objName = xxx if found again.
    
    :param f: file object
    :param objName: name of object in file (e.g. info, T1,..)
    :param objType: Object type (e.g. MetaInfoInput, TxNameInput,...)
    
    :return: string with all lines  
    """
    
    if isinstance(f,list):
        lines = f
    else:
        f.seek(0,0)
        lines = f.readlines()
    objLines = []
    instanceTag = "%s=%s(" %(objName,objType)
    start,stop = False,False
    if not objType:
        start = True    
    for l in lines:
        if l.lstrip() and l.lstrip()[0] == '#':
            continue        
        if not start and instanceTag == l.replace(" ","")[:len(instanceTag)]:
            start = True
            objLines.append(l)            
            continue
        if not start:
            continue
        if stop:
            break
        
        newl = l.replace(" ","")[:len(objName)+1] #Get beginning of line
        if  objName+'=' == newl and start:  #Object name is being redefined. Stop it
            stop = True
        elif objName+'.' == newl:
            objLines.append(l) # Line belongs to metablock

    return objLines

def getDatasetIds(f):
    """
    Reads f and finds all datasets defined by setSource.
    If none are found, returns empty list
    
    :param f: file object
    
    :return: list with dataset IDs or empty list if no datasets
            are found (for UL results).
    """
    
    f.seek(0,0)
    #Collect datasets
    datasets = set()
    for l in f.readlines():
        if l.lstrip() and l.lstrip()[0] == '#':
            continue
        
        if '.setSource(' in l and 'dataset' in l:
            dataId = l.split('dataset')[1]
            dataId = dataId[dataId.find('=')+1:]
            dataId = dataId[:dataId.find('"',2)]
            dataId = dataId.strip().replace('"','').replace("'","")            
            if dataId:
                datasets.add(dataId)
    
    if not datasets:
        return [None]
    else:
        return list(datasets)
    
def getDatasetStatistics(dataLines):
    """
    Reads f and finds all datasets defined by setSource.
    If none are found, returns empty list
    
    :param f: file object
    
    :return: list with dataset IDs or empty list if no datasets
            are found (for UL results).
    """
    
    statDict = {'observedN' : None, 'expectedBG' : None, 'bgError' : None}
    
    dataBlock = "\n".join(dataLines)
    dataB = dataBlock.replace(" ","")
    i0 = dataB.find('.setStatistics(')+15
    stat = dataB[i0:dataB.find(')',i0)]    
        
    statStr = stat.strip()
    for s in statStr.split(','):
        key,val = s.split('=')
        key = key.strip()
        val = eval(val)
        if key in statDict:
            statDict[key] = val
    
    return statDict
            
def getDatasetBlock(f,datasetId):
    
    f.seek(0,0)
    blocks = f.read().split('databaseCreator.create')
    datasetLines = []    
    for b in blocks:
        if not '"'+datasetId+'"' in b:
            continue
        for l in b.split('\n'):
            if not l.strip():
                continue
            datasetLines.append(l+'\n')
    
    return datasetLines

def getValueFor(dataLines,key):

    for l in dataLines:
        newl = l.replace(" ","")
        newkey = key.replace(" ","")
        if newl[:len(newkey)] == newkey:
            val = l.split('=')[-1]
            try:
                val = eval(val)
            except:
                pass
            if isinstance(val,str):
                val = '"'+val+'"'
            return val
   
def getSources(planeLines):
    """
    Reads the lines associated to a plane and extract the sources.
    Returns a unified setSources string in new format
    
    :param planeLines: list with the lines associated to the plane
    
    :return: string with the new setSources format
    """
    
    dataLabelsDict = {}
    dataFormatsDict = {}
    dataFilesDict = {}
    unitsDict = {}
    objcNamesDict = {}
    indicesDict = {}
    
    #First get units (if defined)
    for l in planeLines:
        if '.unit' in l:
            unit = l.split('=')[1].replace(" ","").replace('\n','').replace("'","").replace('"','')
            sourceName = l.split('.')[1]
            unitsDict[sourceName] = unit
    

    for l in planeLines:
        if not '.setSource' in l:
            continue
        #Get source type and input:
        sourceName,sInput = l.split('(')
        sourceName = sourceName.split('.')[1].strip()
        sInput = sInput.replace(')','')
        if sourceName == 'obsUpperLimit':
            sType = 'upperLimits'
        elif sourceName == 'expUpperLimit':
            sType = 'expectedUpperLimits'
        else:
            sType = sourceName
        dataLabelsDict[sourceName] = sType
        sInput = sInput.split(",")
        #Get input entries
        for inputEntry in sInput:
            inputEntry = inputEntry.replace("'","").replace('"','')
            if 'orig/' in inputEntry:
                dataFilesDict[sourceName] = inputEntry.split('=')[-1].strip()          
            elif inputEntry.strip() in ['root','txt','svg','canvas','cMacro']:                
                dataFormatsDict[sourceName] = inputEntry.split('=')[-1].strip()        
            elif 'objectName' in inputEntry:
                objcNamesDict[sourceName] = inputEntry.split('=')[-1].strip()
            elif 'index' in inputEntry:
                indicesDict[sourceName] = inputEntry.split('=')[-1].strip()
    
    dataLabels = []
    dataFiles = []
    dataFormats = []
    units = []
    objNames = []
    indices = []
    #Get ordered list of properties:
    for sourceName in sorted(dataFilesDict.keys()):
        dataFiles.append(dataFilesDict[sourceName])
        dataLabels.append(dataLabelsDict[sourceName])
        dataFormats.append(dataFormatsDict[sourceName])
        if not sourceName in unitsDict:
            units.append(None)
        else:
            units.append(unitsDict[sourceName])
        if not sourceName in objcNamesDict:
            objNames.append(None)
        else:
            objNames.append(objcNamesDict[sourceName])
        if not sourceName in indicesDict:
            indices.append(None)
        else:
            indices.append(eval(indicesDict[sourceName]))
        
    
    newSourceStr = ".setSources(dataLabels= %s,\n\
                 dataFiles= %s,\n\
                 dataFormats= %s" %(dataLabels,dataFiles,dataFormats)
    if objNames.count(None) != len(objNames) and objNames.count('None') != len(objNames):
        newSourceStr += ",objectNames= %s" %objNames                 
    if indices.count(None) != len(indices) and indices.count('None') != len(indices):
        newSourceStr += ",indices= %s" %indices
    if units.count(None) != len(units) and units.count('None') != len(units):
        newSourceStr += ",units= %s" %units

    return newSourceStr+")"

def addTxnameOffLines(fnew,txname,txOffLines,onshellConstraint):
    """
    Adds to fnew the lines corresponding to the
    off-shell txname
    """
    
    hasConstraint = False
    for l in txOffLines:
        if "%s.off.constraint" %txname in l:
            hasConstraint = True
            break
    
    #If no constraint has been defined, the off txname
    #was not properly defined and will be ignored:
    #(Sometimes the off topology is not properly commented out)
    if not hasConstraint:        
        return False
        
    
    #Ignore mass constraints for on-shell txname 
    #everytime off-shell also exists (include full data):
    fnew.write('%s.massConstraint = None\n' %txname)
    
    #Define off-shell txname:
    fnew.write("%soff = dataset.addTxName('%soff')\n" %(txname,txname))
    for l in txOffLines:
        l = l.replace('.off.','off.')
        fnew.write(l)
    #Set mass constraint for off-shell txname:
    massConstraint = getMassConstraint(txname,onshellConstraint) #Get on-shell constraints
    massConstraintOff = str(massConstraint).replace('>','<') #Get off-shell constraints
    massConstraintOff = massConstraintOff.replace("'m <= 0.0'","'m >= 0.0'") #Revert back dummy constraints
    fnew.write('%soff.massConstraint = %s\n' %(txname,massConstraintOff))
    return True

def getMassConstraint(txname,constraint):
    """
    Get mass constraint for constraint appearing in lines
    
    :param txname: Txname string
    :param constraint: Constraint string
    
    :return: String for the massConstraint
    """
    
    tx = TxNameInput(txname)
    tx.constraint = constraint
    tx._setMassConstraints()
    
    if len(tx.massConstraints) == 1:
        massConstraints = tx.massConstraints[0]
    else:
        massConstraints = tx.massConstraints
    
    return massConstraints
    
    
def main(f,fnew):
    
    fold = open(f,'r')
    fnew = open(f.replace('convert.py','convertNew.py'),'w')    
    #Remove comments from old file:
    strClean = rmDocStrings(fold.read())
    fold.close()
    ftemp = f.replace('convert.py','convertTemp.py')
    fold = open(ftemp,'w')
    fold.write(strClean.replace('\n\n','\n'))
    fold.close()
    fold = open(ftemp,'r')
    
    #Open template:
    ftemplate = open(f.replace('convert.py','convertNew_template.py'),'r')
    #Look for aulixiary information:
    template = ftemplate.read()
    auxBlock = template[template.find('BEGIN_AUXILIARY_BLOCK'):template.find('END_AUXILIARY_BLOCK')]
    if auxBlock:
        auxBlock = auxBlock.replace('BEGIN_AUXILIARY_BLOCK','').replace('\n','')
        try:
            exec(auxBlock)
        except Exception as e:
            print 'Error evaluating auxBlock'
            print e
            return False
    
    #Write header
    header = template[:template.find('BEGIN')]
    fnew.write(header)
    
    datasetBlock = template[template.find('BEGIN_BLOCK_TO_FILL'):template.find('END_BLOCK_TO_FILL')]
    templateLines = datasetBlock.replace('BEGIN_BLOCK_TO_FILL','').replace('END_BLOCK_TO_FILL','')
    templateLines = templateLines.split('\n')    
    #Collect datasets
    datasets = getDatasetIds(fold)
    #Loop over datasets and write blocks:
    for dataset in datasets:
        for l in templateLines:
            if not l.strip():
                continue
            l = l + '\n'
            datasetLines = getDatasetBlock(fold, dataset)
            dataDict = {'dataset' : '"'+dataset+'"', 
                        'datasetFolder' : '"'+dataset.replace(" ","")+'"',
                        'datasetStr' : dataset}
            dataDict.update(getDatasetStatistics(datasetLines))
            
            #Get variables:
            lineVars = l.split('$')
            lineVars = [v for v in lineVars[1::2] if v]
            for v in lineVars:
                if v in dataDict:
                    l  = l.replace('$'+v+'$',str(dataDict[v]))
                elif v in locals() or v in globals():
                    l  = l.replace('$'+v+'$',str(eval('%s["%s"]'%(v,dataset))))
                
            if not '$' in l:
                fnew.write(l)
                continue            
            elif '$$' in l:
                key = l.split('=')[0]
                val = getValueFor(datasetLines,key)
                l = key + ' = ' + str(val)+'\n'
                fnew.write(l)
            else:
                print 'Something wrong with line %s' %l
                return False
            
    
    #Write footer
    writeToFile = False
    ftemplate.seek(0,0)
    for l in ftemplate.readlines():
        if 'END_BLOCK_TO_FILL' in l:
            writeToFile = True
            continue
        if writeToFile:
            fnew.write(l)
    
    ftemplate.close()    
    fold.close()
    os.remove(ftemp)    
    fnew.close()        
    return True
    
    
    
if __name__ == "__main__":
    
    
    skipList = [ ]
    
    ignoreList = []
    
    #Set SMODELSNOUPDATE to avoid rewritting implementedBy and lastUpdate fields:
    os.environ["SMODELS_NOUPDATE"] = 'True'
    timeOut = 150.
    
    nres = 0
    for f in sorted(glob.glob(databasePath+'/*/*/*/convert.py')):
        
        if not '-eff' in f:
#             print "\033[31m Not checking %s \033[0m" %f.replace('convert.py','')
            continue  #Skip UL results
        
        
        ignore = False
        for igF in ignoreList:
            if igF in f:                
                ignore = True
                break
        if ignore:
            print "\033[31m Not checking %s \033[0m" %f.replace('convert.py','')
            continue
        
        #Skip writing convertNew.py for the results in skipList
        skipProduction = False
        for skipRes in skipList:
            if skipRes in f:
                skipProduction = True
                break

        nres += 1
        
        if nres < 2:
            continue
                        
        fnew = f.replace('convert.py','convertNew.py')
        if not skipProduction:            
            if os.path.isfile(fnew):
                os.remove(fnew)
            r = main(f,fnew)
                
            if not r:
                print '\033[31m Error generating %s \033[0m' %fnew
                sys.exit()        


        #Make file executable
        run = Popen('chmod +x %s' %fnew,shell=True)
        run.wait()
        #Execute file
        rdir = fnew.replace(os.path.basename(fnew),'')
        t0 = time.time()
        run = Popen(fnew+' -smodelsPath /home/lessa/smodels -utilsPath /home/lessa/smodels-utils',
                    shell=True,cwd=rdir,stdout=PIPE,stderr=PIPE)
        
        rstatus = None
        while rstatus is None and ((time.time() - t0) < timeOut):
            time.sleep(5)
            rstatus = run.poll()
        if time.time() - t0 > timeOut:
            run.terminate()
            print '\033[31m Running %s exceeded timeout %s \033[0m' %(fnew,timeOut)
            sys.exit()
        

        if rstatus:
            print '\033[31m Error running %s \033[0m' %fnew
            print rstatus
            sys.exit()
        rerror = run.stderr.read()
        if rerror:
            print '\033[31m Error running %s: \033[0m' %fnew
            print rerror 
            sys.exit()
        
        oldir = rdir.replace('smodels-database','smodels-database-master')
        check = checkNewOutput(new=rdir,old=oldir,setValidated=True)
        if not check:
            print '\033[31m Error comparing %s \033[0m' %rdir
            sys.exit()
            
        print "\033[32m %s OK (runtime = %.1f s) \033[0m"%(f,time.time()-t0)
        
        