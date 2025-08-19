#!/usr/bin/env python

"""
.. module:: convertToNewFormat
   :synopsis: Tries to create convertNew.py (allowing the new format) from convert.py

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

from __future__ import print_function

import sys,glob,os,time,math,inspect
from subprocess import Popen,PIPE
home=os.environ["HOME"]
sys.path.append(f'{home}/smodels-utils' )
sys.path.append(f'{home}/smodels' )
thisdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
thisdir = thisdir.replace ( "/smodels_utils/dataPreparation", "" )
sys.path.append( thisdir )
from smodels_utils.dataPreparation.inputObjects import TxNameInput
from smodels_utils.dataPreparation.checkConversion import checkNewOutput
from removeDocStrings import rmDocStrings

databasePath = f'{home}/smodels-database'


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

        if f"{objType}(" in l:
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
    instanceTag = f"{objName}={objType}("
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
        if  f"{objName}=" == newl and start:  #Object name is being redefined. Stop it
            stop = True
        elif f"{objName}." == newl:
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
        if not f"\"{datasetId}\"" in b:
            continue
        for l in b.split('\n'):
            if not l.strip():
                continue
            datasetLines.append(f"{l}\n")

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
                val = f"\"{val}\""
            return val



def addTxnameOffLines(fnew,txname,txOffLines,onshellConstraint):
    """
    Adds to fnew the lines corresponding to the
    off-shell txname
    """

    hasConstraint = False
    for l in txOffLines:
        if f"{txname}.off.constraint" in l:
            hasConstraint = True
            break

    #If no constraint has been defined, the off txname
    #was not properly defined and will be ignored:
    #(Sometimes the off topology is not properly commented out)
    if not hasConstraint:
        return False


    #Ignore mass constraints for on-shell txname
    #everytime off-shell also exists (include full data):
    fnew.write(f'{txname}.massConstraint = None\n')

    #Define off-shell txname:
    fnew.write(f"{txname}off = dataset.addTxName('{txname}off')\n")
    for l in txOffLines:
        l = l.replace('.off.','off.')
        fnew.write(l)
    #Set mass constraint for off-shell txname:
    massConstraint = getMassConstraint(txname,onshellConstraint) #Get on-shell constraints
    massConstraintOff = str(massConstraint).replace('>','<') #Get off-shell constraints
    massConstraintOff = massConstraintOff.replace("'m <= 0.0'","'m >= 0.0'") #Revert back dummy constraints
    fnew.write(f'{txname}off.massConstraint = {massConstraintOff}\n')
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
    print ( f"creating {fnew} from {f}" )

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
            print ( 'Error evaluating auxBlock' )
            print ( e )
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
        fnew.write('\n\n')
        for l in templateLines:
            if not l.strip():
                continue
            l = f"{l}\n"
            datasetLines = getDatasetBlock(fold, dataset)
            dataDict = {'dataset' : f"\"{dataset}\"",
                        'datasetFolder' : f"\"{dataset.replace(' ', '')}\"",
                        'datasetStr' : dataset}
            dataDict.update(getDatasetStatistics(datasetLines))

            #Get variables:
            lineVars = l.split('$')
            lineVars = [v for v in lineVars[1::2] if v]
            for v in lineVars:
                if v in dataDict:
                    l  = l.replace(f"${v}$",str(dataDict[v]))
                elif v in locals() or v in globals():
                    l  = l.replace(f"${v}$",str(eval(f'{v}["{dataset}"]')))

            if '.efficiencyMap.dataUrl' in l:
                l = l.replace('efficiencyMap.dataUrl','dataUrl')

            if not '$' in l:
                fnew.write(l)
                continue
            elif '$$' in l:
                key = l.split('=')[0]
                val = getValueFor(datasetLines,key)
                l = f"{key} = {val!s}\n"
                fnew.write(l)
            else:
                print ( f'Something wrong with line {l}' )
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
    import argparse
    ap = argparse.ArgumentParser ( "convert to new format" )
    ap.add_argument ( '-d', '--dont_run', help='just convert, dont run', action='store_true' )
    ap.add_argument ( '-a', '--analysis', help='run only given analysis', type=str, default='all' )
    args = ap.parse_args()

    skipList = ['ATLAS-SUSY-2013-16-eff', #Not all txnames have the same SRs (has to be assigned by hand)
                'ATLAS-SUSY-2013-18-eff',#Same as above and the statistics for a single SR has to be set by hand
                'ATLAS-SUSY-2013-21-eff', #Not all txnames have the same SRs (has to be assigned by hand)
                'CMS-SUS-13-011-eff', #Statistics for a single SR has to be set by hand
                'ATLAS-SUSY-2013-11-eff',
                'ATLAS-SUSY-2013-02-eff'] #Statistics for a single SR has to be set by hand
    skipList = []

    ignoreList = []

    #Set SMODELSNOUPDATE to avoid rewritting implementedBy and lastUpdate fields:
    os.environ["SMODELS_NOUPDATE"] = 'True'
    timeOut = 15000.

    nres = 0
    # files = sorted(glob.glob(databasePath+'/*/*/*/convertNew.py')  )
    files = sorted(glob.glob(f"{databasePath}/*/*/*/convert.py")  )
    t0 = time.time()
    analysis = args.analysis
    if analysis == ".":
        cwd = os.getcwd()
        analysis = os.path.basename ( os.getcwd() )
        print ( f". -> {analysis}" )
    for f in files:
        if not '-eff' in f:
#             print "\033[31m Not checking %s \033[0m" %f.replace('convert.py','')
            continue  #Skip UL results
        if analysis != "all" and not analysis in f: 
            continue

        #Skip writing convertNew.py for the results in skipList
        skipProduction = False #(ALWAYS SKIP SINCE ALL STATISTICS HAVE BEEN SET BY HAND)
        for skipRes in skipList+ignoreList:
            if skipRes in f:
                skipProduction = True
                break

        nres += 1

        if nres < 0:
            continue

        fnew = f.replace('convert.py','convertNew.py')
        print ( f'create {fnew}' )
        if not skipProduction:
            if os.path.isfile(fnew):
                os.remove(fnew)
            r = main(f,fnew)

            if not r:
                print ( f'\x1b[31m Error generating {fnew} \x1b[0m' )
                sys.exit()
        else:
            print ( f'\x1b[31m Skipping {fnew} \x1b[0m' )

        rdir = fnew.replace(os.path.basename(fnew),'')
        #Make file executable
        run = Popen(f'chmod +x {fnew}',shell=True)
        run.wait()
        if args.dont_run:
            continue
        #Execute file
        run = Popen(f"{fnew} -smodelsPath {home}/smodels -utilsPath {home}/smodels-utils",
                    shell=True,cwd=rdir,stdout=PIPE,stderr=PIPE)

        rstatus = None
        while rstatus is None and ((time.time() - t0) < timeOut):
            time.sleep(5)
            rstatus = run.poll()
        if time.time() - t0 > timeOut:
            run.terminate()
            print ( f'\x1b[31m Running {fnew} exceeded timeout {timeOut} \x1b[0m' )
            sys.exit()


        if rstatus:
            print ( f'\x1b[31m Error running {fnew} \x1b[0m' )
            print ( rstatus )
            sys.exit()
        rerror = run.stderr.read()
        if rerror:
            print ( f'\x1b[31m Error running {fnew}: \x1b[0m' )
            print ( rerror )
            sys.exit()

        ignore = False
        for igF in ignoreList:
            if igF in f:
                ignore = True
                break
        if ignore:
            print ( f"\x1b[31m Not checking {f.replace('convert.py', '')} \x1b[0m" )
            continue


        oldir = rdir.replace(databasePath,f'{home}/smodels-database-master' )
        check = checkNewOutput(new=rdir,old=oldir,setValidated=True)
        if not check:
            print ( f'\x1b[31m Error comparing {rdir} \x1b[0m' )
            sys.exit()

    print ( f"\x1b[32m {f} OK (runtime = {time.time() - t0:.1f} s) \x1b[0m" )

