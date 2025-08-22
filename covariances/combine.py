#!/usr/bin/python3

""" Identify a good example for how to combine results. """


import sys, numpy
from smodels.experiment.databaseObj import Database
from smodels.matching.theoryPrediction import theoryPredictionsFor
from smodels.theory.slhaDecomposer import decompose

d=Database( "/home/walten/git/smodels-database" )
# T1bbbb: CMS-PAS-SUS-16-016 <-> CMS-SUS-12-028

slhafile = "./T1bbbb.slha" 

smstoplist = decompose ( slhafile )

print ( "Decomp", len(smstoplist) )

results=d.getExpResults( analysisIDs=['CMS-PAS-SUS-16-016', 'CMS-SUS-12-028' ], 
                         txnames = [ "T1bbbb" ] )

def combined95UL ( theorypreds ):
    """ compute the 95% CL upper limit for a combination of 
    theory predictions. """
    llhd=0.
    llhds=[]
    mu_v = numpy.arange ( 0., 5., .1 )
    for mu in mu_v:
        tmp=1.
        for p in theorypreds:
            tmp=tmp*p.llhd ( mu )
        llhds.append ( tmp )
    s=sum(llhds)
    for ctr,l in enumerate(llhds):
        llhds[ctr]=l/s

    return llhd

for r in results:
    preds = theoryPredictionsFor ( r, smstoplist )
    print ( r )
    for pred in preds:
        pred.computeStatistics()
        print ( pred.likelihood )
