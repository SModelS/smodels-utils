#!/usr/bin/env python3

from __future__ import print_function
import tempfile, argparse, stat, os, math, sys, time, glob, colorama, random
from typing import Dict

try:
    import commands as subprocess
except:
    import subprocess

codedir = "/scratch-cbe/users/wolfgan.waltenberger/git"

def queryStats ( maxsteps : int ):
    """ just give us the statistics """
    import running_stats
    running_stats.count_jobs( "_B" )
    running_stats.running_stats( "_B" )
    if maxsteps != None:
        for i in range(maxsteps):
            time.sleep(30.)
            print()
            running_stats.count_jobs()
            running_stats.running_stats()
            print()
    print ( )
    print ( "embaked files:" )
    print ( "==============" )
    embakedFiles = glob.glob ( f"{codedir}/em-creator/embaked/*.embaked" )
    for embakedFile in embakedFiles:
        name = embakedFile.replace(".embaked","")
        p1 = name.find("/embaked/")
        name = name[p1+9:]
        nlines = 0
        with open ( embakedFile, "rt" ) as f:
            nlines = len (f.readlines())
            f.close()
        print ( f"  - {name:40s} {nlines} points" )
    xmlFiles = f"{codedir}/em-creator/cm2/checkmate2/data/atlas_2010_14293/BDTxml/ZeroLepton2018-SRBDT-GGo4_weight1.xml"
    print ( )
    print ( f"has xml files: {os.path.exists(xmlFiles)}" )
    

def cancelAllBakers():
    o = subprocess.getoutput ( "slurm q | grep _B" )
    lines = o.split("\n")
    cancelled = []
    for line in lines:
        if not "_B" in line:
            continue
        tokens = line.split()
        nr = tokens[0]
        cmd = f"scancel {nr}"
        subprocess.getoutput ( cmd )
        cancelled.append ( nr )
    print ( f"[slurm_bake] cancelled {', '.join(cancelled)}" )


def mkdir ( Dir ):
    if not os.path.exists ( Dir ):
        cmd = f"mkdir {Dir}"
        subprocess.getoutput ( cmd )

