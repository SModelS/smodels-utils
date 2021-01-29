#!/usr/bin/env python3

""" Identify a good example for how to combine results. """


import sys, numpy
import colorama
from math import sqrt
from smodels.experiment.databaseObj import Database
import IPython
import pickle
import tempfile
import os
import argparse


def useNames ( aggs, datasets ):
    ret = []
    for agg in aggs:
        tmp = []
        for i in agg:
            tmp.append ( datasets[i] )
        ret.append ( tmp )
    return ret

def main():
    ap = argparse.ArgumentParser( description= "find aggregate regions based on correlations." )
    ap.add_argument('-a','--analysis',help="name of analysis to discuss [CMS-SUS-16-050]",
                    default = "CMS-SUS-16-050", type=str )
    ap.add_argument('-c','--corr',help="correlation needed to cluster [.5]",
                    default = .5, type=float )
    ap.add_argument( '-t','--takeout',help="dont cluster these SRs", nargs="*",
                     type=int )
    ap.add_argument('-d','--database',help="path to database [../../smodels-database]",
                    default = "../../smodels-database", type=str )
    args = ap.parse_args()
    # dbname="http://smodels.hephy.at/database/official113"
    # dbname="/home/walten/git/smodels-database"
    # d=Database( dbname, subpickle=True )
    d=Database( args.database )

    if "52" in args.analysis:
        args.analysis = "CMS-PAS-SUS-16-052"
    if "50" in args.analysis:
        args.analysis = "CMS-SUS-16-050"
    ids = [ args.analysis ]
    results=d.getExpResults( analysisIDs=ids, dataTypes=["efficiencyMap"],
                             useNonValidated=True )
    result=results[0]

    def getDatasets():
        datasets={}
        for _,ds in enumerate ( result.datasets ):
            i=_ # +1
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
            pairs[cor] = [i,j] 
            # pairs[cor] = [i+1,j+1] 

    corrs = list(pairs.keys())
    corrs.sort(reverse=True)

    done = []
    aggs = []
    excls = []
        
    frac=args.corr

    if args.takeout != None:
        for i in args.takeout:
            done.append ( i )
            excls.append ( i )
            aggs.append ( [ i ] )

    for k in corrs:
        #if k < .1:
        #    break
        v = pairs[k]
        # print ( "%.2f: %s" % ( k, v ) )
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
            if k > frac and not v[1] in excls and not v[0] in excls:
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
            if k > frac and not v[0] in excls and not v[1] in excls:
                ## v1 is already in a region. can we add v0?
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
    # print ( "with names", useNames ( aggs, getDatasets() ) )

main()
