#!/usr/bin/python3

""" Identify a good example for how to combine results. """


import sys
from smodels.experiment.databaseObj import Database

d=Database( "/home/walten/git/smodels-database" )

txnames,sets={},{}

results=d.getExpResults()
for r in results:
    if hasattr ( r, "contact" ) and "fastlim" in r.contact.lower():
        continue
    for t in r.getTxNames():
        if not t.hasLikelihood():
            continue
        txn=t.txName
        if not txn in txnames.keys():
            txnames[txn]=[]
        if not r in txnames[txn]:
            txnames[txn].append ( r )


for txname,analyses in txnames.items():
    if len(analyses) < 2:
        continue
    hasLLHDs=0
    for ctr,a in enumerate(analyses):
        for b in analyses[ctr+1:]:
            if a.isUncorrelatedWith ( b ) == True:
                if not txname in sets.keys():
                    sets[txname]=set()
                sets[txname].add ( f"{a.id()} <-> {b.id()}" )
    #            print ( "%s: %s <-> %s" % ( txname, a.id(), b.id() ) )
    # sys.exit()

for k,v in sets.items():
    for pair in v:
        print ( f"{k}: {pair}" )
