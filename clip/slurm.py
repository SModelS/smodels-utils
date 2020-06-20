#!/usr/bin/env python3

from __future__ import print_function
import tempfile, argparse, stat, os, math, sys
try:
    import commands as subprocess
except:
    import subprocess

def remove( fname, keep):
    ## rmeove filename if exists
    if not os.path.exists ( fname ):
        return
    if keep:
        return
    try:
        if True:
            os.unlink ( fname )
    except:
        pass

codedir = "/scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/"

def runOneJob ( pid, jmin, jmax, cont, dbpath, lines, dry_run, keep, time,
                cheatcode, rundir ):
    """ prepare everything for a single job
    :params pid: process id, integer that idenfies the process
    :param jmin: id of first walker
    :param jmax: id of last walker
    :param cont: pickle file to start with, "" means start from SM
    :param dbpath: path to database
    :param lines: lines of run_walker.sh
    :param dry_run: dont act, just tell us what you would do
    :param keep: keep temporary files, for debugging
    :param time: time in hours
    :param cheatcode: in case we wish to start with a cheat model
    :param rundir: the run directory
    """
    if not "/" in dbpath: ## then assume its meant to be in rundir
        dbpath = rundir + "/" + dbpath
    print ( "[runOneJob:%d] run walkers [%d,%d] " % ( pid, jmin, jmax ) )
    # runner = tempfile.mktemp(prefix="%sRUNNER" % rundir ,suffix=".py", dir="./" )
    runner = "%s/RUNNER_%s.py" % ( rundir, jmin )
    dump_trainingdata = False
    with open ( runner, "wt" ) as f:
        f.write ( "#!/usr/bin/env python3\n\n" )
        f.write ( "import os, sys\n" )
        f.write ( "sys.path.insert(0,'%s')\n" % codedir )
        f.write ( "sys.path.insert(0,'%s/combinations')\n" % codedir )
        f.write ( "os.chdir('%s')\n" % rundir )
        f.write ( "import walkingWorker\n" )
        f.write ( "walkingWorker.main ( %d, %d, '%s', dbpath='%s', cheatcode=%d, dump_training=%s, rundir='%s' )\n" % \
                  ( jmin, jmax, cont, dbpath, cheatcode, dump_trainingdata, rundir ) )
    os.chmod( runner, 0o755 ) # 1877 is 0o755
    # tf = tempfile.mktemp(prefix="%sRUN_" % rundir,suffix=".sh", dir="./" )
    tf = "%s/RUN_%s.sh" % ( rundir, jmin )
    with open(tf,"wt") as f:
        for line in lines:
            f.write ( line.replace("walkingWorker.py", runner.replace("./","") ) )
    os.chmod( tf, 0o755 )
    ram = max ( 25, 2.0 * ( jmax - jmin ) )
    # cmd = [ "srun" ]
    cmd = [ "sbatch" ]
    cmd += [ "--error", "/scratch-cbe/users/wolfgan.waltenberger/outputs/slurm-%j.out",
             "--output", "/scratch-cbe/users/wolfgan.waltenberger/outputs/slurm-%j.out" ]
    qos = "c_short"
    if time > 48:
        qos = "c_long"
    if 8 < time <= 48:
        qos = "c_medium"
    cmd += [ "--qos", qos ]
    # cmd += [ "-n", str(jmax - jmin) ]
    # cmd += [ "--threads-per-core", str(jmax - jmin) ]
    # cmd += [ "-N", str(jmax - jmin) ]
    # cmd += [ "-k" ]
    cmd += [ "--mem", "%dG" % ram, "--time", "%s" % ( time*60-1 ), "%s" % tf ]
    print ( " ".join ( cmd ) )
    if not dry_run:
        a=subprocess.run ( cmd )
        print ( "returned: %s" % a )
    #remove ( tf, keep )
    #remove ( runner, keep )

def produceLLHDScanScript ( pid1, pid2, force_rewrite, rundir, nprocs ):
    fname = "%s/llhdscanner%d.sh" % ( rundir, pid1 )
    if force_rewrite or not os.path.exists ( fname ):
        with open ( fname, "wt" ) as f:
            f.write ("#!/bin/sh\n\n"  )
            f.write ("%s/combinations/llhdscanner.py -R %s --draw --pid1 %d --pid2 %d --nproc %d\n" % ( codedir, rundir, pid1, pid2, nprocs ) )
            f.close()
        os.chmod ( fname, 0o775 )

