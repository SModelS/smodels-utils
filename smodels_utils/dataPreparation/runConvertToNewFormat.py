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

template = open("convertNew_template.py",'r')
header = template.read()



databasePath = '/home/lessa/smodels-database-old'

    
    
def getObjectNames(f,objType):
    """
    Reads the file and get the names of all objects of the type objType
    
    :param f: file object
    :param objType: Object type (e.g. MetaInfoInput, TxNameInput,...)
    
    :return: list with object names in file f
    """    
    
    f.seek(0,0)
    objects = []
    for l in f.readlines():
        if l.lstrip() and l.lstrip()[0] == '#':
            continue
        
        if objType+'(' in l:            
            objName = l.split('=')[0].strip() #Store name of objType instance
            if objName:
                objects.append(objName)        
                
    return objects


def getObjectLines(f,objName,objType):
    """
    Reads f and collects all lines (beginning with one with objName = objType 
    and have objName.xxx. Stops searching when objName = xxx if found again.
    
    :param f: file object
    :param objName: name of object in file (e.g. info, T1,..)
    :param objType: Object type (e.g. MetaInfoInput, TxNameInput,...)
    
    :return: string with all lines  
    """
    
    f.seek(0,0)
    objLines = []
    instanceTag = "%s=%s(" %(objName,objType)
    start,stop = False,False
    for l in f.readlines():
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
            dataId = dataId.strip()
            if dataId:
                datasets.add(dataId)
    
    if not datasets:
        return [None]
    else:
        return list(datasets)
    

def newMassFormat(line):
    """
    Replace axes definition in line by the new format
    (e.g. mother = x, lsp = y --> [[x,y]]*2)
    
    :param line: string containing the axes definition
    
    :return: string with the new format
    """
    
    if not 'mother' in line or not 'lsp' in line or not '(' or not ')':
        print 'Line does not contain old format'
        return line
    
    #Get axes string
    lA = line[:line.find('(')+1]
    lC = line[line.rfind(')'):]
    laxes = line[line.find('(')+1:line.rfind(')')]
    laxes = laxes.split(',')
    newAxes = []
    for eq in laxes:
        eq = eq.replace(" ","")
        xeq = eq.split('=')[1]
        newAxes.append(xeq)
    
    newAxes = str(newAxes).replace("'","")
    newAxes = "2*[%s]" %newAxes
    
    return lA+newAxes+lC
    

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
    massConstraintOff = massConstraintOff.replace("'dm <= 0.0'","'dm >= 0.0'") #Revert back dummy constraints
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

    #Write header:
    fnew.write(header)
    
    #Get metainfo name:
    infoName = getObjectNames(fold, 'MetaInfoInput')
    if not infoName or len(infoName) > 1:
        print 'MetaInfoInput not found or more than one instance found'
        sys.exit()
    else:
        infoName = infoName[0]
    metaData = "\n\n#+++++++ global info block ++++++++++++++\n"
    #Get metainfo lines:
    metaData += "".join(getObjectLines(fold,infoName,'MetaInfoInput'))
    #Write meta info block
    fnew.write(metaData+'\n\n')
    
    #Collect datasets
    datasets = getDatasetIds(fold)    
    #For now only deals with UL results
    #Write dataset blocks:
    for dataId in datasets:
        fnew.write("#+++++++ dataset block ++++++++++++++\n")
        if dataId is None:
            dataFolder = 'data'
            dataType = 'upperLimit'
        else:
            dataFolder = dataId.replace(" ","")
            dataType = 'efficiencyMap'
        datasetStr = "dataset = DataSetInput('%s')\n" %dataFolder #Dataset folder name                
        datasetStr += "dataset.setInfo(dataType = '%s', dataId = %s)" %(dataType,dataId)
        fnew.write(datasetStr+'\n\n')
        
    if datasets != [None]:
        print 'efficiency map result not yet implemented (%s)' %f.replace('convert.py','')
        fold.close()
        fnew.close()        
        return None
        
        
    #Get Txnames:
    txnames = getObjectNames(fold, 'TxNameInput')
    for txname in txnames:
        if txnames.count(txname) > 1:
            print 'Txname %s is defined multiple times' %txname
            return False
        
        fnew.write("#+++++++ next txName block ++++++++++++++\n")
        txLines = getObjectLines(fold, txname,'TxNameInput')
        txOffLines = []
        onshellConstraint = None        
        for l in txLines:
            if 'TxNameInput(' in l:
                l = l.replace('TxNameInput(','dataset.addTxName(')
            elif '.off.' in l:
                txOffLines.append(l)
                continue
            elif '.on.' in l:
                if '%s.on.constraint'%txname in l:
                    onshellConstraint = l.split('=')[1].strip()
                l = l.replace('.on.','.')
            fnew.write(l)
        #Automatically define source:
        if "MetaInfoInput('ATLAS" in metaData.replace(" ",""):
            source = 'ATLAS'
        elif "MetaInfoInput('CMS" in metaData.replace(" ",""):
            source = 'CMS'
        else:
            source = None
        if source:
            fnew.write('%s.source = "%s"\n' %(txname,source))
        #Add txnameOff definitions:
        if txOffLines:
            addedTxOff = addTxnameOffLines(fnew,txname,txOffLines,onshellConstraint)
            if addedTxOff and source:
                    fnew.write('%soff.source = "%s"\n' %(txname,source))


        #Get mass planes for txname:
        massPlanes = getObjectNames(fold, '%s.addMassPlane'%txname)
        for plane in massPlanes:
            fnew.write("#+++++++ next mass plane block ++++++++++++++\n")
            if massPlanes.count(plane) > 1:
                print 'Plane %s for %s is defined multiple times' %(plane,txname)
                return False
            planeLines = getObjectLines(fold, plane, '%s.addMassPlane'%txname)
            hasDataUrl = False            
            for l in planeLines:
                if '.addMassPlane(' in l:
                    l = newMassFormat(l)
                elif '.setSource' in l:
                    continue
                elif '.obsUpperLimit.dataUrl' in l:
                    l = l.replace('.obsUpperLimit','')
                elif l.split('=')[0].count('.') > 1:
                    continue  #Skip attributes given to derived objects
                if 'dataUrl' in l:
                    hasDataUrl = True
                fnew.write(l)
            #Write down dataUrl if not yet appears:
            if not hasDataUrl:
                fnew.write("%s.dataUrl = 'Not defined'\n" %plane)
            #Extract sources from file:
            sourceStr = plane+getSources(planeLines)
            fnew.write(sourceStr+'\n')

            #Add plane to off-shell txname, if off-shell lines
            #have been added
            if txOffLines and addedTxOff:          
                fnew.write("%s.addMassPlane(%s)\n" %(txname+"off",plane))
            
        fnew.write('\n')
            
        
    fold.close()
    os.remove(ftemp)
    
    fnew.write('\n\ndatabaseCreator.create()\n')
    fnew.close()        
    return True
    
    
    
