#!/usr/bin/env python

"""
.. module:: Example
   :synopsis: Basic main file example for using SModelS.

"""

#Import basic functions (this file must be run under the installation folder)
import sys,os
sys.path.insert(0,"../../smodels")
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

def addQuotationMarks ( constraint ):
    """ [[[t+]],[[t-]]] -> [[['t+']],[['t-']]] """
    ret=""
    for i in range(len(constraint)):
        if constraint[i] == "[" and constraint[i+1] not in [ "[", "]" ]:
            ret+=constraint[i]+"'"
            continue
        if constraint[i] == "]" and constraint[i-1] not in [ "[", "]" ]:
            ret+="'" + constraint[i]
            continue
        ret+=constraint[i]
    return ret

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
    slhafiles = []

    # Compute the theory predictions for each analysis
    for expResult in listOfExpRes:
        print('\n',expResult)
        print(expResult.path)
        axes=expResult.getValuesFor("axes")
        constraint=addQuotationMarks ( expResult.getValuesFor("constraint") )
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
            print "get points"
            pts = plotRanges.getPoints ( tgraph[txname][0], txname, naxes, constraint, onshell, offshell )
            print "got points"
            if not naxes in points:
                points[naxes]=[]
            points[naxes].append ( pts )
    for (axes,pts) in points.items():
        print "axes=",axes
        flatpts = plotRanges.mergeListsOfListsOfPoints ( pts )
        print "for",axes,"get",flatpts[-1]
        tempf=slhaCreator.TemplateFile ( templatefile,axes )
        slhafiles += tempf.createFilesFor ( flatpts )

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