def produceScanScript ( pid, force_rewrite, pid2, rundir, nprocs ):
    spid2=""
    if pid2!=-1:
        spid2=str(pid2)
    fname = "%s/scanner%d%s.sh" % ( rundir, pid, spid2 )
    if force_rewrite or not os.path.exists ( fname ):
        argpid2=""
        if pid2!=0:
            argpid2 = " --pid2 %d" % pid2
        with open ( fname, "wt" ) as f:
            f.write ("#!/bin/sh\n\n"  )
            f.write ("%s/combinations/scanner.py --nproc %d -R %s -d -c -P -p %d %s\n" % \
                     ( codedir, nprocs, rundir,pid,argpid2) )
            f.close()
        os.chmod ( fname, 0o775 )

def fetchUnfrozenFromDict():
    """ fetch pids of unfrozenparticles from dictionary
        in <rundir>/pmodel.py, if exists.
    :returns: list of pids, or None.
    """
    if not os.path.exists ( "%s/pmodel.py" % rundir ):
        print ( "[slurm.py] could not find pmodel.py file when trying to fetch unfrozen pids" )
        return None
    with open ( "%s/pmodel.py" % rundir, "rt" ) as f:
        D = eval( f.read() )
        M = D["masses"]
        ret = []
        for k,v in M.items():
            if v < 90000:
                ret.append(k)
        return ret
    return None

def fetchUnfrozenSSMsFromDict():
    """ fetch pid pairs of ssmultipliers from dictionary
        in <rundir>/pmodel.py, if exists.
    :returns: list of pid pairs, or None.
    """
    if not os.path.exists ( "%s/pmodel.py" % rundir ):
        print ( "[slurm.py] could not find pmodel.py file when trying to fetch unfrozen ssms" )
        return None
    with open ( "%s/pmodel.py" % rundir, "rt" ) as f:
        D = eval( f.read() )
        M = D["masses"]
        ssms = D["ssmultipliers"]
        pids = []
        for k,v in M.items():
            if v < 90000:
                pids.append(k)
        ret = []
        for ssmpids,ssm in ssms.items():
            for ssmpid in ssmpids:
                #if abs(ssmpid) == 1000022:
                #    continue
                if abs(ssmpid) not in pids:
                    continue
            ret.append ( ssmpids )
        return ret
    return None

def runLLHDScanner( pid, dry_run, time, rewrite, rundir ):
    """ run the llhd scanner for pid, on the current hiscore
    :param pid: pid of particle on x axis. if zero, run all unfrozen pids of hiscore
    :param dry_run: do not execute, just say what you do
    :param rewrite: force rewrite of scan script
    """
    if pid == 0:
        pids = fetchUnfrozenFromDict()
        if pids == None:
            pids = [ 1000001, 1000003, 1000006 ]
        for i in pids:
            runLLHDScanner ( i, dry_run, time, rewrite, rundir )
        return
    qos = "c_short"
    if time > 48:
        qos = "c_long"
    if 8 < time <= 48:
        qos = "c_medium"
    cmd = [ "sbatch" ]
    cmd += [ "--error", "/scratch-cbe/users/wolfgan.waltenberger/outputs/slurm-%j.out",
             "--output", "/scratch-cbe/users/wolfgan.waltenberger/outputs/slurm-%j.out" ]
    # cmd = [ "srun" ]
    cmd += [ "--qos", qos ]
    cmd += [ "--mem", "40G" ]
    cmd += [ "-c", "30" ]
    #cmd += [ "--ntasks-per-node", "5" ]
    # cmd += [ "--pty", "bash" ]
    cmd += [ "--time", "%s" % ( time*60-1 ) ]
    with  open ( "run_llhd_scanner_template.sh", "rt" ) as f:
        lines=f.readlines()
        f.close()
    script = "_L%s.sh" % pid
    with open ( script, "wt" ) as f:
        for line in lines:
            f.write ( line.replace("@@PID@@",str(pid)).replace("@@RUNDIR@@",rundir ) )
        f.close()
    nprcs = 15
    produceLLHDScanScript ( pid, 1000022, rewrite, rundir, nprcs )
    cmd += [ script ]
    print ( "[runLLHDScanner]", " ".join ( cmd ) )
    if dry_run:
        return
    a = subprocess.run ( cmd )
    print ( ">>", a )

