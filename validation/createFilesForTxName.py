#!/usr/bin/env python

"""
.. module:: createFilesForTxName.py
   :synopsis: create SLHA files for a given txname.

"""

#Import basic functions (this file must be run under the installation folder)
import sys,os
sys.path.insert(0,"../../smodels")
from smodels.experiment.databaseObjects import DataBase

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
    onshell=True
    offshell=False
    if txname[-3:]=="off":
        onshell=False
        offshell=True
    templatefile = "../slha/templates/%s.template" % txname
    # Load all analyses from database
    listOfExpRes = database.getExpResults( txnames=[ txname ], datasetIDs=[None] )

    if type(listOfExpRes)!=list:
        listOfExpRes=[listOfExpRes]

    slhafiles = []
    tgraphs = {}

    # Compute the theory predictions for each analysis
    for expResult in listOfExpRes:
        print('\n',expResult)
        print(expResult.path)
        axes=expResult.getValuesFor("axes")
        constraint= expResult.getValuesFor("constraint") 
        print "constraint=",constraint
        #  constraint="[[['t+']],[['t-']]]"
        if type(axes)==str:
            axes=[axes]
        for naxes in axes:
            print "naxes=",naxes
            tgraph=getExclusionCurvesFor ( expResult,txname,naxes)
            print "tgraph=",tgraph
            if not tgraph:
                continue
            if not naxes in tgraphs:
                tgraphs[naxes]=[]
            tgraphs[naxes].append ( tgraph[txname][0] )
            #print "get points"
            #pts = plotRanges.getPoints ( tgraph[txname][0], txname, naxes, constraint, onshell, offshell )
            #print "got points"
            #if not naxes in points:
            #    points[naxes]=[]
            #points[naxes].append ( pts )
    for (axes,tgraphs) in tgraphs.items():
        pts = plotRanges.getPoints ( tgraphs, txname, naxes, constraint, onshell, offshell )
        print "axes=",axes
        print "points=",pts
        # flatpts = plotRanges.mergeListsOfListsOfPoints ( pts )
        if len(pts)==0:
            continue
        print "for",axes,"get",pts[-1]
        tempf=slhaCreator.TemplateFile ( templatefile,axes )
        slhafiles += tempf.createFilesFor ( pts )


    import commands
    cmds=commands.getoutput ( "tar cvf %s.tar %s_*.slha" % ( txname, txname ) )
    print cmds
    #Remove SLHA files
    for f in slhafiles: os.remove(f)
    


if __name__ == '__main__':
    txname="T2tt"
    if len(sys.argv)>1:
        txname=sys.argv[1]
    main( txname )
