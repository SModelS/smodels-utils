#!/usr/bin/env python3

import shutil, os
from smodels.matching import modelTester
from smodels.experiment.databaseObj import Database
from pathlib import Path

from stats_ml import yieldsPrinter # yieldsPrinter is self-registering

def getSLHAFile ( masses ):
    ## we copy file, to keep track
    mN2 = masses["mN2"]
    mC1 = masses["mC1"]
    mN1 = masses["mN1"]
    srcf = f"TChiWZoff_{mN2}_{mN1}_{mC1}_{mN1}.slha"
    destf = f"TChiWZoff_{mN2}_{mN1}_{mC1}_{mN1}.slha"
    src = f"../smodels-utils/slha/{srcf}"
    if os.path.exists ( src ):
        ## cool, we can just copy
        dest = f"slha_scan/{destf}"
        shutil.copyfile ( src, dest )
        return dest
    else:
        return createSLHAFile ( masses )

def createSLHAFile ( masses ):
    mN2 = masses["mN2"]
    mC1 = masses["mC1"]
    mN1 = masses["mN1"]
    destf = f"TChiWZoff_{mN2}_{mN1}_{mC1}_{mN1}.slha"
    with open ( f"templates/TChiWZoff.template", "rt" ) as f:
        lines = f.readlines()
        f.close()
    dest = f"slha_scan/{destf}"
    with open ( dest, "wt" ) as f:
        for line in lines:
            t = line.replace("M1",f"{mN1}" )
            t = t.replace("M0",f"{mN2}" )
            t = t.replace("m0",f"{mC1}" )
            f.write ( t )
        f.close()
    addXSec ( dest )
    return dest

def addXSec ( filename ):
    from validation.pythiaCardGen import getPythiaCardFor
    motherPDGs = [ 1000023, 1000024 ]
    pythiaVersion = 6
    pythiaCard = getPythiaCardFor ( motherPDGs, None, pythiaVersion )
    nprocesses = 2
    sqrts = [[ 13 ]]
    nevents = 10000
    # import argparse
    from types import SimpleNamespace
    # xargs = argparse.Namespace()
    xargs = SimpleNamespace()
    xargs.filename = filename
    xargs.pythia6 = False
    xargs.pythia8 = True
    if pythiaVersion == 6:
        xargs.pythia6 = True
        xargs.pythia8 = False
    xargs.sqrts = sqrts
    xargs.ncpus = nprocesses
    xargs.nevents = nevents
    xargs.pythiacard = pythiaCard
    xargs.NLL = False
    xargs.NLO = False
    # xargs.NLL = True
    xargs.tofile = False
    xargs.alltofile = True
    xargs.keep=False
    xargs.LOfromSLHA = False
    xargs.query = False
    xargs.colors = None
    xargs.verbosity = 30
    from smodels.tools import xsecComputer
    print ( f"[yieldsCreator] computing xsecs" )
    xsecComputer.main ( xargs )
    Path ( pythiaCard ).unlink ( missing_ok = True )

def runOnePoint ( p ):
    print ( f"[yieldsCreator] run for {p['mN2']},{p['mC1']},{p['mN1']}" )
    inFile = getSLHAFile ( p )
    parameterFile="inis/1909.ini"
    parser = modelTester.getParameters(parameterFile)
    database = Database ( "../smodels-database/" )
    modelTester.loadDatabaseResults(parser, database)
    fileList, inDir = modelTester.getAllInputFiles(inFile)
    development = False
    timeout = 0
    outputDir = "my_results/"
    modelTester.testPoints ( fileList , inDir, outputDir, parser,
        database, timeout, development, parameterFile )

def prepare():
    Path ( "slha_scan/" ).mkdir(exist_ok=True)
    Path ( "my_results/" ).mkdir(exist_ok=True)

def getPoints():
    points = []
    points.append ( { "mN2": 180,  "mC1": 180, "mN1": 157 } )
    points.append ( { "mN2": 405,  "mC1": 405, "mN1": 360 } )
    points.append ( { "mN2": 360,  "mC1": 360, "mN1": 285 } )
    points.append ( { "mN2": 105,  "mC1": 105, "mN1": 60 } )
    points.append ( { "mN2": 285,  "mC1": 285, "mN1": 240 } )
    points.append ( { "mN2": 150,  "mC1": 110, "mN1": 70 } )
    points.append ( { "mN2": 120,  "mC1": 150, "mN1": 100 } )
    # points.append ( { "mN2": 225,  "mC1": 225, "mN1": 211 } )
    return points

def runAll():
    prepare()
    points = getPoints()
    for p in points:
        runOnePoint ( p )

def submit ( mN2, mC1, mN1 ):
    cmd = [ "sbatch", "-c", "2", "--time", "479" ]
    cmd += [ "./yieldsCreator.py", "--mN1", f"{mN1}", "--mC1", f"{mC1}" ]
    cmd += [ "--mN2", f"{mN2}" ]
    import subprocess
    a = subprocess.run ( cmd, stdout = subprocess.PIPE )
    print ( str ( a.stdout.strip() ) )

def runGrid():
    for mN2 in range(100,401,50 ):
        for mN1 in range ( 0, 401, 30 ):
            if mN1 > mN2:
                continue
            if mN2 - mN1 > 80:
                continue
            submit ( mN2, mN2, mN1 )
    for mN2 in range(100,351,50 ):
        for mN1 in range ( 20, 300, 30 ):
            mC1 = mN2 - mN1/2.
            if mN1 > mC1:
                continue
            if mN2 - mN1 > 80.:
                continue
            submit ( mN2, mC1, mN1 )
    import sys; sys.exit()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="create points for joaquin" )
    ap.add_argument( '--all',
            help='do all points', action='store_true')
    ap.add_argument( '--grid',
            help='a grid', action='store_true')
    ap.add_argument( '--point',
            help='one specific point', type=int, default = None )
    ap.add_argument( '--mN1',
            help='mass of N1', type=float, default = None )
    ap.add_argument( '--mC1',
            help='mass of C1', type=float, default = None )
    ap.add_argument( '--mN2',
            help='mass of N2', type=float, default = None )
    args = ap.parse_args()
    if args.all:
        runAll()
    if args.grid:
        runGrid()
    if args.point != None:
        points = getPoints()
        prepare()
        runOnePoint ( points[args.point] )
    if args.mN1 != None:
        prepare()
        point = { "mN1": args.mN1, "mN2": args.mN2, "mC1": args.mC1 }
        runOnePoint ( point )
