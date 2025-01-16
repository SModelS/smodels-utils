#!/usr/bin/env python3

"""
the script to start all results validation jobs with 

"""

import tempfile, argparse, stat, os, math, sys, time, glob, subprocess, shutil
from smodels_utils.helper.terminalcolors import *
from typing import Union, Dict

codedir = f"/scratch-cbe/users/{os.environ['USER']}/git"
outputsdir = f"/scratch-cbe/users/{os.environ['USER']}/outputs/"
if "CODEDIR" in os.environ:
    codedir = os.environ["CODEDIR"]
if "OUTPUTS" in os.environ:
    outputsdir = os.environ["OUTPUTS"]

def mkdir ( Dir ):
    if not os.path.exists ( Dir ):
        cmd = f"mkdir {Dir}"
        subprocess.getoutput ( cmd )

def cancelAllValidaters():
    o = subprocess.getoutput ( "slurm q | grep _V" )
    lines = o.split("\n")
    cancelled = []
    for line in lines:
        if not "_V" in line:
            continue
        tokens = line.split()
        nr = tokens[0]
        cmd = f"scancel {nr}"
        subprocess.getoutput ( cmd )
        cancelled.append ( nr )
    print ( f"[slurm_walk] cancelled {', '.join(cancelled)}" )

def getMaxJobId() -> int:
    """ get the highest job id """
    o = subprocess.getoutput ( "slurm q | grep _V" )
    lines = o.split("\n")
    nmax = 0
    for line in lines:
        tokens = line.split()
        nr = int(tokens[0])
        if nr > nmax:
            nmax = nr
    return nmax

def getMinJobId() -> int:
    """ get the lowest job id """
    o = subprocess.getoutput ( "slurm q | grep _V" )
    lines = o.split("\n")
    nmin = 1e99
    for line in lines:
        tokens = line.split()
        nr = int(tokens[0])
        if nr < nmin:
            nmin = nr
    return nmin

def cancelRangerOfValiders( jrange : str ):
    """ cancel only the jrange of runners """
    import re
    jrange = jrange.strip(" ")
    if re.search('[a-zA-Z]', jrange) is not None:
        from running_stats import cancelJobsByString
        return cancelJobsByString ( jrange )
    if not "-" in jrange: # single job
        cmd = f"scancel {jrange}"
        subprocess.getoutput ( cmd )
        print ( f"[slurm_walk] cancelled {jrange}" )
        return
    cancelled = []
    p1 = jrange.find("-")
    if p1 == len(jrange)-1: ## range is given as '<min>-'
        maxJobId = getMaxJobId()
        jrange += str(maxJobId)
    if p1 == 0:
        minJobId = getMinJobId()
        jrange = str(minJobId) + jrange

    if 0 < p1 < len(jrange)-1:
        # full range given
        jmin,jmax = int ( jrange[:p1] ), int ( jrange[p1+1:] )
        for i in range(jmin,jmax+1):
            cmd = f"scancel {i}"
            subprocess.getoutput ( cmd )
            cancelled.append ( i )
        print ( f"[slurm_walk] cancelled {', '.join(map(str,cancelled))}" )
        return
    o = subprocess.getoutput ( "slurm q | grep _V" )
    lines = o.split("\n")
    running = []
    for line in lines:
        if not "_V" in line:
            continue
        tokens = line.split()
        nr = tokens[0]
        running.append ( int ( nr ) )
    if p1 == 0:
        cancelRangerOfValiders( f"{min(running)}-{jrange[p1+1:]}" )
        return
    if p1 == len(jrange)-1:
        cancelRangerOfValiders( f"{jrange[:p1]}-{max(running)}" )
        return
    print ( "[slurm_walk] FIXME sth is wrong" )



def queryStats ( maxsteps : Union[None,int] = None ):
    """ just give us the statistics """
    import running_stats
    running_stats.count_jobs( "_V" )
    running_stats.running_stats( "_V" )
    if maxsteps != None:
        for i in range(maxsteps):
            time.sleep(30.)
            print()
            running_stats.count_jobs( "_V" )
            running_stats.running_stats( "_V" )
            print()

