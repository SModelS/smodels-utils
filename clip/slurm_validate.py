#!/usr/bin/env python3

"""
the script to start all results validation jobs with 

"""

import tempfile, argparse, stat, os, math, sys, time, glob, subprocess, shutil
from smodels_utils.helper.terminalcolors import *
from typing import Union, Dict
from cliphelpers import SQUEUE

codedir = f"/scratch/users/{os.environ['USER']}/git"
outputsdir = f"/scratch/users/{os.environ['USER']}/outputs/"
if os.path.exists ( "/scratch-cbe/" ): # old cluster
    codedir = f"/scratch-cbe/users/{os.environ['USER']}/git"
    outputsdir = f"/scratch-cbe/users/{os.environ['USER']}/outputs/"
if "CODEDIR" in os.environ:
    codedir = os.environ["CODEDIR"]
if "OUTPUTS" in os.environ:
    outputsdir = os.environ["OUTPUTS"]

def mkdir ( Dir : os.PathLike ):
    if not os.path.exists ( Dir ):
        cmd = f"mkdir {Dir}"
        subprocess.getoutput ( cmd )

def cancelAllValidaters():
    o = subprocess.getoutput ( f"{SQUEUE} | grep _V" )
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
    o = subprocess.getoutput ( f"{SQUEUE} | grep _V" )
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
    o = subprocess.getoutput ( f"{SQUEUE} | grep _V" )
    lines = o.split("\n")
    nmin = 1e99
    for line in lines:
        tokens = line.split()
        nr = int(tokens[0])
        if nr < nmin:
            nmin = nr
    return nmin

def cancelRangeOfValidaters( jrange : str ):
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
    o = subprocess.getoutput ( f"{SQUEUE} | grep _V" )
    lines = o.split("\n")
    running = []
    for line in lines:
        if not "_V" in line:
            continue
        tokens = line.split()
        nr = tokens[0]
        running.append ( int ( nr ) )
    if p1 == 0:
        cancelRangeOfValidaters( f"{min(running)}-{jrange[p1+1:]}" )
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

def usesHS3 ( analyses : Union[None,str], databasepath : Union[None,str] = None ) -> bool:
    """ check if any analysis to be validated has an HS3 statistical model.

        HS3 models are announced in the analysis' globalInfo.txt via statModels
        entries of type hs3/full_hs3 and/or by hs3 json files in the analysis
        folder. Checking those is cheap; loading the database with SModelS
        (which would also tell us this) is not.

        :param analyses: comma separated analyses as given to --analyses;
                         None, "all" or "*" means all analyses in the database
        :param databasepath: path to the database, as given to --databasepath.
                             Relative paths are interpreted relative to the
                             validation folder, just like in runValidation.py.
        :returns: True if at least one of the selected analyses uses HS3
    """
    import re, fnmatch
    if databasepath is None:
        databasepath = "../../smodels-database"
    dbpath = os.path.expandvars ( os.path.expanduser ( databasepath ) )
    if not os.path.isabs ( dbpath ):
        dbpath = os.path.abspath ( f"{codedir}/smodels-utils/validation/{dbpath}" )
    if not os.path.isdir ( dbpath ):
        print ( f"[slurm_validate.py] cannot look for HS3 models in {dbpath}: assuming none" )
        return False
    wanted = None
    if analyses not in [ None, "", "all", "*" ]:
        wanted = [ a.strip() for a in analyses.split(",") if a.strip() ]
    def isSelected ( aid, dirname ):
        if wanted is None:
            return True
        for pattern in wanted:
            if ( fnmatch.fnmatchcase ( aid, pattern ) or
                 fnmatch.fnmatchcase ( dirname, pattern ) or
                 aid.startswith ( pattern ) or
                 dirname.startswith ( pattern ) ):
                return True
        return False
    for dirpath, dirnames, filenames in os.walk ( dbpath ):
        dirnames[:] = [ d for d in dirnames if d != ".git" ]
        dirname = os.path.basename ( dirpath )
        globalInfo = os.path.join ( dirpath, "globalInfo.txt" )
        content = ""
        if os.path.exists ( globalInfo ):
            with open ( globalInfo, "rt", errors="ignore" ) as f:
                content = f.read()
        match = re.search ( r"^\s*id\s*:\s*(\S+)", content, re.MULTILINE )
        aid = match.group(1) if match else dirname
        if not isSelected ( aid, dirname ):
            continue
        ## e.g. statModels: { 'all': [ ( 'full_hs3', 'hs3_model.json' ) ] }
        for line in content.splitlines():
            if "hs3" in line.lower() and "statmodels" in line.lower():
                return True
        ## e.g. hs3_model.json or bOnlyFit_postFit__w.hs3.json
        if glob.glob ( os.path.join ( dirpath, "*hs3*.json" ) ):
            return True
    return False

