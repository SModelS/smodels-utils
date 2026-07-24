#!/usr/bin/env python3

import shutil, os, sys, time
from smodels.matching import modelTester
from smodels.experiment.databaseObj import Database
from pathlib import Path

# printers are self-registering
from stats_ml import yieldsPrinter, csvPrinter
from yields_helpers import outputFile, unlock

def getTopLevelDir ():
    """ get the path to smodels-utils/ """
    current_dir = "/users/wolfgan.waltenberger/git/smodels-utils/"
    if os.path.exists ( current_dir ):
        return current_dir
    current_dir = Path(__file__).resolve().parent.parent
    return current_dir

def getSLHAFile ( masses, txname : str, options ):
    ## we copy file, to keep track
    mN2 = masses["mN2"]
    mC1 = masses["mC1"]
    mN1 = masses["mN1"]
    srcf = f"{txname}_{mN2}_{mN1}_{mC1}_{mN1}.slha"
    destf = f"{txname}_{mN2}_{mN1}_{mC1}_{mN1}.slha"
    src_d = f"{getTopLevelDir()}/slha"
    src = os.path.abspath ( f"{src_d}/{srcf}" )
    if os.path.exists ( src ):
        print ( f"[yieldsCreator] found {src}: will use it" )
        ## cool, we can just copy
        dest = f"slha_scan/{destf}"
        shutil.copyfile ( src, dest )
        return dest
    else:
        if options["compute_xsecs"]:
            print ( f"[yieldsCreator] did not find {src}: need to make it" )
            return createSLHAFile ( masses, txname )
        else:
            print ( f"[yieldsCreator] did not find {src}: skip it" )
            return None

def createSLHAFile ( masses, txname : str ):
    mN2 = masses["mN2"]
    mC1 = masses["mC1"]
    mN1 = masses["mN1"]
    destf = f"{txname}_{mN2}_{mN1}_{mC1}_{mN1}.slha"
    templ_d = os.path.abspath ( f"{getTopLevelDir()}/slha/templates/" )
    with open ( f"{templ_d}/{txname}.template", "rt" ) as f:
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
    addRefXSec ( dest )
    return dest

def addRefXSec ( filename ):
    from smodels_utils.morexsecs.refxsecComputer import RefXSecComputer
    first = True
    verbose = True
    computer = RefXSecComputer( verbose, first )
    version = "1.0.0"
    c = f"produced via yieldsCreator v{version}"
    ewk = None
    comment = None
    ignore_pids = []
    if comment != None:
        c+= f": {comment}"
    if ewk != "wino":
        c+= f" [{ewk}]"
    computer.computeForOneFile ( [13], filename, True,
            comment = c, ignore_pids = ignore_pids, ewk = ewk )

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

def runOnePoint ( p, options ) -> bool:
    """
    :returns True if success
    """
    of = outputFile ( p['mN2'], p['mC1'], p['mN1'], options )
    for particle,mass in p.items():
        if mass == int(mass):
            p[particle]=int(mass)
    print ( f"[yieldsCreator] run for {p['mN2']}, {p['mC1']}, {p['mN1']}" )
    parser = modelTester.getParameters(options["inifile"])
    txname = parser["database"]["txnames"]
    inFile = getSLHAFile ( p, txname, options )
    if inFile == None:
        unlock ( of )
        return False
    database = Database ( parser["database"]["path"] )
    modelTester.loadDatabaseResults(parser, database)
    if options["enable_full"]:
        enableFullLlhds ( database )
    fileList, inDir = modelTester.getAllInputFiles(inFile)
    development = False
    timeout = 0
    modelTester.testPoints ( fileList , inDir, options["outputdir"], parser,
        database, timeout, development, options["inifile"] )
    unlock ( of )
    return True

def prepare( options ):
    Path ( "slha_scan/" ).mkdir(exist_ok=True)
    Path ( options["outputdir"] ).mkdir(exist_ok=True)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="create points for joaquin" )
    ap.add_argument( '--dry_run',
            help='just show the batch jobs', action='store_true')
    ap.add_argument( '--enable_full',
            help='enable full likelihoods', action='store_true')
    ap.add_argument( '--compute_xsecs',
            help='compute xsecs if missing', action='store_true')
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
    args = ap.parse_args()
    prepare( vars(args) )
    point = { "mN1": args.mN1, "mN2": args.mN2, "mC1": args.mC1 }
    runOnePoint ( point, vars(args) )
