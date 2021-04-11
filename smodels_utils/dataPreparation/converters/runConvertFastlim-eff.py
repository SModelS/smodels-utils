#!/usr/bin/env python

"""
.. module:: convertFastlim
   :synopsis: Tries to create convertNew.py (allowing the new format) for Fastlim results

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""


import sys,glob,os,time,math
from subprocess import Popen,PIPE
sys.path.append('/home/lessa/smodels-utils')
sys.path.append('/home/lessa/smodels')
from smodels_utils.dataPreparation.inputObjects import TxNameInput
from smodels_utils.dataPreparation.checkConversion import checkNewOutput
from removeDocStrings import  rmDocStrings
import textwrap


databasePathSource = '/home/lessa/smodels-database-master'
databasePath = '/home/lessa/smodels-database'

template = open("convertNew_template.py",'r')
header = template.read()
template.close()    
    
def getDatasetInfo(fold):
    """
    Get the folder names, and the dataset info from the old
    dataInfo.txt files
    
    :param fold: Experimental result folder in old format
    """
    
    datasets = []
    for f in glob.glob(fold+'/data-cut*/dataInfo.txt'):
        dtDict = {}
        
        folder = f.replace('/dataInfo.txt','')
        dtDict['folder'] = folder.split('/')[-1]
        dataInfo = open(f,'r')
        for l in dataInfo.readlines():            
            field = l[:l.find(':')].strip()
            value = l[l.find(':')+1:].strip()
            try:
                dtDict[field] = value
            except:
                dtDict[field] = value
        datasets.append(dtDict)
        dataInfo.close()
        
    return datasets
        
def getGlobalInfo(fold):
    """
    Get the fields in the old globalInfo.txt file.
    
    :param fold: Experimental result folder in old format
    """
    
    globalDict = {}
    
    globalInfo = open(os.path.join(fold,'globalInfo.txt'),'r')
    for l in globalInfo.readlines():
        if not l.strip().replace('\n',''):
            continue  #Ignore  empty lines
        field = l[:l.find(':')].strip()
        value = l[l.find(':')+1:].strip()
        globalDict[field] = value    
    
    globalInfo.close()
    return globalDict

def getConstraints(fold):
    """
    Returns a dictionary with all the constraints for a given experimental result
    (It is the same for almost all results)
    
    :param fold: Experimental result folder in old format
    """
    constraintsDict =  { "T2tt": "[[['t+']],[['t-']]]", "T2bb": "[[['b']],[['b']]]",
                     "T2": "[[['jet']],[['jet']]]",
                     "T2gg": "[[['jet']],[['jet']]]",
                     "T2bt": "[[['b']],[['t']]]", 
                     "T1tttt": "[[['t+','t-']],[['t+','t-']]]",
                     "T5tttt": "[[['t+'],['t-']],[['t+'],['t-']]]+" \
                               "[[['t-'],['t+']],[['t-'],['t+']]]",
                     "T5bbbb": "[[['b'],['b']],[['b'],['b']]]",
                     "T5bbbt": "[[['b'],['b']],[['b'],['t']]]",
                     "T1bbtt": "[[['b','b']],[['t+','t-']]]", 
                     "T1btbt": "[[['b','t']],[['b','t']]]",
                     "T1bbqq": "[[['b','b']],[['jet','jet']]]", 
                     "T1bbbb": "[[['b','b']],[['b','b']]]",
                     "T1bbbt": "[[['b','b']],[['b','t']]]", 
                     "T5btbt": "[[['b'],['t']],[['b'],['t']]]",
                     "T5tbtb": "[[['t'],['b']],[['t'],['b']]]", 
                     "T5tbtt": "[[['t'],['b']],[['t+'],['t-']]]+[[['t'],['b']],[['t-'],['t+']]]",
                     "TGQqtt": "[[['jet']],[['t+','t-']]]", 
                     "TGQ": "[[['jet']],[['jet','jet']]]",
                     "TGQbtq": "[[['b','t']],[['jet']]]", 
                     "TGQbbq": "[[['b','b']],[['jet']]]",
                     "T1btqq": "[[['b','t']],[['jet','jet']]]", 
                     "T1qqtt": "[[['jet','jet']],[['t+','t-']]]",
                     "T1bttt": "[[['b','t']],[['t+','t-']]]", 
                     "T1": "[[['jet','jet']],[['jet','jet']]]" }

    expid = os.path.basename(fold).replace ( "ATLAS-CONF-","" ).replace("-eff","" )
    if expid in [ "2013-024", "2013-037", "2013-047", "2013-053", "2013-054",
                      "2013-061", "2013-062", "2013-093" ]:
        constraintsDict['T2tt'] = "[[['t']],[['t']]]"
    
    return constraintsDict

def getFigureInfo(fold):
    """
    Collects additional information from old convert.py files
    """
    
    figureLines = []
    for f in glob.glob(fold+'/data-cut*/convert.py'):
        convert = open(f,'r')
        lines = rmDocStrings(convert.read()).split('\n')
        convert.close()
        for l in lines:
            l = l.strip()
            l += '\n'
            if l[:6] == 'figure':
                if not l in figureLines:
                    figureLines.append(l)
                
    return figureLines
                
    
     
   
def main(f,fold):
    
    fnew = open(os.path.join(f,'convertNew.py'),'w')
    
    #Write header:
    fnew.write(header)
    
    #Write dataset information:
    datasets = getDatasetInfo(fold)
    datasetData = "\n\n#+++++++ Datasets info ++++++++++++++\n"
    datasetData += "datasetsInfo = "    
    datasetData += str(datasets).replace('}, ',"},\n").replace('[','[\n').replace(']','\n]')
    fnew.write(datasetData)
    
    #Write constraints information:
    constraints = getConstraints(fold)
    constraintData = "\n\n#+++++++ Constraints info ++++++++++++++\n"
    constraintData += "constraintsDict = {\n"
    for key,val in constraints.items():
        constraintData += '"%s" : "%s",\n' %(key,val)
    constraintData = constraintData.rstrip(',\n')
    constraintData += "\n}"
    fnew.write(constraintData)    
    
    #Write figure dictionary:
    figureLines = getFigureInfo(fold)
    figureData = "\n\n#+++++++ Figure info ++++++++++++++\n"
    figureData += "".join(figureLines)
    fnew.write(figureData)    
    
    
    metaData = "\n\n#+++++++ global info block ++++++++++++++\n"
    #Get metainfo data:
    globalDict = getGlobalInfo(fold)
    metaData += "info = MetaInfoInput('%s')\n" %globalDict['id']
    for key,val in globalDict.items():
        if key == 'id':
            continue
        metaData += "info.%s = '%s'\n" %(key.strip(),val)
    #Write meta info block
    fnew.write(metaData+'\n\n')


    
    #Write common block
    footer = textwrap.dedent("""\
    for dt in datasetsInfo:
        folder = dt.pop('folder')
        dataset = DataSetInput(folder)        
        dataset.setInfo(**dt)
        origDir = os.path.basename(folder)+"-orig/"
        for i in os.listdir(origDir):
            if i[-5:]!=".effi": continue
            txname=i[:-5]
            tmp = dataset.addTxName(txname)
            tmp.constraint = constraintsDict[txname]
            tmp.conditionDescription=None
            tmp.condition = None
            tmp.source = 'Fastlim-v1.0'
            tmp.dataUrl = None
            if i[:2] in [ "T5", "T6" ]:
                tmp_1 = tmp.addMassPlane([[x,y,z]]*2)
                tmp_1.addSource('efficiencyMap', origDir+'%s.effi' % txname, 'effi')
            else:
                tmp_1 = tmp.addMassPlane([[x,y]]*2)
                tmp_1.addSource('efficiencyMap', origDir+'%s.effi' % txname, 'effi')
            if os.path.exists(origDir+'%s_excl.dat' % txname):
                tmp_1.addSource('obsExclusion', origDir+'%s_excl.dat' % txname, 'txt')
            if txname in figure:
                tmp_1.figure = figure[txname]
            if txname in figureUrl:
                tmp_1.figureUrl = figureUrl[txname]
    databaseCreator.create()
    """)
    
    fnew.write(footer+"\n")
    
    fnew.close()
    return True
    
    
    
if __name__ == "__main__":
    
    
    fastlimResults = ["ATLAS-CONF-2013-024-eff",
                      "ATLAS-CONF-2013-035-eff",
                      "ATLAS-CONF-2013-037-eff",
                      "ATLAS-CONF-2013-047-eff",
                      "ATLAS-CONF-2013-048-eff",
                      "ATLAS-CONF-2013-049-eff",
                      "ATLAS-CONF-2013-053-eff",
                      "ATLAS-CONF-2013-054-eff",
                      "ATLAS-CONF-2013-061-eff",
                      "ATLAS-CONF-2013-062-eff",
                      "ATLAS-CONF-2013-093-eff"]
    
    skipList = []
    
    #Set SMODELSNOUPDATE to avoid rewritting implementedBy and lastUpdate fields:
    os.environ["SMODELS_NOUPDATE"] = 'True'
    timeOut = 150.
    
    nres = 0
    for f in sorted(glob.glob(databasePath+'/*/*/*-eff')):
        
        if not os.path.basename(f) in fastlimResults:
#             print "\033[31m Not checking %s \033[0m" %f.replace('convert.py','')
            continue  #Skip UL results
      
        #Skip writing convertNew.py for the results in skipList        
        skipProduction = False
        for skipRes in skipList:
            if skipRes in f:
                skipProduction = True
                break
        
        fold = f.replace('smodels-database','smodels-database-master')
        fnew = os.path.join(f,'convertNew.py')
        print fnew
        if not skipProduction:            
            if os.path.isfile(fnew):
                os.remove(fnew)
            r = main(f,fold)
                
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
        
        oldir = rdir.replace(databasePath,'/home/lessa/smodels-database-master')
        check = checkNewOutput(new=rdir,old=oldir,setValidated=True)
        if not check:
            print '\033[31m Error comparing %s \033[0m' %rdir
            sys.exit()
            
        print "\033[32m %s OK (runtime = %.1f s) \033[0m"%(f,time.time()-t0)
        