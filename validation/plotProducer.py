#!/usr/bin/env python

"""
.. module:: plotProducer
   :synopsis: Main classes and methods for producing several validation plots

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
from validationObjs  import ValidationPlot
from plottingFuncs import getExclusionCurvesFor
from smodels.tools.physicsUnits import fb, pb, GeV

logger.setLevel(level=logging.ERROR)

def getExpIdFromPath():
    """ get experimental id from path """
    ret=os.getcwd()
    ret=ret.replace("/validation","")
    ret=ret.replace("-eff","")
    ret=ret[ret.rfind("/")+1:]
    return ret

def getDatasetIdsFromPath(folder="../"):
    """ determine the datasetids from the path"""
    files=os.listdir(folder)
    datasetids=[]
    for f in files:
        if not f in [ "globalInfo.txt", "validation", "sms.root", "convert.py", "old", "smodels.log", "orig", ".DS_Store" ]:
        ## f=f.replace("data-","").replace("ana","ANA").replace("cut","CUT" )
            if not os.path.isdir ( os.path.join ( dir, f ) ): 
                continue
            if f=="data": f=None
            datasetids.append  ( f )
    return datasetids


def validatePlot(expRes,txname,axes,slhadir,kfactor=1.,recycle_data=False ):
    """
    Creates a ValidationPlot object and saves its output.
    
    :param expRes: a ExpResult object containing the result to be validated
    :param txname: String describing the txname (e.g. T2tt)
    :param axes: the axes string describing the plane to be validated
     (i.e.  2*Eq(mother,x),Eq(lsp,y))
    :param slhadir: folder containing the SLHA files corresponding to txname
    or the .tar file containing the SLHA files.
    :param kfactor: optional global k-factor value to re-scale 
                    all theory prediction values
    :param recycle_data: use python dictionary files, if they exist
    """

    #Get exclusion curve for expRes:
    curve = getExclusionCurvesFor(expResult=expRes,txname=txname,axes=axes)
    if not curve:
        return False

    logger.info("Generating validation plot for " + expRes.getValuesFor('id')[0]
                +", "+txname+", "+axes)        
    valPlot = ValidationPlot(expRes,txname,axes,kfactor=kfactor)
    valPlot.setSLHAdir(slhadir)
    filename="%s_%s.py" % ( txname, 
            axes.replace("(","").replace(")","").replace(",","").replace("*","") )
    if recycle_data and os.path.exists (filename ):
        print "Recycling data from %s" % filename
        globs ={ "pb": pb, "fb": fb }
        execfile(filename,globs )
        valPlot.data = globs["validationData"]
    else:
        valPlot.getData()
    valPlot.getPlot()
    valPlot.savePlot()
    valPlot.saveData()
    logger.info("Validation plot done.")
    return valPlot.computeAgreementFactor() # return agreement factor
    
def validateTxName(expRes,txname,slhadir,kfactor=1., recycle_data = False ):
    """
    Creates a ValidationPlot for each plane/axes appearing
    in txname and saves the output.
    
    :param expRes: a single ExpResult object containing the result to be validated
    or a list of ExpResult objects containing the txname.
    :param txname: a TxName object containing the txname to be validated
    :param slhadir: folder containing the SLHA files corresponding to txname
    or the .tar file containing the SLHA files.
    :param kfactor: optional global k-factor value to re-scale 
                    all theory prediction values
    :param recycle_data: use python dictionary files, if they exist
    
    :return: Nested dictionary with the wrongness factor for each experimental
             result/plot.
    """    
    if not isinstance(expRes,list): expResList = [expRes]
    else: expResList = expRes
    ret = {}
    for exp in expResList:
        tgraphs = getExclusionCurvesFor(exp,txname=txname)
        if not tgraphs or not tgraphs[txname]:
            continue
        else:
            tgraphs = tgraphs[txname] 
        axes = []
        for tgraph in tgraphs:
            ax = tgraph.GetName()
            ax = ax.replace('exclusion_',"")
            axes.append(ax)
    
        if not axes: continue
        ID=exp.getValuesFor('id')[0]
        ret = { ID : {}}
        for ax in axes: 
            ret[ID][ax]= validatePlot(exp,txname,ax,slhadir, 
                    kfactor=kfactor, recycle_data = recycle_data ) 
    return ret ## return agreement factors
<<<<<<< HEAD
 
def validateExpRes(expRes,slhaDir,kfactorDict=None):
=======
    
    
def validateExpRes(expRes,slhaDir,kfactorDict=None, recycle_data = False ):
>>>>>>> b91bcefdbba9caab401aeeb893193ec93e0cd888
    """
    Creates a ValidationPlot for each txname appearing in expRes and 
    each plane/axes appearing in txname and saves the output.
    
    :param expRes: a ExpResult object containing the result to be validated    
    :param slhaDir: Location of the slha folder containing the    
                    txname.tar files or the ./txname folders (i. e. ../slha/)
    :param kfactorDict: optinal k-factor dictionary for the txnames 
                        (i.e. {'TChiWZ' : 1.2, 'T2tt' : 1.,...})
                        If not define will assume k-factors = 1 for txnames.
    :param recycle_data: use python dictionary files, if they exist
    """    

    #Get all exclusion curves appearing in sms.root:
    curves = getExclusionCurvesFor(expRes)
    ret={}
    for txname in curves:
        slhadir = os.path.join(slhaDir,txname)
        if not os.path.isdir(slhadir):
            slhadir = os.path.join(slhaDir,txname+'.tar')
            if not os.path.isfile(slhadir):
                logger.error("SLHA files for %s not found in %s" %(txname,slhadir))
                continue
        if not kfactorDict or not txname in kfactorDict:
            kfactor=1.
        else: kfactor = kfactorDict[txname]
        ret[txname]= validateTxName(expRes,txname,slhadir,kfactor,recycle_data)
        
    return ret
