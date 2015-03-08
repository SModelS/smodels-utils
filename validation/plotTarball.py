#!/usr/bin/python

from smodels.experiment.databaseObjects import DataBase
from plottingFuncs import getExclusionCurvesFor
import os, glob
from smodels.tools import modpyslha
import ROOT
import commands

txname="T2tt"

tarball="%s.tar" % txname
commands.getoutput ( "tar xvf %s" % tarball )
files=glob.iglob( "%s_*.slha" % txname )

gr=ROOT.TGraph()
gr.SetMarkerSize(1)
gr.SetMarkerStyle(23)

for (ctr,f) in enumerate(files):
    pyfile=modpyslha.readSLHAFile ( f )
    masses=pyfile.blocks["MASS"]
    stopmass=masses[1000006]
    lspmass=masses[1000022]
    gr.SetPoint(ctr,stopmass,lspmass)

gr.Draw("AP")

database = DataBase("../../smodels-database/")
listOfExpRes = database.getExpResults( txnames=[ txname ] )
cont=[]
if type(listOfExpRes)!=list:
    listOfExpRes=[listOfExpRes]
for expResult in listOfExpRes:
    axes=expResult.getValuesFor("axes")
    tgraph=getExclusionCurvesFor ( expResult,txname,axes[0])
    tgraph[txname][0].Draw("same")
    cont.append ( tgraph)

ROOT.c1.Print("check_%s.png" % txname )