if __name__ == "__main__":
    
    
    skipList = ['ATLAS-CONF-2013-001', #T6bbWW only has off-shell data, so the on-shell massConstraint has to be set
                'ATLAS-CONF-2013-007',  #Mass constraints are tricky and need to be fixed by hand
                'ATLAS-CONF-2013-035',   #DataUrl was not set for full plane
                'ATLAS-CONF-2013-036',    #TChiSlepSlep (asymmetric branches)
                'ATLAS-CONF-2013-047','ATLAS-SUSY-2013-02'    #TGQ (asymmetric branches)                                
                ]
    
    ignoreList = ['CMS-SUS-13-006', #The on/off-shell splitting in master is inconsistent with the constraints
                  'CMS-SUS-13-007', #The on/off-shell splitting in master is inconsistent with the constraints
                  'ATLAS-SUSY-2013-05',  #Plane assignments are tricky (some planes only have off-shell points) -> Only axes and figureUrl differ
                  'ATLAS-SUSY-2013-15',   #Plane assignments are tricky (on/off-shell) and need to be defiend by hand -> Only axes and figureUrl differ
                  'CMS-SUS-13-013'] #The on/off-shell splitting in master is inconsistent with the constraints
    
    #Set SMODELSNOUPDATE to avoid rewritting implementedBy and lastUpdate fields:
    os.environ["SMODELS_NOUPDATE"] = 'True'
    timeOut = 150.
    
    for f in sorted(glob.glob(databasePath+'/*/*/*/convert.py'))[:]:               
        
        if '-eff' in f:
#             print "\033[31m Not checking EM result %s \033[0m" %f.replace('convert.py','')
            continue  #Skip efficiency map results
        
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
                
        fnew = f.replace('convert.py','convertNew.py')
        if not skipProduction:            
            if os.path.isfile(fnew):
                os.remove(fnew)
#             print f
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
        
#         print run.stdout.read()
#         print run.stderr.read()

        if rstatus:
            print '\033[31m Error running %s \033[0m' %fnew
            print rstatus
            sys.exit()
        rerror = run.stderr.read()
        if rerror:
            print '\033[31m Error running %s: \033[0m' %fnew
            print rerror 
            sys.exit()
        
        oldir = rdir.replace(databasePath,'/home/lessa/smodels-database-master')
        check = checkNewOutput(new=rdir,old=oldir,setValidated=True)
        if not check:
            print '\033[31m Error comparing %s \033[0m' %rdir
            sys.exit()
            
        print "\033[32m %s OK (runtime = %.1f s) \033[0m"%(f,time.time()-t0)
        