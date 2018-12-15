#!/usr/bin/python3

import scipy.stats
import ROOT
try:
    import commands as C
except:
    import subprocess as C
a=C.getoutput ( "tac ../log/pip_backup.log > ./.reverse.log" )

ROOT.gStyle.SetOptStat(0000)

t=ROOT.TTree()

n=t.ReadFile( "./.reverse.log", "d/C[12]:p/D", ",")

hi = ROOT.TH2F ( "h", "pip downloads", n, 0, n, 10, 0., 500. )
hi.SetYTitle ( "Downloads per day" )
xa=hi.GetXaxis()
lastdate=""
gr = ROOT.TGraph(n)
gr.SetLineColor(ROOT.kBlue) 
values=[]
for i in range(n):
    t.GetEntry(i)
    y=t.GetLeaf("p").GetValue()
    values.append ( y )

def smooth ( values, idx ):
    ret,w=0.,0.
    r=40
    for i in range(idx-r,idx+r):
        if i<0: continue
        if i>=len(values): continue
        tmp = scipy.stats.norm.pdf(i,idx,r)
        w+=tmp
        ret+=tmp*values[i]
    return ret/w


for i in range(n):
    t.GetEntry(i)
    gr.SetPoint(i-1,float(i),smooth(values,i))
    if i % 5 != 0:
        continue
    date = (t.GetLeaf("d").GetValueString()[0:12]).replace("201","'1")
    if lastdate != date:
        xa.SetBinLabel( i, date )
        lastdate=date

hi.Draw()

t.Draw("p:d","","Lsame" )
# gr.Draw("Csame")
ROOT.c1.Modified()

ROOT.c1.Print("downloads.png")