def runScanner( pid, dry_run, time, rewrite, pid2, rundir ):
    """ run the Z scanner for pid, on the current hiscore
    :param pid: if 0, run on unfrozen particles in hiscore.
    :param dry_run: do not execute, just say what you do
    :param rewrite: force rewrite of scan script
    :param pid2: if >0, scan for ss multipliers (pid,pid2),
                 if 0, scan all ss multipliers, if < 0, scan masses,
                 not ssm multipliers.
    """
    if pid == 0:
        if pid2 == 0:
            pidpairs = fetchUnfrozenSSMsFromDict()
            for pidpair in pidpairs:
                runScanner ( pidpair[0], dry_run, time, rewrite, pidpair[1], rundir )
            return
        pids = fetchUnfrozenFromDict()
        if pids == None:
            pids = [ 1000001, 1000003, 1000006, 10000022 ]
        for i in pids:
            runScanner ( i, dry_run, time, rewrite, pid2, rundir )
        return
    qos = "c_short"
    if time > 48:
        qos = "c_long"
    if 8 < time <= 48:
        qos = "c_medium"
    cmd = [ "sbatch" ]
    cmd += [ "--error", "/scratch-cbe/users/wolfgan.waltenberger/outputs/slurm-%j.out",
             "--output", "/scratch-cbe/users/wolfgan.waltenberger/outputs/slurm-%j.out" ]
    # cmd = [ "srun" ]
    cmd += [ "--qos", qos ]
    cmd += [ "--mem", "40G" ]
    cmd += [ "-c", "30" ]
    # cmd += [ "--ntasks-per-node", "5" ]
    # cmd += [ "--pty", "bash" ]
    cmd += [ "--time", "%s" % ( time*60-1 ) ]
    with  open ( "run_scanner_template.sh", "rt" ) as f:
        lines=f.readlines()
        f.close()
    spid2 = ""
    if pid2 != -1:
        spid2 = "%d" % pid2
    script = "_S%s%s.sh" % ( pid, spid2 )
    with open ( script, "wt" ) as f:
        for line in lines:
            f.write ( line.replace("@@PID@@",str(pid)).replace("xxPID2xx",spid2).replace("@@RUNDIR@@",rundir)  )
        f.close()
    os.chmod( script, 0o755 ) # 1877 is 0o755
    cmd += [ script ]
    nprc = 15
    produceScanScript ( pid, rewrite, pid2, rundir, nprc )
    print ( "[runScanner]", " ".join ( cmd ) )
    if dry_run:
        return
    a = subprocess.run ( cmd )
    print ( "[runScanner] >>", a )

def runUpdaterOld( dry_run, time, rundir ):
    """ thats the hiscore updater
    :param time: time, given in minutes(?)
    """
    # cmd = [ "srun", "--qos", qos, "--mem", "100G", "./run_hiscore_updater.sh" ]
    cmd = [ "srun", "--mem", "40G" ]
    cmd += [ "--reservation", "interactive" ]
    # cmd = [ "srun", "--mem", "50G" ]
    cmd += [ "--time", "%s" % ( time*60-1 ) ]
    qos = "c_short"
    if time > 48:
        qos = "c_long"
        cmd += [ "--qos", qos ]
    if 8 < time <= 48:
        qos = "c_medium"
        cmd += [ "--qos", qos ]
    cmd += [ "--pty", "bash", "./run_hiscore_updater.sh" ]
    print ( "updater: " + " ".join ( cmd ) )
    if dry_run:
        return
    subprocess.run ( cmd )

