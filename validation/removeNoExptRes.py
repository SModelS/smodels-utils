#!/usr/bin/env python3

""" remove all output files that dont have an ExptRes """

def removeFor ( files : str ):
    import glob, os
    files = glob.glob ( "_VWZoff/results/TChiWZoff*py" )
    for f in files:
        print ( f )
        with open ( f ) as h:
            try:
                d = {}
                e = exec(h.read(), d )
                if not "smodelsOutput" in d:
                    print ( f"{f}: no smodelsOutput: unlink!" )
                    os.unlink ( f )
                    continue
                smodelsOutput = d["smodelsOutput"]
                if not "ExptRes" in d:
                    print ( f"{f}: no ExptRes: unlink!" )
                    os.unlink ( f )
                    continue
                print ( f, "d", d["smodelsOutput"] )
            except SyntaxError as e:
                print ( f"{f}: SyntaxError {e}: unlink!" )
                os.unlink ( f )

def removeInDict ( dictfile : str ):
    from validationHelpers import streamlineValidationData
    print ( f"remove from {dictfile}" )
    f=open(dictfile,"r")
    d={}
    exec(f.read(),d)
    print ( d.keys() )
    oldData = d["validationData"]
    newData = []
    for x in oldData:
        if not "error" in x:
            newData.append ( x )
    validationData = streamlineValidationData ( str ( newData ) )
    g=open("dict.py","wt")
    g.write( f"validationData = {validationData}\n" )
    meta = d["meta"]
    meta["nerr"]=0
    meta["npoints"]=len(newData)
    g.write( f"meta = {str(meta)}\n" )
    g.close()
    print ( f"cp dict.py {dictfile}" )

def main():
    # removeFor ( "_VWZoff/results/TChiWZoff*py" )
    removeInDict ( "../../smodels-database/13TeV/ATLAS/ATLAS-SUSY-2019-09-eff/validationFull/TChiWZoff_x_x-y_combined.py" )

if __name__ == "__main__":
    main()
