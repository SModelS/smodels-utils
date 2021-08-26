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
import cov_helpers


def useNames ( aggs, datasets ):
    ret = []
    for agg in aggs:
        tmp = []
        for i in agg:
            tmp.append ( datasets[i] )
        ret.append ( tmp )
    return ret

def oneIndex ( aggs ):
    """ move all from 0-indexed to 1-indexed, i.e. add one to all elements """
    ret = []
    for a in aggs:
        tmp = []
        for i in a:
            # tmp.append ( "SR%d" % ( i+1 ) )
            tmp.append ( i+1 )
        ret.append ( tmp )
    return ret

def checkIfToAdd ( index : int, agg : list, frac : float, corrmatrix : list ):
    """ check if to add index to aggregation list agg, 
    :param index: the index to be added
    :param agg: list of aggregated indices
    :param frac: threshold on correlation, aggregate if all correlations are above it
    :param corrmatrix: correlation matrix to look up the correlations
    """
    # a minimum spanning tree is implemented as follows:
    return True

    # print ( f"shall we add {index} to {agg}?" )
    # print ( f"covs are: {[ corrmatrix[ index ][x] for x in agg ] }" ) 
    ## for now we implement a maximum spanning tree, i.e. add index only to agg
    ## if *all* correlations are above threshold
    allAbove = True
    for x in agg:
        corr = corrmatrix[ index ][x]
        if corr < frac:
            allAbove = False
            break
    return allAbove

def main():
    ap = argparse.ArgumentParser( description= "find aggregate regions based on correlations." )
    ap.add_argument('-a','--analysis',help="name of analysis to discuss [CMS-SUS-19-006-ma5]",
                    default = "CMS-SUS-19-006-ma5", type=str )
    ap.add_argument('-c','--corr',help="correlation needed to cluster [.5]",
                    default = .5, type=float )
    ap.add_argument( '-t','--takeout',help="dont cluster these SRs", nargs="*",
                     type=int )
    ap.add_argument( '-d','--drop',help="drop these SRs", nargs="*",
                     type=int )
    ap.add_argument('-D','--database',help="path to database [../../smodels-database]",
                    default = "../../smodels-database", type=str )
    args = ap.parse_args()
    # dbname="http://smodels.hephy.at/database/official113"
    # dbname="/home/walten/git/smodels-database"
    # d=Database( dbname, subpickle=True )
    print ( "[findAggregates.py] instantiating database ", end="...", flush=True )
    d=Database( args.database )
    print ( "done." )

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
    corrmatrix = cov_helpers.computeCorrelationMatrix ( cov )
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

    if args.drop != None:
        for i in args.drop:
            done.append ( i-1 )

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
                ## a virgin pair. add as new aggregate region
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
                for agg in aggs:
                    if v[0] in agg and checkIfToAdd ( v[1], agg, frac, corrmatrix ):
                        ## lets assume yes
                        done.append ( v[1] )
                        agg.append ( v[1] )
            else: ## we cant add v1
                done.append ( v[1] )
                aggs.append ( [ v[1] ] )
        if v[1] in done and not v[0] in done:
            if k > frac and not v[0] in excls and not v[1] in excls:
                ## v1 is already in a region. can we add v0?
                for agg in aggs:
                    if v[1] in agg and checkIfToAdd ( v[0], agg, frac, corrmatrix ):
                        done.append ( v[0] )
                        agg.append ( v[0] )
            else:
                done.append ( v[0] )
                aggs.append ( [ v[0] ] )

    for a in aggs:
        a.sort()
    aggs.sort()
            
    c=set()
    for i in aggs: 
        for j in i: c.add ( j )
    oaggs = oneIndex ( aggs )
    print ( "%d regions -> %d agg regions: %s" % ( len(c), len(aggs), oaggs ) )
    print ( "largest aggregation has %d elements" % ( max( [ len(x) for x in aggs ] ) ) )
    # print ( "with names", useNames ( aggs, getDatasets() ) )

main()
