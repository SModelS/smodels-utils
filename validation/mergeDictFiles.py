#!/usr/bin/env python3

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
    for v in validationData2:
        if not v["slhafile"] in validationData1:
            validationData1.append ( v )
    meta1["npoints"]=meta1["npoints"]+meta2["npoints"]
    out.write ( f"validationData = " ) # {validationData1}\n" )
    for i,v in enumerate ( validationData1 ):
        out.write ( f"{v}" )
        if i + 1 < len ( validationData1 ):
            out.write ( ",\n" )
        else:
            out.write ( "]\n" )
    out.write ( f"meta={meta1}\n" )
    out.close()
    
if __name__ == "__main__":
    dbpath = "../../smodels-database/13TeV/CMS/"
    topodict = "T1_2EqMassAx_EqMassBy_combined.py"
    infile1 = f"{dbpath}CMS-SUS-19-006-adl/validation/{topodict}"
    infile2 = f"{dbpath}CMS-SUS-19-006-adl-agg/validation/{topodict}"
    merge ( infile1, infile2 )