def bake ( args : Dict ):
    """ bake with the given recipe
    :param analyses: eg "cms_sus_16_033,atlas_susy_2016_07"
    :param topo: eg T3GQ
    :param mass: eg [(50,4500,200),(50,4500,200),(0.)]
    :param nevents: number of events
    :param dry_run: dont do anything, just produce script
    :param nprocesses: number of processes, typically 5
    :param cutlang: if true, then use cutlang
    :param checkmate: if true, then use checkmate
    :param colliderbit: if true, then use colliderbit
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
    nprocesses = args["nprocesses"]
    mass = args["mass"]
    dry_run = args["dry_run"]
    cutlang = args["cutlang"]
    checkmate = args["checkmate"]
    colliderbit = args["colliderbit"]
    time = args["time"]
    keep = args["keep"]
    keephepmc = args["keephepmc"]
    doLog = not args["dontlog"]
    analyses = args["analyses"]
    event_condition = args["event_condition"]
    adl_file = args["adl_file"]
    njets = args["njets"]
    source_env = ""
    if colliderbit:
        source_env = f"source {codedir}/em-creator/utils/gambit_env.sh"

    filename = "bake.sh"
    filename = tempfile.mktemp(prefix="_B",suffix=".sh",dir="")
    Dir = f"{codedir}/smodels-utils/clip/temp/"
    if not os.path.exists ( Dir ):
        os.mkdir ( Dir )
    pathname = os.path.join ( Dir, filename )
    print ( f"[slurm.py] creating script at {pathname}: {len(lines)} lines." )
    # nprc = int ( math.ceil ( nproc * .5  ) )
    maxgaps = ""
    gaps = [ "maxgap1", "maxgap2", "maxgap13", "mingap1", "mingap2", "mingap13" ]
    for gap in gaps:
        if gap in args and args[gap]!=None:
            ngap = args[gap]
            maxgaps += f" --{gap} {ngap}"
    with open ( pathname, "wt" ) as f:
        for line in lines:
            largs = f'-a -b -n {nevents} --topo {topo} -p {nprocesses} -m "{mass}"'
            largs += f' --analyses "{analyses}"{maxgaps} --njets {njets}'
            # args += ' -b'
            if cutlang:
                largs += ' --cutlang'
            if checkmate:
                largs += ' --checkmate'
            if colliderbit:
                largs += ' --colliderbit'
            if keep:
                largs += ' --keep'
            if keephepmc:
                largs += ' --keephepmc'
            if event_condition is not None:
                event_condition = event_condition.replace("'",'"')
                pids = { "gamma": 22, "Z": 23, "higgs": 25 }
                for name,pid in pids.items():
                    event_condition = event_condition.replace ( name, str(pid) )
                largs += f" --event_condition '{event_condition}'"
            if adl_file is not None:
                adl_file = adl_file.replace("'",'').replace('"','')
                largs += f" --adl_file '{adl_file}'"
            line = line.replace("@@SOURCE_ENV@@", source_env )
            line = line.replace("@@ARGS@@", largs )
            f.write ( line )
            # f.write ( line )
        f.close()
    # the following is only needed with singularity containers! """
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
    ram = 2.5 * nprocesses
    if nevents >= 50000:
        ram = int ( 3. * nprocesses )
    if nevents >= 100000:
        ram = int ( 4. * nprocesses )
    ncpus = int(nprocesses*2)
    if cutlang:
        ram = 2.5 * nprocesses ## in GB
        ncpus = int(nprocesses*2)
    if checkmate:
        ram = int(2 * ram)
        ncpus = int(nprocesses*4)
    if colliderbit:
        ram = int(1.5 * ram)
        ncpus = int(nprocesses*4)
    cmd += [ "--mem", f"{int(ram)}G" ]
    cmd += [ "-c", f"{ncpus}" ] # allow for 200% per process
    # cmd += [ tmpfile ]
    cmd += [ Dir + filename ]
    print ( f'[slurm.py] baking {" ".join ( cmd )}' )
    if not dry_run:
        a=subprocess.run ( cmd )
        print ( f"returned: {a}" )
    #cmd = "rm %s" % tmpfile
    #o = subprocess.getoutput ( cmd )
    #print ( "[slurm.py] %s %s" % ( cmd, o ) )

def logCall ():
    logfile = f"{os.environ['HOME']}/slurm_bake.log"
    line = ""
    for i in sys.argv:
        if " " in i or "," in i:
            i = '"%s"' % i
        line += i + " "
    line = line.strip()
    lastline = ""
    if os.path.exists ( logfile ):
        f=open(logfile,"rt")
        lines = f.readlines()
        f.close()
        lastline = lines[-1].strip()
        p = lastline.find("]")
        lastline = lastline[p+2:]
    if line == lastline: # skip duplicates
        return
    f=open(logfile,"at")
    f.write ( f"[slurm_bake.py-{time.strftime('%H:%M:%S')}] {line}\n" )
    f.close()

