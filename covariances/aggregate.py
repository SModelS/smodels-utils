#!/usr/bin/env python3

""" code to compute aggregates based on the dataset stats *and* the correlation matrix """

import glob
import argparse
import aggregators 
from smodels_utils.helper import various

def pprint ( C, droprate = 2., takeoutrate = 150., 
             cut = .5 ):
    """ 
    :param droprate: maximum score with which we drop SR
    :param takeoutrate: minimum score with which we takeout
    :param cut: cut on correlation for findAggregates
    """
    print ( C )
    ones = 0
    aggs, overflow, exclusives = [], [], []
    drops, zeroes = [], []
    pmax = takeoutrate
    pmin = droprate
    nmax = -1
    for k,v in C.items():
        sr = k.replace("SR","")
        sr = int(sr)
        if sr > nmax:
            nmax = sr

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
        # print ( f"{sr}: {C[sr]:.3f}" )
    aggs.append ( overflow )
    print ( f"{len(zeroes)} zeroes, {ones} < {pmax}, {len(exclusives)} > pmax" )
    # print ( f"agg: {aggs}" )
    print ( f'{len(exclusives)} exclusives: -t {" -t ".join ( map(str, exclusives ) ) }' )
    print ( f'{len(drops)} drops: -d {" -d ".join ( map(str, drops ) ) }' )
    return drops, exclusives

def run():
    ap = argparse.ArgumentParser( description= "determine some stats about the SRs" )
    ap.add_argument( '-d','--drop',help="maximum score with which we drop [2.]",
                     default = 2., type=float )
    ap.add_argument( '-t','--takeout',help="minimum score with which we takeout [150.]",
                     default = 150., type=float )
    ap.add_argument( '-c','--corr',help="cut on correlations for findAggregates, zero means aggregate by names [None]",
                     default = None, type=float )
    ap.add_argument('-D','--database',help="path to database [../../smodels-database]",
                    default = "../../smodels-database", type=str )
    ap.add_argument('-a','--analysis',help="name of analysis to discuss [CMS-SUS-19-006-ma5]",
                    default = "CMS-SUS-19-006-ma5", type=str )
    args = ap.parse_args()
    path = various.getPathName ( args.database, args.analysis )
    files = glob.glob ( f"{path}/validation/T*_2EqMassAx_EqMassBy.py" )
    print ( f"[aggregate.py] getting stats for {path}." )
    C = {}
    print ( f"[aggregate.py]", end=" " )
    for f in files:
        p1 = f.rfind("/")
        topo = f[p1+1:]
        p2 = topo.find("_")
        topo = topo[:p2]
        print ( topo, end=" ", flush=True )
        factor = 1.0
        if "off" in f: # the offshell regions receive lower weight
            factor = .5
        D = aggregators.retrieve ( f )
        for k,v in D.items():
            if not k in C:
                C[k]=0
            C[k]+=v*factor
    print ( "done!" )
    drops, exclusives = pprint ( C, args.drop, args.takeout, args.corr )
    if args.corr in [ 0., None ]:
        aggs, dropped = aggregators.aggregateByNames ( args.database, args.analysis, drops, exclusives )
    else:
        aggs, dropped = aggregators.aggregateByCorrs ( args.database, args.analysis, drops, exclusives, 
                                       args.corr )
    aggregators.describe ( aggs, dropped, len(C) )
    aggregators.check ( aggs, dropped, len(C) )

if __name__ == "__main__":
    run()
