#!/usr/bin/env python

"""
.. module:: plotProducer
   :synopsis: Main classes and methods for producing several validation plots

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
from validationObjs  import ValidationPlot
from plottingFuncs import getExclusionCurvesFor

logger.setLevel(level=logging.DEBUG)

def getExpIdFromPath ():
    """ get experimental id from path """
    ret=os.getcwd()
    ret=ret.replace("/validation","")
    ret=ret.replace("-eff","")
    ret=ret[ret.rfind("/")+1:]
    return ret

def getDatasetIdsFromPath(dir="../"):
    """ determine the datasetids from the path"""
    import os
    files=os.listdir(dir)
    datasetids=[]
    for f in files:
        if not f in [ "globalInfo.txt", "validation", "sms.root", "convert.py", "old", "smodels.log", "orig", ".DS_Store" ]:
       ##     f=f.replace("data-","").replace("ana","ANA").replace("cut","CUT" )
            if f=="data": f=None
            datasetids.append  ( f )
    return datasetids


def validatePlot(expRes,txname,axes,slhadir,kfactor=1.):
    """
    Creates a ValidationPlot object and saves its output.
    
    :param expRes: a ExpResult object containing the result to be validated
    :param txname: a TxName object containing the txname to be validated
    :param axes: the axes string describing the plane to be validated
     (i.e.  2*Eq(mother,x),Eq(lsp,y))
    :param slhadir: folder containing the SLHA files corresponding to txname
    or the .tar file containing the SLHA files.
    :param kfactor: optional global k-factor value to re-scale 
                    all theory prediction values
    """

    #Get exclusion curve for expRes:
    curve = getExclusionCurvesFor(expResult=expRes,txname=txname,axes=axes)
    if not curve:
        return False

    logger.info("Generating validation plot for " + expRes.getValuesFor('id')[0]
                +", "+txname+", "+axes)        
    valPlot = ValidationPlot(expRes,txname,axes,kfactor=kfactor)
    valPlot.setSLHAdir(slhadir)
    valPlot.getData()
    valPlot.getPlot()
    valPlot.savePlot()
    valPlot.saveData()
    logger.info("Validation plot done.")
    return valPlot.computeAgreementFactor() # return agreement factor
    
def validateTxName(expRes,txname,slhadir,kfactor=1.):
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
    
    :return: Nested dictionary with the wrongness factor for each experimental
             result/plot.
    """    
    if not isinstance(expRes,list): expResList = [expRes]
    else: expResList = expRes
    ret = {}
    for exp in expResList:
        tgraphs = getExclusionCurvesFor(exp,txname=txname)[txname]
        if not tgraphs:
            continue
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
                                                          kfactor=kfactor) 
    return ret ## return agreement factors
    
    
def validateExpRes(expRes,slhaDir,kfactorDict=None):
    """
    Creates a ValidationPlot for each txname appearing in expRes and 
    each plane/axes appearing in txname and saves the output.
    
    :param expRes: a ExpResult object containing the result to be validated    
    :param slhaDir: Location of the slha folder containing the    
                    txname.tar files or the ./txname folders (i. e. ../slha/)
    :param kfactorDict: optinal k-factor dictionary for the txnames 
                        (i.e. {'TChiWZ' : 1.2, 'T2tt' : 1.,...})
                        If not define will assume k-factors = 1 for txnames.
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
        ret[txname]= validateTxName(expRes,txname,slhadir,kfactor)
        
    return ret

def validateDatabase(database,slhaDir):
    """
    Creates a ValidationPlot for each expRes/txname/axes appering in the database
    and saves the output.
   
    :param database: a Database object
    :param slhaDir: Location of the slha folder containing the
    txname.tar files or the ./txname folders (i. e. ../slha/)
    """  
    ret={}
    for expRes in database.getExpResults(): 
        ret[expRes.id]= validateExpRes(expRes,slhaDir)
        
    return ret
