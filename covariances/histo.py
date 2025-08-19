#!/usr/bin/python3

""" simple script that produces a histogram of which signal regions 
    are marked as one of the first <n> bests (i.e. highest expected r values).
    Suggests also aggregate regions.
"""

import sys
import argparse
import pickle


def main():
    histo={}
    def add ( Id, n ):
        for i in range(1,Id+1):
            if not i in histo.keys():
                histo[i]=0
        histo[Id]+=n

    ap = argparse.ArgumentParser( description= "histogramming signal regions." )
    ap.add_argument('-a','--analysis',help="name of analysis to histogram [CMS-SUS-16-050]",
                    default = "CMS-SUS-16-050", type=str )
    ap.add_argument('-t','--topo',help="specify a topology [all]",
                    default = "all", type=str )
    args = ap.parse_args()
    fname = args.analysis
    if fname == "052":
        fname = "CMS-PAS-SUS-16-052"
    if fname == "050":
        fname = "CMS-SUS-16-050"
    # fname = "CMS-PAS-SUS-16-052"
    # fname = "CMS-SUS-16-050"

    # onlyTopo = "T2tt"
    onlyTopo = args.topo
    if onlyTopo in [ "all", "none" ]:
        onlyTopo=None

    regions = { "CMS-PAS-SUS-16-052": 44, "CMS-SUS-16-050": 84 }
    for i in range(1,regions[fname]+1):
        histo[i]=0
    print ( "opening",fname )
    f=open(f"{fname}.pcl","rb")
    ctr=0
    skipped = []
    while True:
        try:
            d=pickle.load(f)
            ctr+=1
            topo=d["t"]
            if onlyTopo != None and topo != onlyTopo:
                continue
            r0 = d["r0"]
            if r0 > 5. or r0 < 0.05:
                skipped.append ( [ ctr,r0 ] )
                continue

            for i in range(20):
                nr=d[f"n{int(i)}" ]
                points = 2**(-i)
                add(nr,points)
        except EOFError as e:
            break

    if len ( skipped ):
        print ( f"skipped: {skipped}" )
    tot_points = sum ( histo.values() )
    print ( f"read {int(ctr)} lines. {int(tot_points)} points total. topo: {onlyTopo}" )

    almostnever,never = [],[]
    occurs = {}
    threshold = tot_points / 10000.
    for Id,occ in histo.items():
        if not occ in occurs:
            occurs[occ]=[]
        occurs[occ].append ( Id )
        if occ<threshold:
            almostnever.append ( Id )
        if occ==0.:
            never.append ( Id )

    keys = list ( occurs.keys() )
    keys.sort()

    for ctr,k in enumerate(keys[::-1]):
        v = occurs[k]
        SRs=f"{v}"
        if len(v) == 1:
            SRs = f"{v[0]}"
        if ctr<3:
            print ( f"{int(k)} points: {SRs}" )

    agg=[]

    tmp = []
    cur = 0
    for k in keys[::-1]:
        v = occurs[k]
        for vi in v:
            tmp.append ( vi )
        cur += k
        if cur >= tot_points/14.:
            agg.append( tmp )
            tmp=[]
            cur = 0

    print ( f"proposed aggregation {len(agg)} SRs: {agg}" )
    print ()
    print ( f"{len(almostnever)} SRs have < {threshold} points: {almostnever}" )
    print ()
    print ( f"{len(never)} SRs have 0 points: {never}" )

if __name__ == "__main__":
    main()
