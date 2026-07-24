#!/usr/bin/env python3

import shutil, os, sys, time
from smodels.matching import modelTester
from smodels.experiment.databaseObj import Database
from pathlib import Path

# printers are self-registering
from stats_ml import yieldsPrinter, csvPrinter
from yields_helpers import outputFile, lock, unlock

def logCall ( jobids : list ):
    logfile = f"yields_creator.log"
    #logfile = f"{os.environ['HOME']}/yields_creator.log"
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
        if len(lines)>0:
            lastline = lines[-1].strip()
            p = lastline.find("]")
            lastline = lastline[p+2:]
    if line == lastline: # skip duplicates
        return
    f=open(logfile,"at")
    #f.write ( f"# slurm_validate.py-{time.strftime('%H:%M:%S')}\n{line}\n\n" )
    f.write ( f"# slurm_yields.py-{time.asctime()}\n" )
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

def prepare( options ):
    Path ( "slha_scan/" ).mkdir(exist_ok=True)
    Path ( "slurm_logs/" ).mkdir(exist_ok=True)
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

def submit ( mN2, mC1, mN1, options ):
    oFile = outputFile ( mN2, mC1, mN1, options )
    for ext in [ "csv", "json", "err", "temp" ]:
        fn = f"{oFile}.{ext}"
        if os.path.exists ( fn ):
            print ( f"[slurm_yields] {fn} exists. skipping" )
            # import sys; sys.exit()
            return
        else:
            pass
            # print ( f"[slurm_yields] {fn} doesnt exist" )
    for m in [ "mN1", "mC1", "mN2" ]:
        options.pop(m,None)
    cmd = [ "sbatch", "-c", "6", "--time", "479" ]
    #cmd = [ "sbatch", "-c", "2", "--time", "479" ]
    cmd += [ "--error", f"./slurm_logs/%j.out",
             "--output", f"./slurm_logs/%j.out" ]
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
    print ( f"[yieldsCreator] {' '.join(cmd)}" )
    if options["dry_run"]:
        return
    import subprocess
    lock ( oFile )
    a = subprocess.run ( cmd, stdout = subprocess.PIPE )
    print ( f'[yieldsCreator] {a.stdout.strip().decode("utf-8")}' )

def runGrid( options : dict ):
    prepare ( options )
    dmMothers = int ( options["dmMothers"] )
    dmN1 = int ( options["dmN1"] )
    minMothers = int ( options["minMothers"] )
    minN1 = int ( options["minN1"] )
    maxMothers = int ( options["maxMothers"] )
    maxN1 = int ( options["maxN1"] )
    max_dm = int ( options["max_dm"] )
    min_dm = int ( options["min_dm"] )
    halfway = bool ( options["halfway"] )
    for i in [ "dmMothers", "dmN1", "minMothers", "minN1", \
               "maxMothers", "maxN1", "max_dm", "min_dm", "halfway" ]:
        options.pop ( i )
    if not halfway:
        for mN2 in range(minMothers,maxMothers, dmMothers ):
            for mN1 in range ( minN1, maxN1, dmN1 ):
                if mN2 - mN1 < min_dm:
                    continue
                if mN2 - mN1 > max_dm:
                    continue
                submit ( mN2, mN2, mN1, options )
    if halfway:
        for mN2 in range( minMothers, maxMothers, dmMothers ):
            for mN1 in range ( minN1, maxN1, dmN1 ):
                mC1 = (mN2 + mN1)/2.
                if mC1 == int(mC1):
                    mC1 = int(mC1)
                if mC1 - mN1 < min_dm:
                    continue
                if mN2 - mN1 > max_dm:
                    continue
                submit ( mN2, mC1, mN1, options )

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="create points for joaquin" )
    ap.add_argument( '--all',
            help='do all points', action='store_true')
    ap.add_argument( '--grid',
            help='a grid', action='store_true')
    ap.add_argument( '--halfway',
            help='put mC1 halfway between mN2 and mN1', action='store_true')
    ap.add_argument( '--dry_run',
            help='just show the batch jobs', action='store_true')
    ap.add_argument( '--enable_full',
            help='enable full likelihoods', action='store_true')
    ap.add_argument( '--dmMothers',
            help='dm(mothers) for the grid [50]', type=int, default = 50 )
    ap.add_argument( '--minMothers',
            help='minimum mass of mothers for the grid [100]', type=int, default = 100 )
    ap.add_argument( '--maxMothers',
            help='maximum mass of mothers for the grid [401]', type=int, default = 401 )
    ap.add_argument( '--dmN1',
            help='dm(LSP) for the grid [30]', type=int, default = 30 )
    ap.add_argument( '--max_dm',
            help='max_dm between mothers and LSP [80]', type=int, default = 80 )
    ap.add_argument( '--min_dm',
            help='min_dm between mothers and LSP [0]', type=int, default = 0 )
    ap.add_argument( '--minN1',
            help='minimum mass of LSP for the grid [0]', type=int, default = 0 )
    ap.add_argument( '--maxN1',
            help='maximum mass of LSP for the grid [300]', type=int, default = 300 )
    ap.add_argument( '--mN1',
            help='mass of N1', type=float, default = None )
    ap.add_argument( '--mC1',
            help='mass of C1', type=float, default = None )
    ap.add_argument( '--mN2',
            help='mass of N2', type=float, default = None )
    ap.add_argument( '--inifile',
            help='path to ini file [default.ini]', type=str, default = "default.ini" )
    ap.add_argument( '--outputdir',
            help='output directory [yields_results]',
            type=str, default = "yields_results" )
    args = ap.parse_args()
    if args.grid:
        runGrid( vars(args) )
        logCall([])
        import sys; sys.exit()
