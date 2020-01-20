#!/usr/bin/env python3

import ROOT

def main():
    anas = { "CMS-SUS-16-007": "razorboost_results.root" }
    f=ROOT.TFile( anas["CMS-SUS-16-007"] )
    regions=f.Get("regions")
    n=regions.GetEntries()
    # counts=f.Get("counts")
    ret = []
    SR="preselection"
    for i in range(n):
        ev = { "id": i }
        regions.GetEntry(i)
        v = int ( regions.GetLeaf( SR ).GetValue( )  )
        ev[SR]=v
        print ( "row", v )
        ret.append ( ev )
    return ret

def printDict( D ):
    print ( D )

ret = main()
printDict ( ret )
