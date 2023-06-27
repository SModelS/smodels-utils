#!/usr/bin/env python3

from __future__ import print_function
import tempfile, argparse, stat, os, math, sys, time, glob, colorama, random
try:
    import commands as subprocess
except:
    import subprocess

codedir = "/scratch-cbe/users/wolfgan.waltenberger/git"

def mkdir ( Dir ):
    if not os.path.exists ( Dir ):
        cmd = f"mkdir {Dir}"
        subprocess.getoutput ( cmd )

def bake ( analyses, mass, topo, nevents, dry_run, nproc, cutlang,
           time, doLog = True ):
    """ bake with the given recipe
    :param analyses: eg "cms_sus_16_033,atlas_susy_2016_07"
    :param topo: eg T3GQ
    :param mass: eg [(50,4500,200),(50,4500,200),(0.)]
    :param nevents: number of events
    :param dry_run: dont do anything, just produce script
    :param nproc: number of processes, typically 5
    :param cutlang: if true, then use cutlang
    :param time: time in hours
    :param doLog: do write out bake-*.out log files
    """
    with open ( f"{codedir}/smodels-utils/clip/bake_template.sh", "rt" ) as f:
        lines = f.readlines()
        f.close()
    #if "cutlang" in recipe and not cutlang:
    #    print ( f"[slurm.py] cutlang is mentioned in recipe but -l was not given. maybe use -l?" )
    #    sys.exit()

    filename = "bake.sh"
    filename = tempfile.mktemp(prefix="_B",suffix=".sh",dir="")
    Dir = "%s/smodels-utils/clip/temp/" % codedir
    if not os.path.exists ( Dir ):
        os.mkdir ( Dir )
    print ( "[slurm.py] creating script at %s/%s" % ( Dir, filename ) )
    # nprc = int ( math.ceil ( nproc * .5  ) )
    with open ( "%s/%s" % ( Dir, filename ), "wt" ) as f:
        for line in lines:
            args = f'-a -n {nevents} --topo {topo} -p {nproc} -m "{mass}"'
            args += f' --analyses "{analyses}"'
            # args += ' -b'
            if cutlang:
                args += ' --cutlang'
            f.write ( line.replace("@@ARGS@@", args ) )
        f.close()
    templatefile = f"{codedir}/smodels-utils/clip/run_bakery_template.sh"
    with open ( templatefile, "rt" ) as f:
        lines = f.readlines()
        f.close()
    tdir = "./temp"
    if not os.path.exists ( tdir ):
        os.mkdir ( tdir )
    tmpfile = tempfile.mktemp(prefix="B", suffix=".sh",dir=tdir )
    with open ( tmpfile, "wt" ) as f:
        for line in lines:
            f.write ( line.replace ( "@@SCRIPT@@", filename ) )
        f.write ( f"# this script will perform:\n" )
        line = f'./bake.py -a -n {nevents} -t {topo} -m "{mass}" --analyses "{analyses}" -p {nproc}'
        if cutlang:
            line += ' --cutlang'
        f.write ( f"# {line}\n" )
        f.close()
    os.chmod( tmpfile, 0o755 ) # 1877 is 0o755
    os.chmod( Dir+filename, 0o755 ) # 1877 is 0o755
    cmd = [ "sbatch" ]
    if doLog:
        cmd += [ "--error", "/scratch-cbe/users/wolfgan.waltenberger/outputs/bake-%j.out",
             "--output", "/scratch-cbe/users/wolfgan.waltenberger/outputs/bake-%j.out" ]
    else:
        cmd += [ "--error",  "/dev/null",
                 "--output", "/dev/null" ]
    if True:
        # time = 48
        qos = "c_short"
        if time > 48:
            qos = "c_long"
        if 8 < time <= 48:
            qos = "c_medium"
        cmd += [ "--qos", qos ]
        cmd += [ "--time", "%s" % ( time*60-1 ) ]
    # ma5 seems to not need much RAM
    ram = 2.5 * nproc
    if nevents > 50000:
        ram = 3. * nproc
    ncpus = int(nproc*1.5)
    if cutlang:
        ram = 2.5 * nproc ## in GB
        ncpus = int(nproc*2)
    cmd += [ "--mem", "%dG" % ram ]
    cmd += [ "-c", "%d" % ( ncpus ) ] # allow for 200% per process
    cmd += [ tmpfile ]
    # cmd += [ "./run_bakery.sh" ]
    print ("[slurm.py] baking %s" % " ".join ( cmd ) )
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

def main():
    import argparse
    argparser = argparse.ArgumentParser(description="slurm-run a walker")
    argparser.add_argument ( '--dontlog',
            help='dont produce bakery log files',
            action="store_true" )
    argparser.add_argument ( '-d','--dry_run', help='dry-run, dont actually call srun',
                             action="store_true" )
    argparser.add_argument ( '-k','--keep',
            help='keep the shell scripts that are being run, do not remove them afters',
            action="store_true" )
    argparser.add_argument ( '-B', '--nbakes', nargs="?",
                    help='launch n identical jobs',
                    type=int, default=1 )
    argparser.add_argument ( '-n', '--nevents', nargs="?",
                    help='number of events to be generated',
                    type=int, default=1000 )
    argparser.add_argument ( '-m', '--mass', nargs="?",
                    help='bake EM maps, mass specification, for baking only [(50,4500,200),(50,4500,200),(0.)]',
                    type=str, default="default" )
    argparser.add_argument ( '-t', '--time', nargs='?', help='time in hours [48]',
                        type=int, default=48 )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?',
            help='number of processes to split task up to, 0 means one per worker [0]',
            type=int, default=0 )
    argparser.add_argument ( '-a', '--analyses', help='analyses considered in EM baking and validation [None]',
                        type=str, default=None )
    argparser.add_argument ( '-l', '--cutlang', help='use cutlang for baking',
                             action='store_true' )
    argparser.add_argument ( '-T', '--topo', help='topology considered in EM baking and validation [None]',
                        type=str, default=None )
    args=argparser.parse_args()
    doLog = not args.dontlog
    if args.mass == "default":
        # args.mass = "[(300,1099,25),'half',(200,999,25)]"
        args.mass = "[(50,4500,200),(50,4500,200),(0.)]"
    for i in range(args.nbakes):
        bake ( args.analyses, args.mass, args.topo, args.nevents, args.dry_run,
               args.nprocesses, args.cutlang, args.time, doLog )
    logCall()

if __name__ == "__main__":
    main()
