#!/usr/bin/env python3

from __future__ import print_function
import tempfile, argparse, stat, os, math
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

def runOneJob ( pid, jmin, jmax, cont, dbpath, lines, dry_run, keep, time,
                rundir ):
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
    :param rundir: directory with all temp files, cwd of job
    """
    print ( "[runOneJob:%d] run walkers [%d,%d] " % ( pid, jmin, jmax ) )
    codedir = "/mnt/hephy/pheno/ww/git/smodels-utils/combinations/"
    #runner = tempfile.mktemp(prefix="RUNNER",suffix=".py", dir="./" )
    runner = tempfile.mktemp(prefix="%sRUNNER" % rundir ,suffix=".py", dir="./" )
    with open ( runner, "wt" ) as f:
        f.write ( "#!/usr/bin/env python3\n\n" )
        f.write ( "import os, sys\n" )
        f.write ( "sys.path.insert(0,'%s')\n" % codedir )
        f.write ( "os.chdir('%s')\n" % rundir )
        f.write ( "import walkingWorker\n" )
        f.write ( "walkingWorker.main ( %d, %d, '%s', dbpath='%s' )\n" % \
                  ( jmin, jmax, cont, dbpath ) )
    os.chmod( runner, 0o755 ) # 1877 is 0o755

    #tf = tempfile.mktemp(prefix="RUN_",suffix=".sh", dir="./" )
    tf = tempfile.mktemp(prefix="%sRUN_" % rundir,suffix=".sh", dir="./" )
    with open(tf,"wt") as f:
        for line in lines:
            f.write ( line.replace("walkingWorker.py", runner.replace("./","") ) )
    os.chmod( tf, 0o755 )
    ram = max ( 35, 2.0 * ( jmax - jmin ) )
    # cmd = [ "srun" ]
    cmd = [ "sbatch" ]
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
            
def runUpdater( dry_run, time ):
    qos = "c_short"
    if time > 48:
        qos = "c_long"
    if 8 < time <= 48:
        qos = "c_medium"
    cmd = [ "srun", "--qos", qos, "--time", "%s" % ( time*60-1 ), "--mem", "100G", "./run_hiscore_updater.sh" ]
    # cmd = [ "srun", "--mem", "100G", "--pty", "bash", "./run_hiscore_updater.sh" ]
    print ( "updater: " + " ".join ( cmd ) )
    if dry_run:
        return
    subprocess.run ( cmd )

def runRegressor( dry_run ):
    cmd = [ "srun", "--mem", "120G", "./regressor.py" ]
    print ( "regressor: " + " ".join ( cmd ) )
    if dry_run:
        return
    subprocess.run ( cmd )

def clean_dirs( rundir, clean_all = False ):
    cmd = "rm slurm*out"
    o = subprocess.getoutput ( cmd )
    cmd = "cd %s; rm -rf old*pcl .cur* RUN* walker*log" % rundir
    if clean_all:
        cmd = "cd %s; rm -rf *pcl .cur* RUN* walker*log training*gz" % rundir
    o = subprocess.getoutput ( cmd )

def main():
    import argparse
    argparser = argparse.ArgumentParser(description="slurm-run a walker")
    argparser.add_argument ( '-d','--dry_run', help='dry-run, dont actually call srun',
                             action="store_true" )
    argparser.add_argument ( '-k','--keep', help='keep calling scripts',
                             action="store_true" )
    argparser.add_argument ( '-U','--updater', help='run the updater',
                             action="store_true" )
    argparser.add_argument ( '--clean', help='clean up files from old runs',
                             action="store_true" )
    argparser.add_argument ( '--clean_all', help='clean up *all* files from old runs',
                             action="store_true" )
    argparser.add_argument ( '-R','--regressor', help='run the regressor',
                             action="store_true" )
    argparser.add_argument ( '-r','--restart', help='restart worker jobs n times [0]',
                             type=int, default=0 )
    argparser.add_argument ( '-n', '--nmin', nargs='?', help='minimum worker id [0]',
                        type=int, default=0 )
    argparser.add_argument ( '-N', '--nmax', nargs='?', help='maximum worker id. Zero means nmin + 1. [0]',
                        type=int, default=0 )
    argparser.add_argument ( '-t', '--time', nargs='?', help='time in hours [8]',
                        type=int, default=8 )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?', 
            help='number of processes to split task up to, 0 means one per worker [1]',
            type=int, default=1 )
    argparser.add_argument ( '-f', '--cont', help='continue with saved states [""]',
                        type=str, default="" )
    argparser.add_argument ( '-D', '--dbpath', help='path to database ["/mnt/hephy/pheno/ww/git/smodels-database/"]',
                        type=str, default="/mnt/hephy/pheno/ww/git/smodels-database/" )
    args=argparser.parse_args()
    rundir = "/mnt/hephy/pheno/ww/rundir/"
    if args.clean:
        clean_dirs( rundir, clean_all = False )
        return
    if args.clean_all:
        clean_dirs( rundir, clean_all = True )
        return
    if args.updater:
        runUpdater( args.dry_run, args.time )
        return
    if args.regressor:
        runRegressor ( args.dry_run )
        return
    with open("run_walker.sh","rt") as f:
        lines=f.readlines()
    nmin, nmax, cont = args.nmin, args.nmax, args.cont
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
                        args.keep, args.time, rundir )
        else:
            import multiprocessing
            ## nwalkers is the number of jobs per process
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
                                 args.keep, args.time, rundir ) )
                jobs.append ( p )
                p.start()

            for j in jobs:
                j.join()
        if args.restart < 1:
            break
        restartctr+=1
        if restartctr>args.restart:
            break

main()
