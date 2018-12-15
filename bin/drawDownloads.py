#!/usr/bin/python3

import scipy.stats
import ROOT
try:
    import commands as C
except:
    import subprocess as C
a=C.getoutput ( "tac ../log/pip_backup.log > ./.reverse.log" )

ROOT.gStyle.SetOptStat(0000)
Min,Max = 0.,400.

t=ROOT.TTree()

n=t.ReadFile( "./.reverse.log", "d/C[12]:p/D", ",")

hi = ROOT.TH2F ( "h", "SModelS: pip downloads", n, 0, n, 10, Min, Max )
hi.SetYTitle ( "Downloads per day" )
xa=hi.GetXaxis()
xa.SetTickSize(.007)
lastdate=""
values=[]
for i in range(1,n):
    t.GetEntry(i)
    y=t.GetLeaf("p").GetValue()
    values.append ( y )

def releases():
    f=open("../log/releases.log","r")
    lines=f.readlines()
    f.close()
    ret=[]
    for line in lines:
        ret.append ( line.split(",") )
    return ret

binlabels={}
for i in range(1,n):
    t.GetEntry(i)
    d = t.GetLeaf("d").GetValueString()
    date = d.replace("201","'1")
    binlabels[d]=i
    if i % 5 != 0:
        continue
    if lastdate != date:
        xa.ChangeLabel ( i, 90. )
        xa.SetBinLabel( i, date )
        lastdate=date

hi.Draw()
t.SetLineWidth(3)
t.Draw("p:d","","Lsame" )
for d,ver in releases():
    if "post" in ver:
        continue
    if d in binlabels.keys():
        Bin = binlabels[d]
        # print ( "release %s at %s" % ( ver, Bin ) )
        l=ROOT.TLine ( Bin, Min, Bin, Max )
        l.SetLineColor ( ROOT.kRed )
        l.SetLineWidth( 2 )
        l.SetLineStyle ( 2 )
        l.Draw()
        pos=.8
        t=ROOT.TText ( Bin, pos*Max, ver )
        t.SetTextColor ( ROOT.kRed )
        t.SetTextSize(.04)
        t.SetTextAngle(90.)
        t.Draw()
        values.append ( (l,t) )
ROOT.c1.Modified()

ROOT.c1.Print("downloads.png")
ROOT.c1.Print("../../smodels.github.io/logos/downloads.png")
