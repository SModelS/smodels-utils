#!/usr/bin/env python3

""" code to compute aggregates based on the dataset stats *and* the correlation matrix """

import glob
import argparse

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
        if 'leadingsDSes' in pt:
            for idx,(k,v) in enumerate(pt["leadingsDSes"]):
                if not v in ret:
                    ret[v]=0
                ret[v]+=1000./(n*(idx+1)**2)
    return ret

def pprint ( C, droprate = 2., takeoutrate = 150., 
             cut = .5 ):
    """ 
    :param droprate: maximum score with which we drop SR
    :param takeoutrate: minimum score with which we takeout
    :param cut: cut on correlation for findAggregates
    """
    # print ( C )
    ones = 0
    aggs, overflow, greater = [], [], []
    drops, zeroes = [], []
    pmax = takeoutrate
    pmin = droprate
    for i in range(1,174):
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
            greater.append ( i )
            aggs.append ( [ i ] )
        # print ( f"{sr}: {C[sr]:.3f}" )
    aggs.append ( overflow )
    print ( f"{len(zeroes)} zeroes, {ones} < {pmax}, {len(greater)} > pmax" )
    # print ( f"agg: {aggs}" )
    print ( f'{len(greater)} takeouts: -t {" -t ".join ( map(str, greater ) ) }' )
    print ( f'{len(drops)} drops: -d {" -d ".join ( map(str, drops ) ) }' )
    return drops, greater

def run():
    ap = argparse.ArgumentParser( description= "determine some stats about the SRs" )
    ap.add_argument( '-d','--drop',help="maximum score with which we drop [2.]",
                     default = 2., type=float )
    ap.add_argument( '-t','--takeout',help="minimum score with which we takeout [150.]",
                     default = 150., type=float )
    ap.add_argument( '-c','--corr',help="cut on correlations for findAggregates [.5]",
                     default = .5, type=float )
    ap.add_argument('-D','--database',help="path to database [../../smodels-database]",
                    default = "../../smodels-database", type=str )
    ap.add_argument('-a','--analysis',help="name of analysis to discuss [CMS-SUS-19-006-ma5]",
                    default = "CMS-SUS-19-006-ma5", type=str )
    args = ap.parse_args()
    from smodels_utils.helper import various
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
        D = retrieve ( f )
        for k,v in D.items():
            if not k in C:
                C[k]=0
            C[k]+=v*factor
    print ( "done!" )
    drops, greater = pprint ( C, args.drop, args.takeout, args.corr )
    import aggregators 
    print ( "drops", drops )
    # aggregators.aggregateByCorrs ( args.database, args.analysis, drops, greater, args.corr )
    aggregators.aggregateByNames ( args.database, args.analysis )

if __name__ == "__main__":
    run()
