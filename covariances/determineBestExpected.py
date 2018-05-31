#!/usr/bin/python3

""" Identify a good example for how to combine results. """


import sys, numpy, subprocess
from smodels.experiment.databaseObj import Database
from smodels.tools.xsecComputer import XSecComputer
from smodels.theory.crossSection import NLL, LO
from smodels.tools.physicsUnits import TeV
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.theory.slhaDecomposer import decompose
import random
import IPython
import pickle
import tempfile
import os

# dbname="http://smodels.hephy.at/database/official113"
dbname="/home/walten/git/smodels-database-test"
d=Database( dbname, subpickle=True )
ids= ['CMS-PAS-SUS-16-052' ]
# ids= ['CMS-SUS-16-050' ]
if len(sys.argv)>1:
    ids = [ sys.argv[1] ]
    if sys.argv[1]=="-h" or sys.argv[1]=="--help":
        print ( "usage: determineBestExpeced.py [CMS-PAS-SUS-16-052|CMS-SUS-16-050]" )
        sys.exit()
results=d.getExpResults( analysisIDs=ids, dataTypes=["efficiencyMap"],
                         useNonValidated=True )
result=results[0]

def getDatasets():
    datasets={}
    for _,ds in enumerate ( result.datasets ):
        i=_+1
#        print ( i, ds.dataInfo.dataId )
        datasets[i]=ds.dataInfo.dataId
        datasets[ ds.dataInfo.dataId ] = i
    return datasets

def createFile ():
    topos=[ "T2bbffff" ]
    if "16-050" in ids[0]:
        topos=["T1tttt","T2tt" ]
    random.shuffle ( topos )
    topo=topos[0]
    template="./template_%s.slha" % topo
    # tempfile = "tmp.slha"
    tfile = tempfile.mktemp(suffix=".slha")
    glu_lim = { "T1tttt": [ 1800., 2162. ], "T5tctc": [ 61.5, 2162.5 ], "T2tt": [ 1e6, 1e6 ],
                "T2bbffff": [1e6,1e6], "T4bbffff": [ 250., 800. ]  } 
    stop_lim = { "T2tt": [ 400.5, 1162.5 ], "T5tctc":  [], "T2bbffff": [350.,600], \
                 "T1tttt": [ 1e6, 1e6 ] }
    lsp_lim = { "T1tttt": [ 12.5, 1400. ], "T2tt": [ 12.5 , 662.5 ], "T2bbffff": [ 240., 720. ] }
    mgl = random.uniform( glu_lim[topo][0], glu_lim[topo][1] )
    mstop=random.uniform(  stop_lim[topo][0], stop_lim[topo][1] )
    mlsp = random.uniform( lsp_lim[topo][0], lsp_lim[topo][1] )
    if "16-052" in ids[0]:
        mlsp = random.uniform ( mstop - 80, mstop-10. )
    if "16-050" in ids[0]:
        mgl=random.uniform( glu_lim[topo][0], glu_lim[topo][1] )
        mstop=random.uniform( stop_lim[topo][0], stop_lim[topo][1] )
        mlsp = random.uniform( lsp_lim[topo][0], lsp_lim[topo][1] )
        if mstop < 900. and topo=="T2tt":
            mlsp = random.uniform ( mstop/2. - 100., mstop/2. + 100. )
        if topo == "T1tttt" and mgl < 1800.:
            mlsp = random.uniform ( 900., 1300. )
    f=open(template,"r")
    lines=f.readlines()
    f.close()
    g=open(tfile,"w")
    for line in lines:
        line=line.replace("MGLUINO","%s" % mgl )
        line=line.replace("MSTOP","%s" % mstop )
        line=line.replace("MGL","%s" % mgl )
        line=line.replace("MLSP","%s" % mlsp )
        g.write ( line )
    g.close()
    return topo,mgl,mstop,mlsp,tfile


def runSingleFile( slhafile ):
    # slhafile = "tmp.slha"
    # print ( "now computing cross sections for %s" % slhafile )
    computer = XSecComputer ( LO, 10000, 8 )
    sqrts = [ 8, 13 ]
    computer.computeForOneFile ( sqrtses = sqrts, inputFile = slhafile,\
            unlink = True, lOfromSLHA = False, tofile=True )
    smstoplist = decompose ( slhafile )
    preds = theoryPredictionsFor ( result, smstoplist, useBestDataset=False, 
                                   combinedResults=False )
    if preds == None:
        return None
    dpreds={}
    for pred in preds:
        if pred.dataType() == "upperLimit":
            continue
        r=int(pred.getRValue(expected=True)*10**6)
        dpreds[r]=pred.dataId()
    os.unlink ( slhafile )
    return dpreds

def main():
    subprocess.getoutput ( "cp %s.txt .%s.bu" % ( ids[0], ids[0] ) )
    subprocess.getoutput ( "cp %s.pcl .%s.pcl.bu" % ( ids[0], ids[0] ) )
    datasets=getDatasets()
    #print ( datasets ) 
    #sys.exit()
    g=open("%s.txt" % ids[0],"w")
    g2=open("%s.pcl" % ids[0],"wb")
    i=0
    while True:
        topo,mgl,mstop,mlsp,tfile=createFile()
        preds=runSingleFile(tfile)
        D={ "nr": i, "t": topo, "mgl": mgl, "mstop": mstop, "mlsp": mlsp }
        if preds==None:
            print ( "skip", topo, mgl, mstop, mlsp )
            continue
        keys = list ( set ( preds.keys() ) )
        keys.sort( reverse=True )
        sid=""
        first_n = 20
        for ctr,k in enumerate(keys[:first_n]):
            sid+="id%d='%s'; r%d=%.2f; n%d=%d; " % ( ctr, preds[k], ctr, float(k)/10**6, ctr, datasets[preds[k]] )
            D["r%d" % ctr]= float(k)/10**6
            D["n%d" % ctr] = datasets[preds[k]]
            D["id%d" % ctr] = preds[k] 
        sid=sid[:-2]
        print ( "file %d, topo=%s, m=%d,%d,%d -> %s" % ( i, topo, mgl,mstop, mlsp, keys[:first_n] ) )
        line="X: nr=%d; t='%s'; mgl=%.1f; mstop=%.1f; mlsp=%.1f; %s.\n" % ( i, topo, mgl, mstop, mlsp, sid ) 
        g.write ( line )
        g.flush()
        pickle.dump ( D, g2 )
        i+=1
        if i>=1000:
            break
    g2.close()
    g.close()

main()
