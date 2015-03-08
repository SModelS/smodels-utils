#!/usr/bin/env python

"""
.. module:: Example
   :synopsis: Basic main file example for using SModelS.

"""

#Import basic functions (this file must be run under the installation folder)
import sys
from smodels.theory import slhaDecomposer
from smodels.theory import lheDecomposer
from smodels.tools.physicsUnits import fb, GeV
from smodels.theory.theoryPrediction import theoryPredictionsFor
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
    listOfExpRes = database.getExpResults( txnames=[ txname ] )

    if type(listOfExpRes)!=list:
        listOfExpRes=[listOfExpRes]

    points={}

    # Compute the theory predictions for each analysis
    for expResult in listOfExpRes:
        print('\n',expResult)
        print(expResult.path)
        axes=expResult.getValuesFor("axes")
        constraint=expResult.getValuesFor("constraint")
        print "constraint=",constraint
        constraint="[[['t+']],[['t-']]]"
        if type(axes)==str:
            axes=[axes]
        for naxes in axes:
            print "naxes=",naxes
            tgraph=getExclusionCurvesFor ( expResult,txname,naxes)
            pts = plotRanges.getPoints ( tgraph[txname][0], txname, naxes, constraint, onshell, offshell )
            if not naxes in points:
                points[naxes]=[]
            points[naxes].append ( pts )
    for (axes,pts) in points.items():
        print "axes=",axes
        flatpts = plotRanges.mergeListsOfListsOfPoints ( pts )
        print "for",axes,"get",flatpts[-1]
        tempf=slhaCreator.TemplateFile ( templatefile,axes, constraint )
        slhafiles = tempf.createFilesFor ( flatpts )

    import commands
    cmds=commands.getoutput ( "tar cvf %s.tar %s_*.slha" % ( txname, txname ) )
    print cmds




if __name__ == '__main__':
    txname="T2tt"
    if len(sys.argv)>1:
        txname=sys.argv[1]
    main( txname )
