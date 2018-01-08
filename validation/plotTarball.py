#!/usr/bin/python

import sys,os

home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))

from smodels.experiment.databaseObj import Database
import pyslha,tarfile
import ROOT



txname="T6bbWW"

tarball="../slha/%s.tar.gz" % txname
tar = tarfile.open(tarball,"r:gz")
files = [f for f in tar.getnames() if '.slha' in f]

xM = 1000006
yM = 1000022
zM = 1000024

if zM is None:
    gr = ROOT.TGraph()  #2-D grid
else:
    gr = ROOT.TGraph2D() #3-D grid
    
gr.SetMarkerSize(1)
gr.SetMarkerStyle(20)


for (ifile,f) in enumerate(files):
    fobj = tar.extractfile(f)
    pyfile=pyslha.readSLHA(fobj.read())
    fobj.close()
    masses=pyfile.blocks["MASS"]
    xmass=masses[xM]
    ymass=masses[yM]
    if zM:
        zmass=masses[zM]
        gr.SetPoint(ifile,xmass,ymass,zmass)
    else:
        gr.SetPoint(ifile,xmass,ymass)


print gr.GetN()

gr.GetYaxis().SetTitleFont(132)
gr.GetYaxis().SetTitleSize(0.04)
gr.GetYaxis().CenterTitle(True)
gr.GetYaxis().SetTitleOffset(2.)
gr.GetXaxis().SetTitleFont(52)
gr.GetXaxis().SetTitleSize(0.04)
gr.GetXaxis().CenterTitle(True)
gr.GetXaxis().SetTitleOffset(2.)
gr.GetYaxis().SetLabelFont(132)
gr.GetXaxis().SetLabelFont(132)
gr.GetYaxis().SetLabelSize(0.05)
gr.GetXaxis().SetLabelSize(0.05)
if zM:
    gr.GetZaxis().SetTitleFont(132)
    gr.GetZaxis().SetTitleSize(0.04)
    gr.GetZaxis().CenterTitle(True)
    gr.GetZaxis().SetTitleOffset(2.)
    gr.GetZaxis().SetLabelFont(132)
    gr.GetZaxis().SetLabelSize(0.05)

plane = ROOT.TCanvas("c1", "c1",0,0,800,600)    
plane.SetLeftMargin(0.17)
plane.SetBottomMargin(0.16)
plane.SetRightMargin(0.2)
plane.cd()
gr.GetXaxis().SetTitle("%s mass (GeV)" %str(xM))
gr.GetYaxis().SetTitle("%s mass (GeV)" %str(yM))
if zM:
    gr.GetZaxis().SetTitle("%s mass (GeV)" %str(zM))

gr.SetTitle(tarball)
gr.Draw("P")





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
