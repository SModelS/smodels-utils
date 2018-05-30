#!/usr/bin/python3

""" Identify a good example for how to combine results. """


import sys, numpy
import colorama
from math import sqrt
from smodels.experiment.databaseObj import Database
import IPython
import pickle
import tempfile
import os

# dbname="http://smodels.hephy.at/database/official113"
dbname="/home/walten/git/smodels-database"
d=Database( dbname, subpickle=True )
#ids= ['CMS-PAS-SUS-16-052' ]
ids= ['CMS-SUS-16-050' ]
if len(sys.argv)>1:
    ids = [ sys.argv[1] ]
    if sys.argv[1]=="-h" or sys.argv[1]=="--help":
        print ( "usage: findAggregates.py [CMS-PAS-SUS-16-052|CMS-SUS-16-050]" )
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

cov = result.globalInfo.covariance 
n=len(cov)
# n=2

pairs = {}

for i in range(n):
    for j in range(i+1,n):
        cor = cov[i][j]/sqrt(cov[i][i]*cov[j][j] )
        # print ( "cov[%d,%d]=%f" % ( i+1,j+1, cor) )
        pairs[cor] = [i+1,j+1] 

corrs = list(pairs.keys())
corrs.sort(reverse=True)

done = []
aggs = []
    
frac=.4

for k in corrs:
    #if k < .1:
    #    break
    v = pairs[k]
    print ( "%.2f: %s" % ( k, v ) )
    if v[0] in done and v[1] in done:
        ## all taken care of
        continue
    if not v[0] in done and not v[1] in done:
        if k > frac:
            ## a virigin pair. add as new aggregate region
            done.append ( v[0] )
            done.append ( v[1] )
            aggs.append ( v )
        else:
            done.append ( v[0] )
            done.append ( v[1] )
            aggs.append ( [ v[0] ] )
            aggs.append ( [ v[1] ] )
    if v[0] in done and not v[1] in done:
        if k > frac:
            ## v0 is already in a region. lets add v1.
            for a in aggs:
                if v[0] in a:
                    ## lets assume yes
                    done.append ( v[1] )
                    a.append ( v[1] )
        else: ## we cant add v1
            done.append ( v[1] )
            aggs.append ( [ v[1] ] )
    if v[1] in done and not v[0] in done:
        if k > frac:
            ## v0 is already in a region. can we add v1?
            for a in aggs:
                if v[1] in a:
                    ## lets assume yes
                    done.append ( v[0] )
                    a.append ( v[0] )
        else:
            done.append ( v[0] )
            aggs.append ( [ v[0] ] )

for a in aggs:
    a.sort()
aggs.sort()
        
c=set()
for i in aggs: 
    for j in i: c.add ( j )
print ( "%d regions -> %d agg regions: %s" % ( len(c), len(aggs), aggs ) )
