#!/usr/bin/env python3

"""
the script to start all results validation jobs with 

"""

import tempfile, argparse, stat, os, math, sys, time, glob, subprocess, shutil
from typing import Union

codedir = "/scratch-cbe/users/wolfgan.waltenberger/git"
if "CODEDIR" in os.environ:
    codedir = os.environ["CODEDIR"]

def mkdir ( Dir ):
    if not os.path.exists ( Dir ):
        cmd = f"mkdir {Dir}"
        subprocess.getoutput ( cmd )

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

def getNProcesses ( nprocesses, inifile ):
    if nprocesses > 0:
        return nprocesses
    inipath = f"{codedir}/smodels-utils/validation/inifiles/{inifile}"
    if not os.path.exists ( inipath ):
        print ( f"[slurm_validate] error: cannot find {inipath}" )
        sys.exit()
    f = open ( inipath, "rt" )
    ncpus = 1
    for line in f.readlines():
        if not "ncpus" in line:
            continue
        p1 = line.find("=")
        p2 = line.find(";")
        token = line[p1+1:p2]
        token = token.strip()
        ncpus = int(token)/2# *2
    return ncpus

def validate ( inifile, dry_run, nproc, time, analyses, topo,
               keep : bool, tempname : Union[None,str] ):
    """ run validation with ini file 
    :param inifile: ini file, should reside in smodels-utils/validation/
    :param dry_run: dont do anything, just produce script
    :param nproc: number of processes, typically 5
    :param time: time in hours
    :param analyses: string that replaces @@ANALYSES@@ in inifile
    :param topo: string that replaces @@TOPOS@@ in inifile
    :param keep: keep temporary files
    :param tempname: if not None, use this for the temp files names
    """
    if topo in [ None, "all" ]:
        topo = "*"
    if analyses == None:
        analyses = "all"
    print ( f"[slurm.py] run validation with {inifile}" )
    Dir = f"{codedir}/smodels-utils/clip/temp/"
    if not os.path.exists ( Dir ):
        os.mkdir ( Dir )
    with open ( f"{codedir}/smodels-utils/validation/inifiles/{inifile}", "rt" ) as f:
        lines = f.readlines()
        f.close()
    if tempname is None:
        newini = tempfile.mktemp(prefix="_V",suffix=".ini",dir=Dir )
    else:
        newini = f"{Dir}/{tempname}.ini"
    tempdir = os.path.basename ( newini ).replace(".ini","") # .replace("_V","tmp")
    # if possible name the tempdir the same as the temp script and the temp ini file
    skeep = ""
    if keep:
        skeep = "--keep --cont"
    with open ( newini, "wt" ) as f:
        for line in lines:
            newline = line.replace("@@ANALYSES@@", analyses )
            newline = newline.replace("@@TOPO@@", topo )
            newline = newline.replace("@@TEMPDIR@@", tempdir )
            f.write ( newline )
        f.close()

    with open ( f"{codedir}/smodels-utils/clip/validate_template.sh", "rt" ) as f:
        lines = f.readlines()
        f.close()
    # filename = tempfile.mktemp(prefix="_V",suffix=".sh",dir="")
    filename = os.path.basename ( newini ).replace(".ini",".sh")
    newFile = f"{Dir}/{filename}"
    print ( f"[slurm.py] creating script at {newFile}" )
    nprc = nproc #  int ( math.ceil ( nproc * .5  ) )
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
    outdir = "/scratch-cbe/users/wolfgan.waltenberger/outputs"
    #cmd += [ "--error", f"{outdir}/validate-%j.out",
    #         "--output", f"{outdir}/validate-%j.out" ]
    cmd += [ "--error", f"{outdir}/{tempdir}.out",
             "--output", f"{outdir}/{tempdir}.out" ]
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
    ram = int ( 3. + .5 * nproc )
    # ncpus = nproc # int(nproc*1.5)
    ncpus = int(nproc*4)
    cmd += [ "--mem", f"{ram}G" ]
    cmd += [ "-c", f"{ncpus}" ] # allow for 200% per process
    cmd += [ newFile ]
    # cmd += [ "./run_bakery.sh" ]
    print ( f"[slurm.py] validating {' '.join ( cmd )}" )
    if not dry_run:
        a=subprocess.run ( cmd )
        print ( "returned: %s" % a )
    #cmd = "rm %s" % tmpfile
    #o = subprocess.getoutput ( cmd )
    #print ( "[slurm.py] %s %s" % ( cmd, o ) )

def logCall ():
    logfile = f"{os.environ['HOME']}/slurm_validate.log"
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
    files += glob.glob ( f"{os.environ['OUTPUTS']}/validate*out" )
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
    argparser.add_argument ( '-a', '--analyses', help='analyses considered in EM baking and validation [None]',
                        type=str, default=None )
    argparser.add_argument ( '-k','--keep',
            help='keep the temporary files,do not remove them afterwards',
            action="store_true" )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?',
            help='number of processes to split task up to, 0 means as specified in inifile [0]',
            type=int, default=0 )
    argparser.add_argument ( '-T', '--topo', help='topology considered in EM baking and validation [None]',
                        type=str, default=None )
    argparser.add_argument ( '-V', '--validate', help='run validation with ini file that resides in smodels-utils/validation/inifiles/ [combined.ini]',
                        type=str, default = "combined.ini" )
    argparser.add_argument ( '--tempname', help='name of temp files to use, without extension, e.g. _Vx9fmn28x. Files and folders will be named accordingly. None for random temp name. Use this for multi-cpu mode [None]',
                        type=str, default = None )
    argparser.add_argument ( '-t', '--time', nargs='?', help='time in hours [8]',
                        type=int, default=8 )
    argparser.add_argument ( '-q','--query',
            help='query status, dont actually run', action="store_true" )
    args=argparser.parse_args()
    if args.clean:
        clean()
        sys.exit()
    if args.query:
        queryStats ( )
        sys.exit()
    mkdir ( "/scratch-cbe/users/wolfgan.waltenberger/outputs/" )
    nproc = getNProcesses ( args.nprocesses, args.validate )
    validate ( args.validate, args.dry_run, nproc, args.time, args.analyses, 
               args.topo, args.keep, args.tempname )
    logCall()

if __name__ == "__main__":
    if "BOOST_ROOT" in os.environ and "1.74" in os.environ["BOOST_ROOT"]:
        print ( f"[slurm_validate] I think you have the wrong environment!" )
        sys.exit()
    main()
