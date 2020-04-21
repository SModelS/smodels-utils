#!/usr/bin/env python3

with open("dict.py") as f:
    exec ( f.read() ) # should give us smodelsOutput

listOfExpRes = smodelsOutput["ExptRes"]

print ( "%d experimental results" % len(listOfExpRes) )
withLLHDs=[]
for er in listOfExpRes:
    if "likelihood" in er:
        withLLHDs.append ( er )
print ( "%d experimental results with llhds" % len(withLLHDs) )