def validate ( args : Dict, idx ) -> Union[None,int]:
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
    :param databasepath: string that replaces @@DATABASEPATH@@ in inifile
    :param spey: use spey, replace @@SPEY@@ in inifile
    :param expectationType: expectationType, replace @@EXPECTATIONTYPE@@ in inifile
    :param limit_points: run over only that many points
    :param model: the model to use (default)
  
    :param idx: 0 for the first job, 1 for all others
    :returns: jobid
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
    databasepath = args["databasepath"]
    spey = args["spey"]
    expectationType = args["expectationType"]
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
        #if spey:
        #    newini = newini.replace(".ini", ".spey.ini" )
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
            if args["model"] in [ "omit", "default" ] and "@@MODEL@@" in newline:
                newline = "" ## omit model line altogether
            newline = newline.replace("@@MODEL@@", args["model"] )
            if args["axis"] in [ "omit", "default", None ] and "@@AXIS@@" in newline:
                newline = "" ## omit axis line altogether
            if "@@USEFULLJSONLIKELIHOODS@@" in newline and args["usefulljsonlikelihoods"]==False:
                newline = ""
            else:
                newline = newline.replace ( "@@USEFULLJSONLIKELIHOODS@@", "True" )
            newline = newline.replace("@@AXIS@@",  args["axis"] )
            newline = newline.replace("@@TIMEOUT@@", "30000" )
            newline = newline.replace("@@VALIDATIONFOLDER@@", validationfolder )
            newline = newline.replace("@@DATABASEPATH@@", databasepath )
            newline = newline.replace("@@SPEY@@", str(spey) )
            newline = newline.replace("@@EXPECTATIONTYPE@@", expectationType )
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
    # monkey_patch = ""
    #
    #if "monkey_patch" in args and args["monkey_patch"]==True:
    #    monkey_patch = "--monkey_patch"
    python_exe = f"{os.environ['HOME']}/.venvs/default/bin/python3"
    if not os.path.exists ( python_exe ):
        python_exe = "/usr/bin/env python3"
    if os.path.exists ( "/scratch-cbe" ):
        python_exe = "/usr/bin/env python3"
    ## all jobs but the first share binaryIdx 1 and thus the same script.
    ## Only write it when it does not exist yet (or its contents changed),
    ## otherwise --repeat would recreate the very same _1.sh over and over.
    script = ""
    for line in lines:
        newline = line.replace("@@INIFILE@@", newini )
        newline = newline.replace("@@CODEDIR@@", codedir )
        # newline = newline.replace("@@MONKEY_PATCH@@", monkey_patch )
        newline = newline.replace("@@ANALYSES@@", analyses )
        newline = newline.replace("@@TOPO@@", topo )
        newline = newline.replace("@@ORIGINIFILE@@", inifile  )
        newline = newline.replace("@@KEEP@@", skeep )
        newline = newline.replace("@@PYTHON_EXE@@", python_exe )
        script += newline
    needToWrite = True
    if os.path.exists ( newFile ):
        with open ( newFile, "rt" ) as f:
            needToWrite = f.read() != script
    if needToWrite:
        print ( f"[slurm_validate.py] creating script at {newFile}" )
        with open ( newFile, "wt" ) as f:
            f.write ( script )
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
        cmd += [ "--time", f"{time * 60 - 1}" ]
    #ram = 1. * nproc
    ## pyhs3 is RAM hungry, but only if the analysis actually uses an HS3 model
    hasHS3 = usesHS3 ( analyses, databasepath )
    if hasHS3:
        ram = int ( 12.0 + 4 * nprocesses )
    else:
        ram = int ( 2.5 + .6 * nprocesses )
    # print ( f"[slurm_validate.py] HS3 model: {hasHS3}, requesting {ram}G of RAM" )
    # ncpus = nproc # int(nproc*1.5)
    ncpus = int(nprocesses*2.5)
    cmd += [ "--mem", f"{ram}G" ]
    cmd += [ "-c", f"{ncpus}" ] # allow for 200% per process
    cmd += [ newFile ]
    # cmd += [ "./run_bakery.sh" ]
    print ( f"[slurm_validate.py] submitting {' '.join ( cmd )}" )
    if not dry_run:
        a=subprocess.run ( cmd, stdout=subprocess.PIPE )
        sjobid = str ( a.stdout.strip() ).split(" ")[-1]
        jobid = int ( sjobid.replace("'","") )
        #cmd = " ".join ( a.args )
        #print ( f"[slurm_validate.py] {cmd}" )
        srcode = ": success!"
        if a.returncode != 0:
            srcode = f": {RED}rcode={a.rcode}{RESET}"
        answer = a.stdout.decode('UTF-8').strip()
        answer = answer.replace('job ', 'job {GREEN}') + RESET
        print ( f"[slurm_validate.py] {answer}{srcode}"
        return jobid
    #cmd = "rm %s" % tmpfile
    #o = subprocess.getoutput ( cmd )
    #print ( "[slurm_validate.py] %s %s" % ( cmd, o ) )
    return None

def logCall ( jobids : list ):
    logfile = f"{os.environ['HOME']}/validate.log"
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
    f.write ( f"\n" )
    f.write ( f"# slurm_validate.py-{time.asctime()}\n" )
    f.write ( f"{line}\n" )
    s_jobids = ','.join(map(str,jobids))
    s_jobids = ""
    for i,jobid in enumerate(jobids):
        if i!=0:
            s_jobids += ", "
            if i % 6 == 0:
                s_jobids += "\n#         "
        s_jobids += str(jobid)
    if False:
        f.write ( f"# jobids: {s_jobids}\n\n" )
    f.close()

def clean():
    """ clean out the temporary files """
    files = glob.glob ( f"{codedir}/smodels-utils/validation/tmp*" )
    files += glob.glob ( f"{codedir}/smodels-utils/clip/temp/_V*" )
    files += glob.glob ( f"{outputsdir}/validate*out" )
    for f in files:
        if os.path.exists ( f ):
            print ( f"[slurm_validate] removing {f}" )
            if os.path.isdir ( f ):
                shutil.rmtree ( f, ignore_errors=True )
            else:
                os.unlink ( f )
def clean_more():
    """ be even more thorough when cleaning """
    files = glob.glob ( f"{os.environ['OUTPUTS']}/_V*" )
    files += glob.glob ( f"{codedir}/smodels-utils/validation/_V*" )
    for f in files:
        if os.path.exists ( f ):
            print ( f"[slurm_validate] removing {f}" )
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
    argparser.add_argument ( '-C','--clean_all', help='be thorough when cleaning',
                             action="store_true" )
    argparser.add_argument ( '-a', '--analyses', help='analyses considered [None]',
                        type=str, default=None )
    argparser.add_argument ( '-k','--keep',
            help='keep the temporary files,do not remove them afterwards',
            action="store_true" )
    argparser.add_argument ( '-j','--usefulljsonlikelihoods',
            help='use the json file specification given in the full json files (if defined)',
            action="store_true" )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?',
            help='number of processes to run [10]',
            type=int, default=10 )
    argparser.add_argument ( '-m', '--model', nargs='?',
            help='model to use (mssm,nmssm,idm,zprime,slha,omit) [omit]',
            type=str, default="omit" )
    argparser.add_argument ( '--axis', nargs='?',
            help='optionally specify the axis [omit]',
            type=str, default="omit" )
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
    argparser.add_argument ( '--databasepath', help='the path to the database [../../smodels-database]',
                        type=str, default = "../../smodels-database" )
    argparser.add_argument ( '--expectationType', help='expectationType used for eULs [aposteriori]',
                        type=str, default = "aposteriori" )
    argparser.add_argument ( '-t', '--time', nargs='?', help='time in hours [8]',
                        type=int, default=8 )
    argparser.add_argument ( '-l', '--limit_points', help='run over no more than many points [all]',
                        type=int, default=0 )
    argparser.add_argument ( '--dataselector', help='dataselector, eg combined, efficiencyMap, upperLimit [combined]',
                        type=str, default="combined" )
    argparser.add_argument ( '-r', '--repeat', nargs='?', help='repeat submission n times [1]',
                        type=int, default=1 )
    argparser.add_argument ( '--spey', help='use spey statistics',
            action="store_true" )
    argparser.add_argument ( '--cancel_all', help='cancel all validaters',
            action="store_true" )
    argparser.add_argument ( '--cancel', help='cancel a certain range of validaters, e.g "65461977-65461985"',
            type=str, default = None )
    argparser.add_argument ( '-q','--query',
            help='query status, dont actually run', action="store_true" )
    #argparser.add_argument ( '-M','--monkey_patch',
    #        help='monkey patch SModelS so we have nn errors', action="store_true" )
    args=argparser.parse_args()
    if args.usefulljsonlikelihoods and args.validationfolder == None:
        print ( f"[slurm_validate] full json likelihoods and no folder given: will change to validation/fullStats" )
        args.validationfolder = "validation/fullStats"
    if args.clean:
        clean()
        sys.exit()
    if args.clean_all:
        clean()
        clean_more()
        sys.exit()
    if args.query:
        queryStats ( )
        sys.exit()
    if args.cancel:
        cancelRangeOfValidaters ( args.cancel )
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
    jobids = []
    for i in range(args.repeat):
        jobid = validate ( vars ( args ), i )
        args.generate_data = "ondemand"
        if jobid != None:
            jobids.append ( jobid )
    logCall( jobids )

if __name__ == "__main__":
    if "BOOST_ROOT" in os.environ and "1.74" in os.environ["BOOST_ROOT"]:
        print ( f"[slurm_validate] I think you have the wrong environment!" )
        sys.exit()
    main()
