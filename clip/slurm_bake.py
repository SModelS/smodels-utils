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

def bake ( args : dict ):
    """ bake with the given recipe
    :param analyses: eg "cms_sus_16_033,atlas_susy_2016_07"
    :param topo: eg T3GQ
    :param mass: eg [(50,4500,200),(50,4500,200),(0.)]
    :param nevents: number of events
    :param dry_run: dont do anything, just produce script
    :param nproc: number of processes, typically 5
    :param cutlang: if true, then use cutlang
    :param checkmate: if true, then use checkmate
    :param time: time in hours
    :param doLog: do write out bake-*.out log files
    :param adl_file: specify path to adl file
    :param event_condition: optionally specify an event condition
    """
    with open ( f"{codedir}/smodels-utils/clip/bake_template.sh", "rt" ) as f:
        lines = f.readlines()
        f.close()
    nevents = args["nevents"]
    topo = args["topo"]
    nproc = args["nprocesses"]
    mass = args["mass"]
    dry_run = args["dry_run"]
    cutlang = args["cutlang"]
    checkmate = args["checkmate"]
    time = args["time"]
    doLog = not args["dontlog"]
    analyses = args["analyses"]
    event_condition = args["event_condition"]
    adl_file = args["adl_file"]

    filename = "bake.sh"
    filename = tempfile.mktemp(prefix="_B",suffix=".sh",dir="")
    Dir = f"{codedir}/smodels-utils/clip/temp/"
    if not os.path.exists ( Dir ):
        os.mkdir ( Dir )
    pathname = os.path.join ( Dir, filename )
    print ( f"[slurm.py] creating script at {pathname}: {len(lines)} lines." )
    with open ( pathname, "wt" ) as f:
        for line in lines:
            largs = f'-a -n {nevents} --topo {topo} -p {nproc} -m "{mass}"'
            largs += f' --analyses "{analyses}"'
            if cutlang:
                largs += ' --cutlang'
            if checkmate:
                largs += ' --checkmate'
            if event_condition is not None:
                event_condition = event_condition.replace("'",'"')
                pids = { "gamma": 22, "Z": 23, "higgs": 25 }
                for name,pid in pids.items():
                    event_condition = event_condition.replace ( name, str(pid) )
                largs += f" --event_condition '{event_condition}'"
            if adl_file is not None:
                adl_file = adl_file.replace("'",'').replace('"','')
                largs += f" --adl_file '{adl_file}'"
            if args["mingap1"] is not None:
                largs += f" --mingap1 {args['mingap1']}"
            if args["maxgap1"] is not None:
                largs += f" --maxgap1 {args['maxgap1']}"
            if args["mingap2"] is not None:
                largs += f" --mingap2 {args['mingap2']}"
            if args["maxgap2"] is not None:
                largs += f" --maxgap2 {args['maxgap2']}"
            if args["mingap13"] is not None:
                largs += f" --mingap13 {args['mingap13']}"
            if args["maxgap13"] is not None:
                largs += f" --maxgap13 {args['maxgap13']}"
            f.write ( line.replace("@@ARGS@@", largs ) )
        f.close()
    # the following is only needed with singularity containers! """
    """
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
        line = f'./bake.py {args}'
        f.write ( f"# {line}\n" )
        f.close()
    os.chmod( tmpfile, 0o755 ) # 1877 is 0o755
    """
    os.chmod( Dir+filename, 0o755 ) # 1877 is 0o755
    cmd = [ "sbatch" ]
    outputsdir = "/scratch-cbe/users/wolfgan.waltenberger/outputs/"
    mkdir ( outputsdir )
    if doLog:
        cmd += [ "--error", f"{outputsdir}/bake-%j.out",
                 "--output", f"{outputsdir}/bake-%j.out" ]
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
    if nevents >= 50000:
        ram = 3. * nproc
    if nevents >= 100000:
        ram = 4. * nproc
    ncpus = int(nproc*1.5)
    if cutlang:
        ram = 2.5 * nproc ## in GB
        ncpus = int(nproc*2)
    cmd += [ "--mem", "%dG" % ram ]
    cmd += [ "-c", "%d" % ( ncpus ) ] # allow for 200% per process
    # cmd += [ tmpfile ]
    cmd += [ Dir + filename ]
    print ( f'[slurm.py] baking {" ".join ( cmd )}' )
    if not dry_run:
        a=subprocess.run ( cmd )
        print ( f"[slurm.py] returned: {a}" )

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
    argparser.add_argument ( '--event_condition', nargs="?",
                    help='optionally specify an event condition',
                    type=str, default=None )
    argparser.add_argument ( '--adl_file', nargs="?",
                    help='optionally specify a path to the adl file',
                    type=str, default=None )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?',
            help='number of processes to split task up to, 0 means one per worker [0]',
            type=int, default=0 )
    argparser.add_argument ( '--maxgap2', help='maximum mass gap between second and third, to force offshell [None]',
                             type=float, default=None )
    argparser.add_argument ( '--mingap1', help='minimum mass gap between first and second, to force onshell or a mass hierarchy [None]',
                             type=float, default=None )
    argparser.add_argument ( '--mingap2', help='minimum mass gap between second and third, to force onshell or a mass hierarchy [None]',
                             type=float, default=None )
    argparser.add_argument ( '--mingap13', help='minimum mass gap between first and third, to force onshell or a mass hierarchy [None]',
                             type=float, default=None )
    argparser.add_argument ( '--maxgap13', help='maximum mass gap between first and third, to force offshell [None]',
                             type=float, default=None )
    argparser.add_argument ( '--maxgap1', help='maximum mass gap between first and second, to force offshell [None]',
                             type=float, default=None )
    argparser.add_argument ( '-a', '--analyses', help='analyses considered in EM baking and validation [None]',
                        type=str, default=None )
    argparser.add_argument ( '-l', '--cutlang', help='use cutlang for baking',
                             action='store_true' )
    argparser.add_argument ( '--checkmate', help='use checkmate for baking',
                             action='store_true' )
    argparser.add_argument ( '-T', '--topo', help='topology considered in EM baking and validation [None]',
                        type=str, default=None )
    args=argparser.parse_args()
    doLog = not args.dontlog
    if args.mass == "default":
        # args.mass = "[(300,1099,25),'half',(200,999,25)]"
        args.mass = "[(50,4500,200),(50,4500,200),(0.)]"
    for i in range(args.nbakes):
        bake ( vars(args) )
    logCall()

if __name__ == "__main__":
    main()
