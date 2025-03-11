#!/usr/bin/env python3

""" code to compute aggregates based on the dataset stats *and* the correlation matrix """

import glob
import argparse
import aggregators 
from smodels_utils.helper import various

def pprint ( C, droprate = 2., isolationscore = 150., 
             cut = .5, listAll = False ):
    """ 
    :param droprate: maximum score with which we drop SR
    :param isolationscore: minimum score with which we isolate an SR
    :param cut: cut on correlation for findAggregates
    :param listAll: list all signal regions with scores
    """
    # print ( C )
    ones = 0
    aggs, overflow, exclusives = [], [], []
    drops, zeroes = [], []
    pmax = isolationscore
    pmin = droprate
    nmax = -1
    for k,v in C.items():
        sr = k.replace("SR","")
        try:
            sr = int(sr)
            if sr > nmax:
                nmax = sr
        except Exception as e:
            pass

    scores = {}
    for i in range(1,nmax):
        sr = f"SR{i}"
        if not sr in C:
            zeroes.append ( i )
            C[sr] = 0
        if C[sr]<pmin:
            drops.append ( i )
        if C[sr]<pmax:
            ones += 1
            overflow.append ( i )
        else:
            exclusives.append ( i )
            aggs.append ( [ i ] )
        scores[ C[sr] ] = sr
    keys = list ( scores.keys() )
    keys.sort()
    if listAll:
        for k in keys:
                print ( f"{k:6.2f}: {scores[k]}" )
    aggs.append ( overflow )
    print ( f"[aggregate.py] {len(zeroes)} zeroes, {ones} < {pmax}, {len(exclusives)} > pmax" )
    # print ( f"agg: {aggs}" )
    print ( f'[aggregate.py] {len(exclusives)} SRs are exclusives: -t {" -t ".join ( map(str, exclusives ) ) }' )
    print ( f'[aggregate.py] {len(drops)} SRs are dropped: {" -d ".join ( map(str, drops ) ) }' )
    return drops, exclusives

def run():
    ap = argparse.ArgumentParser( description= "computes a not too crazy aggregation list" )
    ap.add_argument( '-d','--drop', help="maximum score (a measure of sensitivity) with which we drop [2.]",
                     default = 2., type=float )
    ap.add_argument( '-L','--level', help="aggregation level [1]",
                     default = 1, type=int )
    ap.add_argument( '-v','--verbose', help="be verbose", action="store_true" )
    ap.add_argument( '-l','--list', help="list all", action="store_true" )
    ap.add_argument( '-i','--isolate', help="minimum score (a measure of sensitivity) with which we isolate a signal region. [150.]",
                     default = 150., type=float )
    ap.add_argument( '-c','--corr',help="cut on correlations for findAggregates, None (or 0.) means aggregate by names [None]",
                     default = None, type=float )
    ap.add_argument('-D','--database',help="path to database [../../smodels-database]",
                    default = "../../smodels-database", type=str )
    ap.add_argument('-a','--analysis',help="name of analysis to discuss [CMS-SUS-21-008]",
                    default = "CMS-SUS-21-008", type=str )
    args = ap.parse_args()
    path = various.getPathName ( args.database, args.analysis )
    files = glob.glob ( f"{path}/validation/T*_2EqMassAx_EqMassBy.py" )
    print ( f"[aggregate.py] getting stats for {path}." )
    C = {}
    print ( f"[aggregate.py]", end=" " )
    first = True
    for f in files:
        p1 = f.rfind("/")
        topo = f[p1+1:]
        p2 = topo.find("_")
        topo = topo[:p2]
        if first:
            print ( f"found", end= " " )
            first = False
        else:
            print ( ",", end = " " )
        print ( f"{topo}", end="", flush=True )
        factor = 1.0
        if "off" in f: # the offshell regions receive lower weight
            factor = .5
        D = aggregators.retrieve ( f )
        for k,v in D.items():
            if not k in C:
                C[k]=0
            C[k]+=v*factor
    print ( " done!" )
    drops, exclusives = pprint ( C, args.drop, args.isolate, args.corr, args.list )
    if args.corr in [ 0., None ]:
        aggs, dropped = aggregators.aggregateByNames ( args.database, args.analysis, drops, exclusives, args.level, args.verbose )
    else:
        aggs, dropped = aggregators.aggregateByCorrs ( args.database, args.analysis, drops, exclusives, args.corr, args.verbose )
    aggregators.describe ( aggs, dropped, len(C) )
    result  = aggregators.getExpResult ( args.database, args.analysis )
    datasets, comments = aggregators.getDatasets( result, addReverse=False, verbose = args.verbose )
    aggregators.check ( aggs, dropped, len(datasets) )

if __name__ == "__main__":
    run()
