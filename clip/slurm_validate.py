#!/usr/bin/env python3

from __future__ import print_function
import tempfile, argparse, stat, os, math, sys, time, glob, colorama, random
try:
    import commands as subprocess
except:
    import subprocess

def remove( fname, keep):
    ## remove filename if exists
    if not os.path.exists ( fname ):
        return
    if keep:
        return
    try:
        if True:
            os.unlink ( fname )
    except:
        pass

codedir = "/scratch-cbe/users/wolfgan.waltenberger/git"

def mkdir ( Dir ):
    if not os.path.exists ( Dir ):
        cmd = f"mkdir {Dir}"
        subprocess.getoutput ( cmd )

def getDirname ( rundir ):
    """ get the directory name of rundir, e.g.:
        /scratch-cbe/users/wolfgan.waltenberger/rundir.fake1 -> fake1
    """
    ret = rundir
    if ret.endswith("/"):
         ret = ret[:-1]
    p = ret.rfind("/")
    if p>-1:
         ret = ret[p+1:]
    ret = ret.replace("rundir.","")
    return ret

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
    with open ( "%s/smodels-utils/validation/inifiles/%s" % ( codedir, inifile ), 
                "rt" ) as f:
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
    cmd += [ "--error", "/scratch-cbe/users/wolfgan.waltenberger/outputs/validate-%j.out",
             "--output", "/scratch-cbe/users/wolfgan.waltenberger/outputs/validate-%j.out" ]
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
    ram = 4. + .2 * nproc
    ncpus = nproc # int(nproc*1.5)
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

def getNEvents ( recipe ):
    """ given a recipe, get the number of events pledged.
        used for estimating resources """
    try:
        tokens = recipe.split(" ")
        if "@n" in tokens:
            idx = tokens.index ( "@n" )
            if len(tokens)>idx+1:
                ret = int ( tokens[idx+1] )
                return ret
    except Exception as e:
        print ( f"[slurm] {e}" )
    return 10000

def clean_dirs( rundir, clean_all = False, verbose=True ):
    cmd = "rm slurm*out"
    o = subprocess.getoutput ( cmd )
    # cmd = "cd %s; rm -rf old*hi .*slha H*hi ssm*pcl *old *png decays* states.dict hiscore.hi Kold.conf Zold.conf RUN* *log ../outputs/slurm-*.out" % rundir
    cmd = "cd %s; rm -rf old*hi .*slha H*hi ssm*pcl *old *png decays* states.dict hiscore.hi Kold.conf Zold.conf RUN* xsec* llhdscanner*sh ~/git/smodels-utils/clip/temp ~/git/smodels-utils/validation/tmp* ~/git/smodels-utils/validation/_V* ~/git/smodels-utils/validation/*crash $OUTPUTS" % rundir
    if clean_all:
        # cmd = "cd %s; rm -rf old*pcl H*hi hiscore*hi .cur* .old* .tri* .*slha M*png history.txt pmodel-*py pmodel.py llhd*png decays* RUN*.sh ruler* rawnumb* *tex hiscore.log hiscore.slha *html *png *log RUN* walker*log training*gz Kold.conf Zold.conf ../outputs/slurm-*.out" % rundir
        cmd = "cd %s; rm -rf old*pcl H*hi hiscore*hi .cur* .old* .tri* .*slha M*png history.txt pmodel-*py pmodel.py llhd*png decays* RUN*.sh ruler* rawnumb* *tex hiscore.log hiscore.slha *html *png *log RUN* walker*log training*gz Kold.conf Zold.conf xsec* llhdscanner*sh hiscores.dict Kold.conf Kmin.conf" % rundir
    if verbose:
        print ( "[slurm.py] %s" % cmd )
    o = subprocess.getoutput ( cmd )

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

def main():
    import argparse
    argparser = argparse.ArgumentParser(description="slurm-run the validation process")
    argparser.add_argument ( '-d','--dry_run', help='dry-run, dont actually call srun',
                             action="store_true" )
    argparser.add_argument ( '-a', '--analyses', help='analyses considered in EM baking and validation [None]',
                        type=str, default=None )
    argparser.add_argument ( '-k','--keep',
            help='keep the shell scripts that are being run, do not remove them afters',
            action="store_true" )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?',
            help='number of processes to split task up to, 0 means one per worker [0]',
            type=int, default=0 )
    argparser.add_argument ( '-T', '--topo', help='topology considered in EM baking and validation [None]',
                        type=str, default=None )
    argparser.add_argument ( '-V', '--validate', help='run validation with ini file that resides in smodels-utils/validation/inifiles/',
                        type=str, default=None )
    argparser.add_argument ( '-t', '--time', nargs='?', help='time in hours [48]',
                        type=int, default=48 )
    args=argparser.parse_args()
    mkdir ( "/scratch-cbe/users/wolfgan.waltenberger/outputs/" )
    if args.validate != None:
        nproc = 20
        if args.nprocesses > 0:
            nproc = args.nprocesses
        validate ( args.validate, args.dry_run, nproc, args.time, args.analyses, 
                   args.topo )

if __name__ == "__main__":
    main()
