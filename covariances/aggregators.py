#!/usr/bin/env python3

""" methods revolving around aggregations """


import sys, numpy
import colorama
from math import sqrt
from smodels.experiment.databaseObj import Database
from smodels_utils.helper import various
import IPython
import pickle
import tempfile
import os
import argparse
import cov_helpers

def getDatasets( result, addReverse = True ):
    """ given an experimental result, return datasets and possibly 
        dictionary of comments 
    :param addReverse: if True, then also add reverse lookup
    """
    datasets,comments={},{}
    for _,ds in enumerate ( result.datasets ):
        i=_ + 1
        datasets[i]=ds.dataInfo.dataId
        comments[i]=ds.dataInfo.comment
        if addReverse:
            datasets[ ds.dataInfo.dataId ] = i
    return datasets, comments

def retrieve ( fname ):
    """ get a dictionary of scores of signal regions, for one validation file
    """
    f=open(fname,"rt" )
    globalsParameter = {}
    exec ( f.read(), globalsParameter )
    f.close()
    ret = {}
    n = len ( globalsParameter["validationData"] )
    for pt in globalsParameter["validationData"]:
        if 'leadingsDSes' in pt: # typo in py file
            for idx,(k,v) in enumerate(pt["leadingsDSes"]):
                if not v in ret:
                    ret[v]=0
                ret[v]+=1000./(n*(idx+1)**2)
        if 'leadingDSes' in pt:
            for idx,(k,v) in enumerate(pt["leadingDSes"]):
                if not v in ret:
                    ret[v]=0
                ret[v]+=1000./(n*(idx+1)**2)
    return ret


def useNames ( aggs, datasets ):
    """ given lists of lists of indices, return lists of lists of
        dataset names """
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

def retrieveEMStats ( database, analysis ):
    """ see if we can retrieve data from a statsEM.py file.
        helpful for aggregation by name
    :param database: path to database
    :param analysis: ana id, e.g. CMS-SUS-19-006
    """
    path = various.getPathName ( database, analysis )
    path = os.path.join ( path, "orig", "statsEM.py" )
    if not os.path.exists ( path ):
        return {}
    f = open ( path, "rt" )
    txt = f.read()
    f.close()
    D = eval ( txt )
    return D

def obtainDictFromComment ( comment, analysis ):
    """ given the comment, obtain a dict with relevant analysis specific info,
        for clustering """
    D = {}
    if "CMS-SUS-19-006" in analysis:
        tokens = comment.split("_")
        D["jets"]= int ( tokens[1].replace("Njet","") )
        D["b"] = int ( tokens[2].replace("Nb","") )
        # D["HT"] = tokens[3].replace("HT","")
        # D["MHT"] = tokens[4].replace("MHT","")
    return D

def aggregateByNames ( database, analysis, drops, exclusives ):
    """ run the aggregator based on SR names
    :param database: path to database
    :param analysis: ana id, e.g. CMS-SUS-19-006
    :param drop: list of indices to drop from aggregation entirely
    :param exclusives: list of indices to not aggregate, but keep as individual
                       SRs
    """
    print ( "[findAggregates.py] instantiating database ", end="...", flush=True )
    d=Database( database )
    ids = [ analysis ]
    print ( "done." )
    aggs = []
    results=d.getExpResults( analysisIDs=ids, dataTypes=["efficiencyMap"],
                             useNonValidated=True )
    datasets, comments = getDatasets( results[0], addReverse=False )
    filtered = {}
    dropped = []
    for srnr, srname in datasets.items():
        if srnr in drops:
            dropped.append ( srnr )
            continue
        if srnr in exclusives:
            aggs.append ( [ srnr ] )
            continue
        filtered[srnr] = srname
    newaggs = []
    for srnr,srname in filtered.items():
        comment = obtainDictFromComment ( comments[srnr], analysis )
        hasAdded=False
        for aggctr, agg in enumerate ( newaggs ):
            for aggnr in agg:
                aggcomment = obtainDictFromComment ( comments[aggnr], analysis )
                if comment == aggcomment and not hasAdded:
                    newaggs[aggctr].append ( srnr )
                    hasAdded = True
                    
        if not hasAdded:
            newaggs.append ( [ srnr ] )
    aggs += newaggs
    return aggs, dropped

