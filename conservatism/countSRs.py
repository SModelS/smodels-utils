#!/usr/bin/env python3

f = open ( "original.dict", "rt" )
D = eval ( f.read() )
D10 = D[1.0]
anas, dsIds = set(), set()
for SR in D10:
    ana = SR["id"]
    ana = ana.replace("-multibin","").replace("-strong","")
    ana = ana.replace("-ewk","").replace("-agg","").replace("-hino","")
    anas.add ( ana )
    dsId = f'{SR["id"]}:{SR["datasetId"]}'
    dsIds.add ( dsId )
    if not "p_norm" in SR:
        print ( f"no p_norm in {dsIs}" )
    #print ( dsId )
print ( f"{len(anas)} anas, {len(dsIds)} dsIds in createData" )
dsIds = list(dsIds)
dsIds.sort()

#for i,dsId in enumerate(dsIds):
#    print ( i,dsId )
