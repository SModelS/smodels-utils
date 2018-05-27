#!/usr/bin/python3

""" simple script that produces a histogram of which signal regions 
    are marked as one of the first three bests """

histo={}

def add ( Id, n ):
    if not Id in histo.keys():
        histo[Id]=0
    histo[Id]+=n

import pickle
fname = "CMS-PAS-SUS-16-052"
#fname = "SUS16050"
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
print ( histo )

never = []
for Id,occ in histo.items():
    if occ==0: 
        never.append ( Id )


print ( "%s SRs were never: " % len(never), never )