def aggregateByCorrs ( database, analysis, drop, exclusives, corr ):
    """ run the aggregator based on correlations
    :param database: path to database
    :param analysis: ana id, e.g. CMS-SUS-19-006
    :param drop: list of indices to drop from aggregation entirely
    :param exclusives: list of indices to not aggregate, but keep as individual
                    SRs
    :param corr: cut on correlation
    """
    print ( "[findAggregates.py] instantiating database ", end="...", flush=True )
    d=Database( database )
    print ( "done." )

    ids = [ analysis ]
    results=d.getExpResults( analysisIDs=ids, dataTypes=["efficiencyMap"],
                             useNonValidated=True )
    result=results[0]

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
    dropped = []

    frac=corr

    if drop != None:
        for i in drop:
            if type(i) in [ list, tuple ]:
                done.append ( i[0]-1 )
                dropped.append ( i[0] )
            if type(i) in [ int ]:
                done.append ( i-1 )
                dropped.append ( i )

    if exclusives != None:
        for i in exclusives:
            i0 = i
            if type(i) in [ list, tuple] :
                i0 = i[0]
            done.append ( i0-1 )
            excls.append ( i0-1 )
            aggs.append ( [ i0-1 ] )

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
    aggs = oneIndex ( aggs )

    return aggs, dropped

def describe ( aggs, dropped, n=None ):
    c=set()
    for i in aggs:
        for j in i: c.add ( j )
    # oaggs = oneIndex ( aggs )
    print ( "largest aggregation has %d elements" % ( max( [ len(x) for x in aggs ] ) ) )
    nregions, nexclusives = len(c), 0
    if n != None:
        nregions = n
    for i in aggs:
        if len(i)==1:
            nexclusives+=1
    print ( f"# {' '.join(sys.argv)}" )
    print ( "# %d regions -> %d agg regions with %d dropped and %d exclusives:" % \
            ( n, len(aggs), len(dropped), nexclusives ) )
    print ( "aggregate = %s" % ( aggs ) )
    # print ( "with names", useNames ( aggs, getDatasets() ) )

def check ( aggs, drops, n ):
    """ check if every SR is accounted for """
    errors = 0
    for i in range ( 1, n+1 ):
        #print ( f"[aggregators] SR{i}:", end=" " )
        accountedFor=0
        if i in drops:
            #print  ( "dropped." )
            accountedFor+=1
            continue
        for aggnr,agg in enumerate( aggs ):
            if i in agg:
                #print ( f"in {aggnr+1}" )
                accountedFor+=1
        if accountedFor == 0:
            #print ( "unaccounted for!!!" )
            errors += 1
        if accountedFor > 1:
            #print ( f"accounted for {accountedFor} times!!!" )
            errors += 1
    if errors > 0:
        print ( f"[aggregators] {errors} errors found." )

def main():
    """ redundant main function, see aggregate.py for usage """
    ap = argparse.ArgumentParser( description= "find aggregate regions based on correlations." )
    ap.add_argument('-a','--analysis',help="name of analysis to discuss [CMS-SUS-19-006-ma5]",
                    default = "CMS-SUS-19-006-ma5", type=str )
    ap.add_argument('-c','--corr',help="correlation needed to cluster [.5]",
                    default = .5, type=float )
    ap.add_argument( '-t','--takeout',help="dont cluster these SRs", nargs="*",
                     type=int, action="append" )
    ap.add_argument( '-d','--drop',help="drop these SRs", nargs="*",
                     type=int, action="append" )
    ap.add_argument('-D','--database',help="path to database [../../smodels-database]",
                    default = "../../smodels-database", type=str )
    args = ap.parse_args()
    aggs, dropped = aggregateByCorrs ( args.database, args.analysis, args.drop, args.takeout, args.corr )
    describe ( aggs, dropped )

if __name__ == "__main__":
    main()