def cancelRangeOfBakers( jrange : str ):
    """ cancel only the jrange of bakers """
    #print ( f"[slurm_bake] cancel {jrange}" )
    import re
    jrange = jrange.strip(" ")
    if re.search('[a-zA-Z]', jrange) is not None:
        from running_stats import cancelJobsByString
        return cancelJobsByString ( jrange )
    if not "-" in jrange: # single job
        cmd = f"scancel {jrange}"
        #print ( f"[slurm_bake] cmd {cmd}" )
        subprocess.getoutput ( cmd )
        #print ( f"[slurm_bake] cancelled {jrange}" )
        return
    cancelled = []
    p1 = jrange.find("-")
    if p1 == len(jrange)-1: ## range is given as '<min>-'
        maxJobId = getMaxJobId()
        jrange += str(maxJobId)
    elif p1 == 0:
        minJobId = getMinJobId()
        jrange = str(minJobId) + jrange
    else:
        # full range given
        jmin,jmax = int ( jrange[:p1] ), int ( jrange[p1+1:] )
        if jmax < jmin:
            print ( f"[slurm_bake] sth is wrong with the range: [{jmin},{jmax}]" )
            return

        for i in range(jmin,jmax+1):
            cmd = f"scancel {i}"
            #print ( f"[slurm_bake] cmd {cmd}" )
            subprocess.getoutput ( cmd )
            cancelled.append ( i )
        print ( f"[slurm_bake] cancelled {', '.join(map(str,cancelled))}" )
        return
    o = subprocess.getoutput ( "slurm q | grep _B" )
    lines = o.split("\n")
    running = []
    for line in lines:
        if not "_B" in line:
            continue
        tokens = line.split()
        nr = tokens[0]
        running.append ( int ( nr ) )
    if p1 == 0:
        cancelRangeOfBakers( f"{jrange}" )
        return
    if p1 == len(jrange)-1:
        cancelRangeOfBakers( f"{jrange}" )
        return
    print ( "[slurm_bake] FIXME sth is wrong" )

def getMaxJobId() -> int:
    """ get the highest job id """
    o = subprocess.getoutput ( "slurm q | grep _B" )
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
    o = subprocess.getoutput ( "slurm q | grep _B" )
    lines = o.split("\n")
    nmin = 1e99
    for line in lines:
        tokens = line.split()
        nr = int(tokens[0])
        if nr < nmin:
            nmin = nr
    return nmin

def main():
    import argparse
    argparser = argparse.ArgumentParser(description="slurm-run a baker")
    argparser.add_argument ( '-q','--query',
            help='query status, dont actually run (use -M to query repeatedly)',
            action="store_true" )
    argparser.add_argument ( '--dontlog',
            help='dont produce bakery log files',
            action="store_true" )
    argparser.add_argument ( '-d','--dry_run', help='dry-run, dont actually call srun',
                             action="store_true" )
    argparser.add_argument ( '-k','--keep',
            help='keep the shell scripts that are being run, do not remove them afters',
            action="store_true" )
    argparser.add_argument ( '-K','--keephepmc',
            help='keep hepmc files',
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
    argparser.add_argument ( '-j', '--njets', nargs='?', help='number of jets [1]',
                        type=int, default=1 )
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
    argparser.add_argument ( '-r', '--repeat', help='repeat the submission <r> times [1]',
                             type=int, default=1 )
    argparser.add_argument ( '-a', '--analyses', help='analyses considered in EM baking and validation [None]',
                        type=str, default=None )
    argparser.add_argument ( '-l', '--cutlang', '--adl',
            help='use cutlang for baking', action='store_true' )
    argparser.add_argument ( '--checkmate', help='use checkmate for baking',
                             action='store_true' )
    argparser.add_argument ( '--colliderbit', help='use colliderbit for baking',
                             action='store_true' )
    argparser.add_argument ( '--cancel_all', help='cancel all bakers',
            action="store_true" )
    argparser.add_argument ( '--cancel', help='cancel a certain range of bakers, e.g "65461977-65461985"',
            type=str, default = None )
    argparser.add_argument ( '-T', '--topo', help='topology considered in EM baking and validation [None]',
                        type=str, default=None )
    args=argparser.parse_args()
    if args.cancel:
        cancelRangeOfBakers ( args.cancel )
        return
    if args.cancel_all:
        cancelAllBakers()
        return
    if args.query:
        queryStats ( 0 )
        return
    doLog = not args.dontlog
    if args.mass == "default":
        # args.mass = "[(300,1099,25),'half',(200,999,25)]"
        args.mass = "[(50,4500,200),(50,4500,200),(0.)]"
    for r in range(args.repeat):
        for i in range(args.nbakes):
            # print ( "args", vars(args) )
            bake ( vars(args) )
    if not args.query:
        logCall()

if __name__ == "__main__":
    main()