def validate ( args : Dict, idx ):
    """ run validation with ini file 
    :param inifile: ini file, should reside in smodels-utils/validation/
    :param dry_run: dont do anything, just produce script
    :param nprocesses: number of processes, typically 5
    :param time: time in hours
    :param analyses: string that replaces @@ANALYSES@@ in inifile
    :param topo: string that replaces @@TOPOS@@ in inifile
    :param keep: keep temporary files
    :param tempname: if not None, use this for the temp files names
    :param validationfolder: string that replaces @@VALIDATIONFOLDER@@ in inifile
    :param limit_points: run over only that many points
    :param model: the model to use (default)
    """
    inifile = args["validate"]
    dry_run = args["dry_run"]
    nprocesses = args["nprocesses"]
    time = args["time"]
    analyses = args["analyses"]
    topo = args["topo"]
    keep = args["keep"]
    tempname = args["tempname"]
    validationfolder = args["validationfolder"]
    limit_points = args["limit_points"]
    generatedata = args["generate_data"]
    dataselector = args["dataselector"]
    if topo in [ None, "all" ]:
        topo = "*"
    if analyses == None:
        analyses = "all"
    print ( f"[slurm_validate.py]{YELLOW} run validation with {inifile}{RESET}" )
    Dir = f"{codedir}/smodels-utils/clip/temp/"
    if not os.path.exists ( Dir ):
        os.mkdir ( Dir )
    with open ( f"{codedir}/smodels-utils/validation/inifiles/{inifile}", "rt" ) as f:
        lines = f.readlines()
        f.close()
    ## the first job might be a little different
    ## (eg generateData = True instead of ondemand)
    binaryIdx = 0 if idx == 0 else 1
    if tempname is None:
        newini = tempfile.mktemp(prefix="_V",suffix=".ini",dir=Dir )
    else:
        newini = f"{Dir}/{tempname}_{binaryIdx}.ini"
    # tempdir = os.path.basename ( newini ).replace(".ini","") # .replace("_V","tmp")
    if validationfolder is None:
        validationfolder = "validation"
    tempdir = None
    if tempname != None:
        tempdir = os.path.basename ( tempname )
    # if possible name the tempdir the same as the temp script and the temp ini file
    skeep = ""
    needTempDir = False ## if we operate in "continue" mode, we need:
    hasTempDir = False ## a predefined tempdir, and 
    hasLimitPoints = False ## limited points in the ini files!
    if keep:
        skeep = "--keep --cont"
        needTempDir = True
    with open ( newini, "wt" ) as f:
        for line in lines:
            newline = line.replace("@@ANALYSES@@", analyses )
            newline = newline.replace("@@TOPO@@", topo )
            newline = newline.replace("@@GENERATEDATA@@", generatedata )
            newline = newline.replace("@@DATASELECTOR@@", dataselector )
            newline = newline.replace("@@NCPUS@@", str(nprocesses) )
            newline = newline.replace("@@MODEL@@", args["model"] )
            newline = newline.replace("@@TIMEOUT@@", "30000" )
            newline = newline.replace("@@VALIDATIONFOLDER@@", validationfolder )
            if tempdir is None and "@@TEMPDIR@@" in line:
                continue
            if tempdir is not None:
                newline = newline.replace("@@TEMPDIR@@", tempdir )
            if limit_points in [ "all", 0, None, -1 ] and "limitPoints" in newline:
                ## we dont limit the points
                continue
            newline = newline.replace("@@LIMITPOINTS@@", str(limit_points))
            f.write ( newline )
            if "@@TEMPDIR@@" in line:
                hasTempDir = True
            if "limitPoints" in line:
                hasLimitPoints = True
        f.close()

    if needTempDir:
        if not hasTempDir:
            print ( f"[slurm_validate.py] ERROR we are in continue mode, but no temp dir has been defined in {inifile}!" )
            sys.exit()
        if not hasLimitPoints:
            print ( f"[slurm_validate.py] ERROR we are in continue mode, but no limitPoints has been defined!" )
            sys.exit()

    with open ( f"{codedir}/smodels-utils/clip/validate_template.sh", "rt" ) as f:
        lines = f.readlines()
        f.close()
    # filename = tempfile.mktemp(prefix="_V",suffix=".sh",dir="")
    filename = os.path.basename ( newini ).replace(".ini",".sh")
    newFile = f"{Dir}/{filename}"
    print ( f"[slurm_validate.py] creating script at {newFile}" )
    with open ( newFile, "wt" ) as f:
        for line in lines:
            newline = line.replace("@@INIFILE@@", newini )
            newline = newline.replace("@@ANALYSES@@", analyses )
            newline = newline.replace("@@TOPO@@", topo )
            newline = newline.replace("@@ORIGINIFILE@@", inifile  )
            newline = newline.replace("@@KEEP@@", skeep )
            f.write ( newline )
        f.close()
    tdir = "./temp"
    if not os.path.exists ( tdir ):
        os.mkdir ( tdir )
    os.chmod( newFile, 0o755 ) # 1877 is 0o755
    cmd = [ "sbatch" ]
    #cmd += [ "--error", f"{outputsdir}/validate-%j.out",
    #         "--output", f"{outputsdir}/validate-%j.out" ]
    cmd += [ "--error", f"{outputsdir}/{tempdir}.out",
             "--output", f"{outputsdir}/{tempdir}.out" ]
    # cmd += [ "--ntasks-per-node", str(nproc) ]
    if True:
        # time = 48
        qos = "c_short"
        if time > 48:
            qos = "c_long"
        if 8 < time <= 48:
            qos = "c_medium"
        cmd += [ "--qos", qos ]
        cmd += [ "--time", "%s" % ( time*60-1 ) ]
    #ram = 1. * nproc
    # ram = int ( 12. + .8 * nproc ) # crazy high, no
    ram = int ( 5. + .7 * nprocesses )
    # ncpus = nproc # int(nproc*1.5)
    ncpus = int(nprocesses*4)
    cmd += [ "--mem", f"{ram}G" ]
    cmd += [ "-c", f"{ncpus}" ] # allow for 200% per process
    cmd += [ newFile ]
    # cmd += [ "./run_bakery.sh" ]
    print ( f"[slurm_validate.py] validating {' '.join ( cmd )}" )
    if not dry_run:
        a=subprocess.run ( cmd )
        print ( "returned: %s" % a )
    #cmd = "rm %s" % tmpfile
    #o = subprocess.getoutput ( cmd )
    #print ( "[slurm_validate.py] %s %s" % ( cmd, o ) )

