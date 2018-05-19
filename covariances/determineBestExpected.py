#!/usr/bin/python3

""" Identify a good example for how to combine results. """


import sys, numpy, subprocess
from smodels.experiment.databaseObj import Database
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.theory.slhaDecomposer import decompose
import random
import IPython

dbname="http://smodels.hephy.at/database/official113"
dbname="/home/walten/git/smodels-database-test"
d=Database( dbname )
ids= ['CMS-SUS-16-050' ]
results=d.getExpResults( analysisIDs=ids )
result=results[0]

def getDatasets():
    datasets={}
    for i,ds in enumerate ( result.datasets ):
        print ( i, ds.dataId )
        datasets[i]=ds.dataId
    return datasets

def createFile ():
    topos=["T1tttt","T2tt"]
    random.shuffle ( topos )
    topo=topos[0]
    template="./template_%s.slha" % topo
    tempfile = "tmp.slha"
    glu_lim = { "T1tttt": [ 61.5, 2162. ] } 
    mgl=random.uniform(61.5,2162.)
    mstop=random.uniform(187.5,1162.5)
    mlsp = random.uniform(12.5,min(1612.,mgl-35. ))
    f=open(template,"r")
    lines=f.readlines()
    f.close()
    g=open(tempfile,"w")
    for line in lines:
        line=line.replace("MGLUINO","%s" % mgl )
        line=line.replace("MSTOP","%s" % mstop )
        line=line.replace("MGL","%s" % mgl )
        line=line.replace("MLSP","%s" % mlsp )
        g.write ( line )
    g.close()
    return topo,mgl,mstop,mlsp


def runSingleFile():
    slhafile = "tmp.slha"
    smstoplist = decompose ( slhafile )

    preds = theoryPredictionsFor ( result, smstoplist )
    if preds == None:
        return None
    for pred in preds:
        if pred.dataId() == "combined":
            continue
        return pred.dataId()

def main():
    subprocess.getoutput ( "cp results.txt results.bu" )
    datasets=getDatasets()
    sys.exit()
    g=open("results.txt","w")
    for i in range(5):
        topo,mgl,mstop,mlsp=createFile()
        Id=runSingleFile()
        print ( "one file:", Id )
        if Id != None:
            line="nr=%d; t='%s'; mgl=%.1f; mstop=%.1f; mlsp=%.1f; id='%s'\n" % ( i, topo, mgl, mstop, mlsp, Id ) 
            g.write ( line )
    g.close()

main()
