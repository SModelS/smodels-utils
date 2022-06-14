#!/usr/bin/env python3

import argparse

def merge ( infile1, infile2 ):
    f1 = open ( infile1, "rt" )
    txt1 = f1.read()
    exec ( txt1, globals() )
    meta1 = meta
    validationData1 = validationData
    f1.close()
    f2 = open ( infile2, "rt" )
    txt2 = f2.read()
    exec ( txt2, globals() )
    meta2 = meta
    validationData2 = validationData
    f2.close()
    out = open ( "out.py", "wt" )
    slhafiles = [ x["slhafile"] for x in validationData1 ]
    for v in validationData2:
        if not v["slhafile"] in slhafiles:
            validationData1.append ( v )
    validationData1.sort ( key = lambda x: x["axes"]["x"]*1e6 + x["axes"]["y"] )
    meta1["npoints"]=len(validationData1)
    out.write ( f"validationData = [" )
    for i,v in enumerate ( validationData1 ):
        out.write ( f"{v}" )
        if i + 1 < len ( validationData1 ):
            out.write ( ",\n" )
        else:
            out.write ( "]\n" )
    out.write ( f"meta={meta1}\n" )
    out.close()
    
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="merge dictionary files")
    ap.add_argument('-d', '--databasePath',
            help='database path ../../smodels-database/13TeV/CMS/',
            default = '../../smodels-database/13TeV/CMS/', type = str)
    ap.add_argument('-t', '--topology',
            help='topology [T1]',
            default = 'T1', type = str)
    args = ap.parse_args()
    dbpath = args.databasePath
    topodict = f"{args.topology}_2EqMassAx_EqMassBy_combined.py"
    infile1 = f"{dbpath}CMS-SUS-19-006-adl/validation/{topodict}"
    infile2 = f"{dbpath}CMS-SUS-19-006-adl-agg/validation/{topodict}"
    merge ( infile1, infile2 )
