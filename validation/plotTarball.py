#!/usr/bin/python

import sys,os,shutil

home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))

from smodels.experiment.databaseObj import Database
from plottingFuncs import getExclusionCurvesFor
import glob, pyslha
import ROOT
import commands,tempfile



txname="TSlepSlep"

tarball="../slha/%s.tar" % txname
tempdir = tempfile.mkdtemp(prefix=os.getcwd()+'/')
commands.getoutput ( "tar xvf %s -C %s" %(tarball,tempdir) )
files=glob.iglob( "%s/%s_*.slha" %(tempdir,txname) )

xM = 1000011
yM = 1000022
zM = None

if zM is None:
    gr = ROOT.TGraph()  #2-D grid
else:
    gr = ROOT.TGraph2D() #3-D grid
    
gr.SetMarkerSize(1)
gr.SetMarkerStyle(20)


for (ifile,f) in enumerate(files):
    pyfile=pyslha.readSLHAFile ( f )
    masses=pyfile.blocks["MASS"]
    xmass=masses[xM]
    ymass=masses[yM]
    if zM:
        zmass=masses[zM]
        gr.SetPoint(ifile,xmass,ymass,zmass)
    else:
        gr.SetPoint(ifile,xmass,ymass)

print tempdir
shutil.rmtree(tempdir)
print gr.GetN()
gr.GetXaxis().SetTitle("%s mass (GeV)" %str(xM))
gr.GetYaxis().SetTitle("%s mass (GeV)" %str(yM))
if zM:
    gr.GetZaxis().SetTitle("%s mass (GeV)" %str(zM))
    
gr.Draw("AP")

wait = raw_input("Press any key to exit")
# database = Database("../../smodels-database/")
# listOfExpRes = database.getExpResults( txnames=[ txname ] )
# cont=[]
# if type(listOfExpRes)!=list:
#     listOfExpRes=[listOfExpRes]
# for expResult in listOfExpRes:
#     axes=expResult.getValuesFor("axes")
#     tgraph=getExclusionCurvesFor ( expResult,txname,axes[0])
#     tgraph[txname][0].Draw("same")
#     cont.append ( tgraph)
# 
# ROOT.c1.Print("check_%s.pdf" % txname )
