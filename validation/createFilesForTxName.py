#!/usr/bin/env python

"""
.. module:: createFilesForTxName.py
   :synopsis: create SLHA files for a given txname.

"""

#Import basic functions (this file must be run under the installation folder)
import sys,os,logging
sys.path.insert(0,"../../smodels")
from smodels.experiment.databaseObjects import DataBase
from smodels.experiment.txnameObject import logger as tl
tl.setLevel(level=logging.ERROR)

#Set the address of the database folder
database = DataBase("../../smodels-database/")
# database = DataBase("/home/walten/git/branches/smodels-database/")

from plottingFuncs import getExclusionCurvesFor
import plotRanges
import slhaCreator


def main( txname= "T6bbWW" ):
    """
    Main program. Displays basic use case.

    """
    # first remove old slha files
    cmd = "rm -f %s_??????.slha" % ( txname )
    import commands
    commands.getoutput ( cmd )
    onshell=True
    offshell=False
    if txname[-3:]=="off":
        onshell=False
        offshell=True
    templatefile = "../slha/templates/%s.template" % txname
    # Load all analyses from database
    listOfExpResOn = database.getExpResults( txnames=[ txname.replace("off","") ] )
    onshell_constraint=""
    if type(listOfExpResOn)!=list:
        listOfExpResOn=[listOfExpResOn]
    for expResult in listOfExpResOn:
        onshell_constraint= expResult.getValuesFor("constraint") 
#         print "constraint=",onshell_constraint
        

    listOfExpRes = database.getExpResults( txnames=[ txname ], datasetIDs = [None] )

    if type(listOfExpRes)!=list:
        listOfExpRes=[listOfExpRes]

    print "experimental results",listOfExpRes

    slhafiles = []
    tgraphs = {}
    txnameObjs = []

    # Compute the theory predictions for each analysis
    for expResult in listOfExpRes:
        txnameList = expResult.getTxNames()
        if len(txnameList) != 1:
            print " %i Txname(s) found!" %len(txnameList)
            print [tx.txname for tx in txnameList]
            sys.exit()
        else: 
            txnameObj = txnameList[0]        
            txnameObjs.append ( txnameObj )
#         print('\n',expResult)
#         print(expResult.path)
        axes=txnameObj.getInfo("axes")
        if type(axes)==str:
            axes=[axes]
        for naxes in axes:
#             print "naxes=",naxes
            tgraph=getExclusionCurvesFor(expResult,txname,naxes)
            print expResult
            print tgraph.keys(),tgraph.values()[0][0].GetN()
#             print "tgraph=",tgraph
            if not tgraph:
                continue
            if not naxes in tgraphs:
                tgraphs[naxes]=[]
            tgraphs[naxes].append(tgraph[txname][0])

    for (axes,ntgraph) in tgraphs.items():
        print "--=----------------------"
        pts = plotRanges.getPoints ( ntgraph, txnameObjs, axes, onshell_constraint, onshell, offshell )
        print "axes=",axes
        print "txname=",txname
        print "onshell_constraint=",onshell_constraint
#         print "points=",pts
        print "len(pts)=",len(pts)
        continue
        # flatpts = plotRanges.mergeListsOfListsOfPoints ( pts )
        if len(pts)==0:
            continue
        tempf=slhaCreator.TemplateFile ( templatefile,axes )
        slhafiles += tempf.createFilesFor ( pts, massesInFileName=True )


    import commands
    cmds=commands.getoutput ( "tar cvf %s.tar %s_*.slha" % ( txname, txname ) )
    print cmds
    #Remove SLHA files
    for f in slhafiles: 
        if os.path.exists ( f ): os.remove(f)
    


if __name__ == '__main__':
    if len(sys.argv)>1:
        txname=sys.argv[1]
    main( txname )
