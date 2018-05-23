#!/usr/bin/python3

""" simple script that produces a histogram of which signal regions 
    are marked as one of the first three bests """

histo={}

def add ( Id, n ):
    if not Id in histo.keys():
        histo[Id]=0
    histo[Id]+=n

import pickle
fname = "results"
fname = "CMS-PAS-SUS-16-052"
f=open("%s.pcl" % fname,"rb")
while True:
    try:
        d=pickle.load(f)
        id0,id1,id2=d["n0"],d["n1"],d["n2"]
        add(id0,5)
        add(id0,3)
        add(id0,1)
    except EOFError as e:
        break

print ( histo )

never = []
for Id,occ in histo.items():
    if occ==0: 
        never.append ( Id )


print ( "%s SRs were never: " % len(never), never )