def runUpdater( dry_run, time, rundir ):
    """ thats the hiscore updater
    :param time: time, given in minutes(?)
    """
    with open ( "%sclip/hiscore_update_template.sh" % codedir, "rt" ) as f:
        lines = f.readlines()
        f.close()
    tf = "%s/HISCORE_UPDATER.sh" % ( rundir )
    with open(tf,"wt") as f:
        for line in lines:
            f.write ( line.replace("@@RUNDIR@@", rundir ) )
    os.chmod( tf, 0o755 )
    runner = "%s/upHi.py" % ( rundir )
    with open ( runner, "wt" ) as f:
        f.write ( "#!/usr/bin/env python3\n\n" )
        f.write ( "import os, sys\n" )
        f.write ( "sys.path.insert(0,'%s')\n" % codedir )
        f.write ( "sys.path.insert(0,'%s/combinations')\n" % codedir )
        f.write ( "os.chdir('%s')\n" % rundir )
        f.write ( "import updateHiscores\n" )
        f.write ( "updateHiscores.main ( rundir='%s' )\n" % \
                  ( rundir ) )
    os.chmod( runner, 0o755 ) # 1877 is 0o755
    cmd = [ "srun", "--mem", "40G" ]
    cmd += [ "--reservation", "interactive" ]
    # cmd = [ "srun", "--mem", "50G" ]
    cmd += [ "--time", "%s" % ( time*60-1 ) ]
    qos = "c_short"
    if time > 48:
        qos = "c_long"
        cmd += [ "--qos", qos ]
    if 8 < time <= 48:
        qos = "c_medium"
        cmd += [ "--qos", qos ]
    cmd += [ "--pty", "bash", tf ]
    print ( "updater: " + " ".join ( cmd ) )
    if dry_run:
        return
    subprocess.run ( cmd )

def bake ( recipe, analyses, mass, topo, dry_run, nproc, rundir ):
    """ bake with the given recipe
    :param recipe: eg '@n 10000 @a', will turn into '-n 10000 -a'
    :param analyses: eg "cms_sus_16_033,atlas_susy_2016_07"
    :param topo: eg T3GQ
    :param mass: eg [(50,4500,200),(50,4500,200),(0.)]
    :param dry_run: dont do anything, just produce script
    :param nproc: number of processes, typically 5
    """
    with open ( "%sclip/bake_template.sh" % codedir, "rt" ) as f:
        lines = f.readlines()
        f.close()

    filename = "bake.sh"
    filename = tempfile.mktemp(prefix="_B",suffix=".sh",dir="")
    Dir = "%sclip/" % codedir
    print ( "creating script at %s/%s" % ( Dir, filename ) )
    nprc = int ( math.ceil ( nproc * .5  ) )
    with open ( "%s/%s" % ( Dir, filename ), "wt" ) as f:
        for line in lines:
            args = recipe.replace("@","-")
            args += ' -m "%s"' % mass
            args += ' --analyses "%s"' % analyses
            args += ' -t %s' % topo
            args += ' -p %d' % nprc
            f.write ( line.replace("@@ARGS@@", args ) )
        f.close()
    with open ( "run_bakery_template.sh", "rt" ) as f:
        lines = f.readlines()
        f.close()
    tmpfile = tempfile.mktemp(prefix="B", suffix=".sh",dir="./" )
    with open ( tmpfile, "wt" ) as f:
        for line in lines:
            f.write ( line.replace ( "@@SCRIPT@@", filename ) )
        f.close()
    os.chmod( tmpfile, 0o755 ) # 1877 is 0o755
    os.chmod( Dir+filename, 0o755 ) # 1877 is 0o755
    cmd = [ "sbatch" ]
    cmd += [ "--error", "/scratch-cbe/users/wolfgan.waltenberger/outputs/slurm-%j.out",
             "--output", "/scratch-cbe/users/wolfgan.waltenberger/outputs/slurm-%j.out" ]
    cmd += [ "--ntasks-per-node", str(nproc) ]
    cmd += [ tmpfile ]
    ram = 2
    cmd += [ "--mem", "%dG" % ram ]
    # cmd += [ "./run_bakery.sh" ]
    print ("[slurm.py] baking %s" % " ".join ( cmd ) )
    if not dry_run:
        a=subprocess.run ( cmd )
        print ( "returned: %s" % a )
    #cmd = "rm %s" % tmpfile
    #o = subprocess.getoutput ( cmd )
    #print ( "[slurm.py] %s %s" % ( cmd, o ) )

