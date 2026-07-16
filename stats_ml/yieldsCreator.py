#!/usr/bin/env python3

import shutil, os
from smodels.matching import modelTester
from smodels.experiment.databaseObj import Database
from pathlib import Path

# printers are self-registering
from stats_ml import yieldsPrinter, csvPrinter

def logCall ( jobids : list ):
    logfile = f"{os.environ['HOME']}/yields_creator.log"
    line = ""
    for i in sys.argv:
        if " " in i or "," in i:
            i = f'"{i}"'
        line += f"{i} "
    line = line.strip()
    lastline = ""
    if os.path.exists( logfile ):
        f=open(logfile,"rt")
        lines = f.readlines()
        f.close()
        lastline = lines[-1].strip()
        p = lastline.find("]")
        lastline = lastline[p+2:]
    if line == lastline: # skip duplicates
        return
    f=open(logfile,"at")
    #f.write ( f"# slurm_validate.py-{time.strftime('%H:%M:%S')}\n{line}\n\n" )
    f.write ( f"# yieldsCreator.py-{time.asctime()}\n" )
    f.write ( f"{line}\n" )
    s_jobids = ','.join(map(str,jobids))
    s_jobids = ""
    for i,jobid in enumerate(jobids):
        if i!=0:
            s_jobids += ", "
            if i % 6 == 0:
                s_jobids += "\n#         "
        s_jobids += str(jobid)
    f.write ( f"# jobids: {s_jobids}\n\n" )
    f.close()

def getSLHAFile ( masses ):
    ## we copy file, to keep track
    mN2 = masses["mN2"]
    mC1 = masses["mC1"]
    mN1 = masses["mN1"]
    srcf = f"TChiWZoff_{mN2}_{mN1}_{mC1}_{mN1}.slha"
    destf = f"TChiWZoff_{mN2}_{mN1}_{mC1}_{mN1}.slha"
    src_d = "../smodels-utils/slha"
    if not os.path.exists ( src_d ):
        src_d = "../../smodels-utils/slha"
    src = os.path.abspath ( f"{src_d}/{srcf}" )
    if os.path.exists ( src ):
        print ( f"[yieldsCreator] found {src}: will use it" )
        ## cool, we can just copy
        dest = f"slha_scan/{destf}"
        shutil.copyfile ( src, dest )
        return dest
    else:
        print ( f"[yieldsCreator] did not find {src}: need to make it" )
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
    print ( f"[yieldsCreator] done computing xsecs" )

def enableFullLlhds ( database ):
    """ turn on full llhds """
    from smodels_utils.helper.databaseManipulations import enableFullLlhdModels
    for er in database.getExpResults():
        if not hasattr ( er.globalInfo, "statModels" ):
            continue
        if not "-orig" in er.globalInfo.id:
            continue
        print ( f"[yieldsCreator] enable full model for {er.globalInfo.id}" )
        enableFullLlhdModels ( er.globalInfo )

def runOnePoint ( p, options ):
    for particle,mass in p.items():
        if mass == int(mass):
            p[particle]=int(mass)
    print ( f"[yieldsCreator] run for {p['mN2']}, {p['mC1']}, {p['mN1']}" )
    inFile = getSLHAFile ( p )
    parser = modelTester.getParameters(options["inifile"])
    database = Database ( parser["database"]["path"] )
    modelTester.loadDatabaseResults(parser, database)
    if options["enable_full"]:
        enableFullLlhds ( database )
    fileList, inDir = modelTester.getAllInputFiles(inFile)
    development = False
    timeout = 0
    modelTester.testPoints ( fileList , inDir, options["outputdir"], parser,
        database, timeout, development, options["inifile"] )

def prepare( options ):
    Path ( "slha_scan/" ).mkdir(exist_ok=True)
    Path ( options["outputdir"] ).mkdir(exist_ok=True)

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

def runAll( options ):
    prepare( options )
    points = getPoints()
    for p in points:
        runOnePoint ( p, options )

def submit ( mN2, mC1, mN1, options ):
    for m in [ "mN1", "mC1", "mN2" ]:
        options.pop(m,None)
    cmd = [ "sbatch", "-c", "2", "--time", "479" ]
    cmd += [ "./yieldsCreator.py" ]
    cmd += [ "--mN1", f"{mN1}", "--mC1", f"{mC1}", "--mN2", f"{mN2}" ]
    for option, value in options.items():
        if option in [ "grid", "all", "point" ]:
            continue
        if type(value)==bool:
            if value == True:
                cmd += [ f"--{option}" ]
            else:
                pass
#        elif type(value)!=str:
#            print ( f"[yieldsCreator] option {option} is {type(value)} {value}" )
        else:
            cmd += [ f"--{option}", str(value) ]
    print ( f"[yieldsCreator] {cmd}" )
    if options["dry_run"]:
        return
    import subprocess
    a = subprocess.run ( cmd, stdout = subprocess.PIPE )
    print ( f'[yieldsCreator] {a.stdout.strip().decode("utf-8")}' )

def runGrid( options : dict ):
    for mN2 in range(100,401,int ( options["dmMothers"] ) ):
        for mN1 in range ( 0, 401, int ( options["dmN1"] ) ):
            if mN1 > mN2:
                continue
            if mN2 - mN1 > 80:
                continue
            submit ( mN2, mN2, mN1, options )
    for mN2 in range(100,351, int ( options["dmMothers"] ) ):
        for mN1 in range ( 20, 300, int ( options["dmN1"] ) ):
            mC1 = mN2 - mN1/2.
            if mN1 > mC1:
                continue
            if mN2 - mN1 > 80.:
                continue
            submit ( mN2, mC1, mN1, options )
    import sys; sys.exit()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="create points for joaquin" )
    ap.add_argument( '--all',
            help='do all points', action='store_true')
    ap.add_argument( '--grid',
            help='a grid', action='store_true')
    ap.add_argument( '--dry_run',
            help='just show the batch jobs', action='store_true')
    ap.add_argument( '--enable_full',
            help='enable full likelihoods', action='store_true')
    ap.add_argument( '--point',
            help='one specific point [0-6]', type=int, default = None )
    ap.add_argument( '--dmMothers',
            help='dm for the grid', type=int, default = 50 )
    ap.add_argument( '--dmN1',
            help='dm for the grid', type=int, default = 30 )
    ap.add_argument( '--mN1',
            help='mass of N1', type=float, default = None )
    ap.add_argument( '--mC1',
            help='mass of C1', type=float, default = None )
    ap.add_argument( '--mN2',
            help='mass of N2', type=float, default = None )
    ap.add_argument( '--inifile',
            help='path to ini file', type=str, default = "default.ini" )
    ap.add_argument( '--outputdir',
            help='output directory [yields_results]',
            type=str, default = "yields_results" )
    logCall([])
    args = ap.parse_args()
    if args.all:
        runAll( vars(args) )
    if args.grid:
        runGrid( vars(args) )
    if args.point != None:
        points = getPoints()
        prepare( vars(args) )
        runOnePoint ( points[args.point], vars(args) )
    if args.mN1 != None:
        prepare( vars(args) )
        point = { "mN1": args.mN1, "mN2": args.mN2, "mC1": args.mC1 }
        runOnePoint ( point, vars(args) )
