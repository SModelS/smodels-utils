#!/usr/bin/python3

""" simple script that produces a histogram of which signal regions 
    are marked as one of the first <n> bests (i.e. highest expected r values) """

import sys

histo={}

def add ( Id, n ):
    for i in range(1,Id+1):
        if not i in histo.keys():
            histo[i]=0
    histo[Id]+=n

import pickle
fname = "CMS-PAS-SUS-16-052"
# fname = "CMS-SUS-16-050"

if len(sys.argv)>1:
    fname=sys.argv[1]
    if sys.argv[1]=="-h" or sys.argv[1]=="--help":
        print ( "usage: histo.py [CMS-PAS-SUS-16-052|CMS-SUS-16-050]" )
        sys.exit()

regions = { "CMS-PAS-SUS-16-052": 44, "CMS-SUS-16-050": 84 }
for i in range(1,regions[fname]+1):
    histo[i]=0
print ( "opening",fname )
f=open("%s.pcl" % fname,"rb")
ctr=0
while True:
    try:
        d=pickle.load(f)
        ctr+=1
        id0,id1,id2,id3,id4,id5=d["n0"],d["n1"],d["n2"],d["n3"],d["n4"],d["n5"]
        id6,id7=d["n6"],d["n7"]
        add(id0,21)
        add(id1,15)
        add(id2,11)
        add(id3,9)
        add(id4,7)
        add(id5,5)
        add(id6,3)
        add(id7,1)
    except EOFError as e:
        break

print ( "read",ctr,"lines" )

never = []
occurs = {}
for Id,occ in histo.items():
    if not occ in occurs:
        occurs[occ]=[]
    occurs[occ].append ( Id )
    if occ<1000:
        never.append ( Id )

keys = list ( occurs.keys() )
keys.sort()

for k in keys:
    v = occurs[k]
    SRs="%s" % v
    if len(v) == 1:
        SRs = "%s" % v[0]
    print ( "%d points: %s" % ( k, SRs ) )

print ( "%s SRs have < x points: " % len(never), never )