def logCall ():
    logfile = f"{os.environ['HOME']}/validate.log"
    line = ""
    for i in sys.argv:
        if " " in i or "," in i:
            i = '"%s"' % i
        line += i + " "
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
    f.write ( f"[slurm_validate.py-{time.strftime('%H:%M:%S')}] {line}\n" )
    f.close()

def clean():
    files = glob.glob ( f"{codedir}/smodels-utils/validation/tmp*" )
    files += glob.glob ( f"{codedir}/smodels-utils/clip/temp/_V*" )
    files += glob.glob ( f"{outputsdir}/validate*out" )
    for f in files:
        if os.path.exists ( f ):
            if os.path.isdir ( f ):
                shutil.rmtree ( f, ignore_errors=True )
            else:
                os.unlink ( f )

def main():
    import argparse
    argparser = argparse.ArgumentParser(description="slurm-run the validation process")
    argparser.add_argument ( '-d','--dry_run', help='dry-run, dont actually call srun',
                             action="store_true" )
    argparser.add_argument ( '-c','--clean', help='clean out all temp files',
                             action="store_true" )
    argparser.add_argument ( '-a', '--analyses', help='analyses considered [None]',
                        type=str, default=None )
    argparser.add_argument ( '-k','--keep',
            help='keep the temporary files,do not remove them afterwards',
            action="store_true" )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?',
            help='number of processes to run [10]',
            type=int, default=10 )
    argparser.add_argument ( '-m', '--model', nargs='?',
            help='model to use [default]',
            type=str, default="default" )
    argparser.add_argument ( '-g', '--generate_data', nargs='?',
            help='generateData [False,True,ondemand]. In combination with --repeat we switch to ondemand after the first [ondemand]',
            type=str, default="ondemand" )
    argparser.add_argument ( '-T', '--topo', help='topology considered [None]',
                        type=str, default=None )
    argparser.add_argument ( '-V', '--validate', help='run validation with ini file that resides in smodels-utils/validation/inifiles/ [default.ini]',
                        type=str, default = "default.ini" )
    argparser.add_argument ( '--tempname', help='name of temp files to use, without extension, e.g. _Vx9fmn28x. Files and folders will be named accordingly. None for random temp name. Use this for multi-cpu mode [None]',
                        type=str, default = None )
    argparser.add_argument ( '--validationfolder', help='the name of the validation folder [validation]',
                        type=str, default = None )
    argparser.add_argument ( '-t', '--time', nargs='?', help='time in hours [8]',
                        type=int, default=8 )
    argparser.add_argument ( '-l', '--limit_points', help='run over no more than many points [all]',
                        type=int, default=0 )
    argparser.add_argument ( '--dataselector', help='dataselector, eg combined, efficiencyMap, upperLimit [combined]',
                        type=str, default="combined" )
    argparser.add_argument ( '-r', '--repeat', nargs='?', help='repeat submission n times [1]',
                        type=int, default=1 )
    argparser.add_argument ( '--cancel_all', help='cancel all validaters',
            action="store_true" )
    argparser.add_argument ( '--cancel', help='cancel a certain range of validaters, e.g "65461977-65461985"',
            type=str, default = None )
    argparser.add_argument ( '-q','--query',
            help='query status, dont actually run', action="store_true" )
    args=argparser.parse_args()
    if args.clean:
        clean()
        sys.exit()
    if args.query:
        queryStats ( )
        sys.exit()
    if args.cancel:
        cancelRangerOfValiders ( args.cancel )
        return
    if args.cancel_all:
        cancelAllValidaters()
        return
    mkdir ( outputsdir )
    if args.keep:
        ## when running with --keep, we might want to
        ## remove smodels-utils/validation/<tempname> first.
        valdir = f"{codedir}/smodels-utils/validation/{args.tempname}".replace("//","/")
        parfile = f"{valdir}/results/parameter.ini"
        parfile = parfile.replace("//","/")
        valdirExists = os.path.exists ( parfile )
        valdirExists = False
        if valdirExists:
            print ( f"[slurm_validate] asked for continuation but {parfile} exists" )
            answ = input ( f"[slurm_validate] do you wish to remove the folder and continue? [y|N]" )
            if answ.lower() == "y":
                cmd = f"rm -rf {valdir}"
                print ( f"[slurm_validate] cmd: {cmd}" )
                o = subprocess.getoutput ( cmd )
            else:
                print ( f"[slurm_validate] stopping execution." )
                sys.exit()
        valdictFile = f"{codedir}/smodels-database/"
        valdictFileExists = False
        ## when running with --keep, we might want to remove the
        ## remove smodels-database/**/T*py first
        ## FIXME not yet implemented!
        if valdictFileExists:
            print ( f"[slurm_validate] asked for continuation but {valdictFile} exists"  )
            sys.exit()
    # print ( f"breaking after" )
    # sys.exit()
    if args.repeat > 1:
        args.keep = True
    for i in range(args.repeat):
        validate ( vars ( args ), i )
        args.generate_data = "ondemand"
    logCall()

if __name__ == "__main__":
    if "BOOST_ROOT" in os.environ and "1.74" in os.environ["BOOST_ROOT"]:
        print ( f"[slurm_validate] I think you have the wrong environment!" )
        sys.exit()
    main()
