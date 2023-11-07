#!/usr/bin/env python3

import tempfile, argparse, stat, os, math, sys, time, glob, subprocess, shutil
"""
try:
    import commands as subprocess
except:
    import subprocess
"""

codedir = "/scratch-cbe/users/wolfgan.waltenberger/git"

def mkdir ( Dir ):
    if not os.path.exists ( Dir ):
        cmd = f"mkdir {Dir}"
        subprocess.getoutput ( cmd )

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
        ncpus = int(token)*2
    return ncpus

def validate ( inifile, dry_run, nproc, time, analyses, topo ):
    """ run validation with ini file 
    :param inifile: ini file, should reside in smodels-utils/validation/
    :param dry_run: dont do anything, just produce script
    :param nproc: number of processes, typically 5
    :param time: time in hours
    :param analyses: string that replaces @@ANALYSES@@ in inifile
    :param topo: string that replaces @@TOPOS@@ in inifile
    """
    if topo in [ None, "all" ]:
        topo = "*"
    if analyses == None:
        analyses = "all"
    print ( f"[slurm.py] run validation with {inifile}" )
    Dir = "%s/smodels-utils/clip/temp/" % codedir
    if not os.path.exists ( Dir ):
        os.mkdir ( Dir )
    with open ( f"{codedir}/smodels-utils/validation/inifiles/{inifile}", "rt" ) as f:
        lines = f.readlines()
        f.close()
    newini = tempfile.mktemp(prefix="_V",suffix=".ini",dir=Dir )
    tempdir = os.path.basename ( newini ).replace(".ini","") # .replace("_V","tmp")
    # if possible name the tempdir the same as the temp script and the temp ini file
    with open ( newini, "wt" ) as f:
        for line in lines:
            newline = line.replace("@@ANALYSES@@", analyses )
            newline = newline.replace("@@TOPO@@", topo )
            newline = newline.replace("@@TEMPDIR@@", tempdir )
            f.write ( newline )
        f.close()

    with open ( "%s/smodels-utils/clip/validate_template.sh" % codedir, "rt" ) as f:
        lines = f.readlines()
        f.close()
    # filename = tempfile.mktemp(prefix="_V",suffix=".sh",dir="")
    filename = os.path.basename ( newini ).replace(".ini",".sh")
    print ( "[slurm.py] creating script at %s/%s" % ( Dir, filename ) )
    nprc = nproc #  int ( math.ceil ( nproc * .5  ) )
    newFile = f"{Dir}/{filename}"
    with open ( newFile, "wt" ) as f:
        for line in lines:
            newline = line.replace("@@INIFILE@@", newini )
            newline = newline.replace("@@ANALYSES@@", analyses )
            newline = newline.replace("@@TOPO@@", topo )
            newline = newline.replace("@@ORIGINIFILE@@", inifile  )
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
    ram = 12. + .8 * nproc
    # ncpus = nproc # int(nproc*1.5)
    ncpus = int(nproc*2)
    if "combined" in inifile or "spey" in inifile:
        ram = 2 * ram
    cmd += [ "--mem", "%dG" % ram ]
    cmd += [ "-c", "%d" % ( ncpus ) ] # allow for 200% per process
    cmd += [ newFile ]
    # cmd += [ "./run_bakery.sh" ]
    print ("[slurm.py] validating %s" % " ".join ( cmd ) )
    if not dry_run:
        a=subprocess.run ( cmd )
        print ( "returned: %s" % a )
    #cmd = "rm %s" % tmpfile
    #o = subprocess.getoutput ( cmd )
    #print ( "[slurm.py] %s %s" % ( cmd, o ) )

def logCall ():
    f=open("slurm.log","at")
    args = ""
    for i in sys.argv:
        if " " in i or "," in i:
            i = '"%s"' % i
        args += i + " "
    f.write ("[slurm.py-%s] %s\n" % ( time.strftime("%H:%M:%S"), args.strip() ) )
    # f.write ("[slurm.py] %s\n" % " ".join ( sys.argv ) )
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
            help='keep the shell scripts that are being run, do not remove them afters',
            action="store_true" )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?',
            help='number of processes to split task up to, 0 means as specified in inifile [0]',
            type=int, default=0 )
    argparser.add_argument ( '-T', '--topo', help='topology considered in EM baking and validation [None]',
                        type=str, default=None )
    argparser.add_argument ( '-V', '--validate', help='run validation with ini file that resides in smodels-utils/validation/inifiles/ [combined.ini]',
                        type=str, default = "combined.ini" )
    argparser.add_argument ( '-t', '--time', nargs='?', help='time in hours [48]',
                        type=int, default=48 )
    args=argparser.parse_args()
    if args.clean:
        clean()
        sys.exit()
    mkdir ( "/scratch-cbe/users/wolfgan.waltenberger/outputs/" )
    nproc = getNProcesses ( args.nprocesses, args.validate )
    validate ( args.validate, args.dry_run, nproc, args.time, args.analyses, 
               args.topo )
    logCall()

if __name__ == "__main__":
    main()
