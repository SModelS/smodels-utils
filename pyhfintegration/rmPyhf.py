#!/usr/bin/env python3

""" simple script that removes all pyhf info from a database folder """
    
import glob, os

def cleanGlobalInfo ( f ):
    """ clean globalInfo.txt file """
    print ( f"cleaning global info {f}" )
    h=open ( f, "rt" )
    txt = h.read()
    h.close()
    if not "json" in txt:
        return
    lines= txt.split("\n")
    h=open( f, "wt" )
    for line in lines:
        if line.startswith("jsonFiles"):
            continue
        if line.startswith("datasetOrder"):
            continue
        if line.startswith("covariance" ):
            continue
        h.write ( f"{line}\n" )
    h.close()
    

def rm ( path ):
    files = glob.glob ( f"{path}/*" )
    # print ( f"{len(files)} files in {path}" )
    for f in files:
        if f.endswith ( ".json" ):
            print ( f"unlinking {f}" )
            os.unlink ( f )
        if f.endswith ( "globalInfo.txt" ):
            cleanGlobalInfo ( f )
        if os.path.isdir ( f ) and f != path:
            rm ( f )

rm ( "../../smodels-database" )
