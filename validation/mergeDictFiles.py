#!/usr/bin/env python3

import argparse, subprocess, glob

def merge ( infile1, infile2, copy ):
    """ merge infile1 and infile2
    :param copy: copy output file to infile1
    """
    f1 = open ( infile1, "rt" )
    txt1 = f1.read()
    exec ( txt1, globals() )
    meta1 = meta
    validationData1 = validationData
    prevn1 = len ( validationData1)
    f1.close()
    f2 = open ( infile2, "rt" )
    txt2 = f2.read()
    exec ( txt2, globals() )
    meta2 = meta
    validationData2 = validationData
    prevn2 = len ( validationData2)
    f2.close()
    outf = "out.py"
    out = open ( outf, "wt" )
    slhafiles = [ x["slhafile"] for x in validationData1 ]
    for v in validationData2:
        if not v["slhafile"] in slhafiles:
            validationData1.append ( v )
    validationData1.sort ( key = lambda x: x["axes"]["x"]*1e6 + x["axes"]["y"] )
    postn = len ( validationData1 )
    meta1["npoints"]=len(validationData1)
    out.write ( f"validationData = [" )
    for i,v in enumerate ( validationData1 ):
        out.write ( f"{v}" )
        if i + 1 < len ( validationData1 ):
            out.write ( ",\n" )
        else:
            out.write ( "]\n" )
    out.write ( f"meta = {meta1}\n" )
    out.close()
    print ( f"[mergeDictFiles] merged {prevn1}+{prevn2}={postn} points to {outf}" )
    cmd = f"cp {outf} {infile1}"
    if copy:
        subprocess.getoutput ( cmd )
    print ( cmd )
    
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="merge dictionary files")
    ap.add_argument('-d', '--databasePath',
            help='database path ../../smodels-database/13TeV/CMS',
            default = '../../smodels-database/13TeV/CMS', type = str)
    ap.add_argument('-t', '--topology',
            help='topology [T1]',
            default = 'T1', type = str)
    ap.add_argument('-1', '--infile1',
            help='first directory [CMS-SUS-19-006-adl/validation]',
            default = 'CMS-SUS-19-006-adl/validation', type = str)
    ap.add_argument('-2', '--infile2',
            help='second directory [CMS-SUS-19-006-adl-agg/validation]',
            default = 'CMS-SUS-19-006-adl-agg/validation', type = str)
    ap.add_argument('-c', '--copy',
            help='copy file to target location', action="store_true" )
    args = ap.parse_args()
    dbpath = args.databasePath
    topodict = f"{args.topology}_2EqMassAx_EqMassBy_combined.py"
    infile1 = f"{dbpath}/{args.infile1}/{topodict}"
    infile2 = f"{dbpath}/{args.infile2}/{topodict}"
    merge ( infile1, infile2, args.copy )