def clean_dirs( rundir, clean_all = False ):
    cmd = "rm slurm*out"
    o = subprocess.getoutput ( cmd )
    cmd = "cd %s; rm -rf old*pcl .*slha H*pcl states.dict hiscore.pcl Kold.conf Zold.conf RUN* *log ../outputs/slurm-*.out" % rundir
    if clean_all:
        cmd = "cd %s; rm -rf old*pcl H*pcl hiscore*pcl .cur* .old* .tri* .*slha M*png llhd*png decays* *.sh ruler* rawnumb* *tex hiscore.log hiscore.slha *html *png *log RUN* walker*log training*gz Kold.conf Zold.conf ../outputs/slurm-*.out" % rundir
    o = subprocess.getoutput ( cmd )

def queryStats ( ):
    import running_stats
    running_stats.count_jobs()
    running_stats.running_stats()

def logCall ():
    f=open("slurm.log","at")
    args = ""
    for i in sys.argv:
        if " " in i or "," in i:
            i = '"%s"' % i
        args += i + " "
    f.write ("[slurm.py] %s\n" % args.strip() )
    # f.write ("[slurm.py] %s\n" % " ".join ( sys.argv ) )
    f.close()


def main():
    import argparse
    argparser = argparse.ArgumentParser(description="slurm-run a walker")
    argparser.add_argument ( '-q','--query', help='query status, dont actually run',
                             action="store_true" )
    argparser.add_argument ( '-d','--dry_run', help='dry-run, dont actually call srun',
                             action="store_true" )
    argparser.add_argument ( '-k','--keep', help='keep the shell scripts that are being run, do not remove them afters',
                             action="store_true" )
    argparser.add_argument ( '-U','--updater', help='run the hiscore updater',
                             action="store_true" )
    argparser.add_argument ( '-S', '--scan', nargs="?",
                    help='run the Z scanner on pid [SCAN], -1 means dont run, 0 means run on all unfrozen particles in hiscore.',
                    type=int, default=-1 )
    argparser.add_argument ( '-B', '--nbakes', nargs="?",
                    help='launch n identical jobs',
                    type=int, default=1 )
    argparser.add_argument ( '-b', '--bake', nargs="?",
                    help='bake EM maps, with the given arguments, use "default" if unsure ["@n 10000 @a"]',
                    type=str, default="" )
    argparser.add_argument ( '-m', '--mass', nargs="?",
                    help='bake EM maps, mass specification, for baking only [(50,4500,200),(50,4500,200),(0.)]',
                    type=str, default="default" )
    argparser.add_argument ( '--pid2', nargs="?",
                    help='run the scanner for ss multipliers (pid,pid2), -1 means ignore and run for mass scans instead. 0 means scan over all unfrozen ssms of hiscore.',
                    type=int, default=-1 )
    argparser.add_argument ( '-L', '--llhdscan', nargs="?",
                    help='run the llhd scanner on pid/1000022, -1 means dont run. 0 means run on all unfrozen pids of hiscore.',
                    type=int, default=-1 )
    argparser.add_argument ( '--clean', help='clean up files from old runs',
                             action="store_true" )
    argparser.add_argument ( '--clean_all', help='clean up *all* files from old runs',
                             action="store_true" )
    #argparser.add_argument ( '-R','--regressor', help='run the regressor',
    #                         action="store_true" )
    argparser.add_argument ( '--allscans', help='run all the scans: masses, llhds, and ssmses',
                             action="store_true" )
    #argparser.add_argument ( '-r','--restart', help='restart worker jobs n times [0]',
    #                         type=int, default=0 )
    argparser.add_argument ( '--rewrite', help='force rewrite of scan scripts',
                             action="store_true" )
    argparser.add_argument ( '-n', '--nmin', nargs='?', help='minimum worker id [0]',
                        type=int, default=0 )
    argparser.add_argument ( '-C', '--cheatcode', nargs='?', help='use a cheat code [0]',
                        type=int, default=0 )
    argparser.add_argument ( '-N', '--nmax', nargs='?', help='maximum worker id. Zero means nmin + 1. [0]',
                        type=int, default=0 )
    argparser.add_argument ( '-t', '--time', nargs='?', help='time in hours [48]',
                        type=int, default=48 )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?',
            help='number of processes to split task up to, 0 means one per worker [0]',
            type=int, default=0 )
    argparser.add_argument ( '-f', '--cont', help='continue with saved states [""]',
                        type=str, default="" )
    argparser.add_argument ( '-a', '--analyses', help='analyses considered in EM baking ["cms_sus_16_033,atlas_susy_2016_07"]',
                        type=str, default="cms_sus_16_033,atlas_susy_2016_07" )
    argparser.add_argument ( '-R', '--rundir', 
                        help='override the default rundir [None]',
                        type=str, default=None )
    argparser.add_argument ( '-T', '--topo', help='topology considered in EM baking ["T3GQ"]',
                        type=str, default="T3GQ" )
    argparser.add_argument ( '-D', '--dbpath', help='path to database, or "fake1" or "real" or "default" ["none"]',
                        type=str, default="default" )
    args=argparser.parse_args()
    args.rewrite = True
    if args.nmax > 0 and args.dbpath == "none":
        print ( "dbpath not specified. not starting. note, you can use 'real' or 'fake1' as dbpath" )
        return
    rundir = "/scratch-cbe/users/wolfgan.waltenberger/rundir/"
    if args.rundir != None:
        rundir = args.rundir
        if not "/" in rundir:
            rundir = "/scratch-cbe/users/wolfgan.waltenberger/" + rundir + "/"
    if args.dbpath == "real":
        args.dbpath = "/scratch-cbe/users/wolfgan.waltenberger/git/smodels-database"
    if args.dbpath == "default":
        args.dbpath = rundir + "/default.pcl"
    if "fake" in args.dbpath and not args.dbpath.endswith(".pcl"):
        args.dbpath = args.dbpath + ".pcl"
    logCall ()

    if args.allscans:
        subprocess.getoutput ( "./slurm.py -S 0" )
        subprocess.getoutput ( "./slurm.py -S 0 --pid2 0" )
        subprocess.getoutput ( "./slurm.py -L 0" )
        return
    if args.query:
        queryStats ( )
        return
    if args.bake != "":
        if args.bake == "default":
            args.bake = '@n 10000 @a'
        if args.mass == "default":
            # args.mass = "[(300,1099,25),'half',(200,999,25)]"
            args.mass = "[(50,4500,200),(50,4500,200),(0.)]"
        for i in range(args.nbakes):
            bake ( args.bake, args.analyses, args.mass, args.topo, args.dry_run,
                   args.nprocesses, rundir )
    if args.clean:
        clean_dirs( rundir, clean_all = False )
        return
    if args.clean_all:
        clean_dirs( rundir, clean_all = True )
        return
    if args.updater:
        runUpdater( args.dry_run, args.time, rundir )
        return
    if args.scan != -1:
        rewrite = True # args.rewrite
        runScanner ( args.scan, args.dry_run, args.time, rewrite, args.pid2, rundir )
        return
    if args.llhdscan != -1:
        runLLHDScanner ( args.llhdscan, args.dry_run, args.time, args.rewrite, rundir )
        return

    with open("run_walker.sh","rt") as f:
        lines=f.readlines()
    nmin, nmax, cont = args.nmin, args.nmax, args.cont
    cheatcode = args.cheatcode
    if nmax == 0:
        nmax = nmin + 1
    nworkers = args.nmax - args.nmin # + 1
    nprocesses = min ( args.nprocesses, nworkers )
    if nprocesses == 0:
        nprocesses = nworkers

    restartctr = 0
    while True:
        if nprocesses == 1:
            runOneJob ( 0, nmin, nmax, cont, args.dbpath, lines, args.dry_run,
                        args.keep, args.time, cheatcode, rundir )
        else:
            import multiprocessing
            ## nwalkers is the number of jobs per process
            nwalkers = 0
            if nprocesses > 0:
                nwalkers = int ( math.ceil ( nworkers / nprocesses ) )
            jobs = []
            #print ( "nworkers", nworkers )
            #print ( "nproceses", nprocesses )
            for i in range(nprocesses):
                imin = nmin + i*nwalkers
                imax = imin + nwalkers
                #print ( "process", imin, imax )
                p = multiprocessing.Process ( target = runOneJob,
                        args = ( i, imin, imax, cont, args.dbpath, lines, args.dry_run,
                                 args.keep, args.time, cheatcode, rundir ) )
                jobs.append ( p )
                p.start()

            for j in jobs:
                j.join()
        break
        #if args.restart < 1:
        #    break
        #restartctr+=1
        #if restartctr>args.restart:
        #    break

main()
