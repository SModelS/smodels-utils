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

logger.setLevel(level=logging.DEBUG)


def validatePlot(expRes,txname,axes,slhadir):
    """
    Creates a ValidationPlot object and saves its output.
    
    :param expRes: a ExpResult object containing the result to be validated
    :param txname: a TxName object containing the txname to be validated
    :param axes: the axes string describing the plane to be validated
     (i.e.  2*Eq(mother,x),Eq(lsp,y))
    :param slhadir: folder containing the SLHA files corresponding to txname
    """

    logger.info("Generating validation plot for " + expRes.getValuesFor('id') 
                +", "+txname.txname+", "+axes)        
    valPlot = ValidationPlot(expRes,txname,axes)
    valPlot.setSLHAdir(slhadir)
    valPlot.getData()
    valPlot.getPlot()
    valPlot.savePlot()
    logger.info("Validation plot done.")
    
def validateTxName(expRes,txname,slhadir):
    """
    Creates a ValidationPlot for each plane/axes appearing
    in txname and saves the output.
    
    :param expRes: a ExpResult object containing the result to be validated
    :param txname: a TxName object containing the txname to be validated
    :param slhadir: folder containing the SLHA files corresponding to txname
    """    

    axes = txname.getInfo('axes')
    if not axes: return False
    
    if isinstance(axes,list):
        for ax in axes: validatePlot(expRes,txname,ax,slhadir)
    else: validatePlot(expRes,txname,axes,slhadir)
    
def validateExpRes(expRes,slhaDict):
    """
    Creates a ValidationPlot for each txname appearing in expRes and 
    each plane/axes appearing in txname and saves the output.
    
    :param expRes: a ExpResult object containing the result to be validated    
    :param slhaDict: Dictionary containing the SLHA files corresponding to the
    txnames (i.e. {'T1bbbb' : ./T1bbbb/, 'T1ttt' : ./T1tttt/,...})
    """    

    #Get the txnames appearing in expRes:
    txstrs = expRes.getValuesFor('txname')  #List of strings
    for txstr in txstrs:
        if not txstr in slhaDict:
            logger.warning("The SLHA folder for %s has not been defined" % txstr)
            continue
        slhadir = slhaDict[txstr]
        txname = expRes.getTxnameWith({'txname' : txstr})
        validateTxName(expRes,txname,slhadir)
        
    return True

def validateDataBase(database,slhaDict):
    """
    Creates a ValidationPlot for each expRes/txname/axes appering in the database
    and saves the output.
   
    :param database: a DataBase object
    :param slhaDict: Dictionary containing the SLHA files corresponding to the
    txnames (i.e. {'T1bbbb' : ./T1bbbb/, 'T1ttt' : ./T1tttt/,...})
    """  
    
    for expRes in database.getExpResults(): validateExpRes(expRes,slhaDict)
        
    return True          
