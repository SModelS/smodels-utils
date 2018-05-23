#!/usr/bin/python3

""" simple script that produces a histogram of which signal regions 
    are marked as one of the first three bests """

histo={}
for i in range(84):
    histo[i]=0

import pickle
f=open("results.pcl","rb")
while True:
    try:
        d=pickle.load(f)
        id0,id1,id2=d["n0"],d["n1"],d["n2"]
        histo[id0]+=5
        histo[id1]+=3
        histo[id2]+=1
    except EOFError as e:
        break

print ( histo )

never = []
for Id,occ in histo.items():
    if occ==0: 
        never.append ( Id )


print ( "%s SRs were never: " % len(never), never )
