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

def runOneJob ( pid, jmin, jmax, cont, dbpath, lines, dry_run, keep ):
    """ prepare everything for a single job 
    :params pid: process id, integer that idenfies the process
    :param jmin: id of first walker
    :param jmax: id of last walker
    :param cont: pickle file to start with, "" means start from SM
    :param dbpath: path to database
    :param lines: lines of run_walker.sh
    :param dry_run: dont act, just tell us what you would do
    :param keep: keep temporary files, for debugging
    """
    print ( "[runOneJob:%d] run walkers [%d,%d] " % ( pid, jmin, jmax ) )
    runner = tempfile.mktemp(prefix="RUNNER",suffix=".py", dir="./" )
    with open ( runner, "wt" ) as f:
        f.write ( "#!/usr/bin/env python3\n\n" )
        f.write ( "import walkingWorker\n" )
        f.write ( "walkingWorker.main ( %d, %d, '%s', dbpath='%s' )\n" % \
                  ( jmin, jmax, cont, dbpath ) )
    os.chmod( runner, 0o755 ) # 1877 is 0o755

    tf = tempfile.mktemp(prefix="RUN_",suffix=".sh", dir="./" )
    with open(tf,"wt") as f:
        for line in lines:
            f.write ( line.replace("walkingWorker.py", runner.replace("./","") ) )
    os.chmod( tf, 0o755 )
    ram = max ( 50, 3 * ( jmax - jmin ) )
    cmd = [ "srun", "--mem", "%dG" % ram, "--time", "480", "%s" % tf ]
    print ( " ".join ( cmd ) )
    if not dry_run:
        a=subprocess.run ( cmd )
        print ( a )
    remove ( tf, keep )
    remove ( runner, keep )
            

def main():
    import argparse
    argparser = argparse.ArgumentParser(description="slurm-run a walker")
    argparser.add_argument ( '-d','--dry_run', help='dry-run, dont actually call srun',
                             action="store_true" )
    argparser.add_argument ( '-k','--keep', help='keep calling scripts',
                             action="store_true" )
    argparser.add_argument ( '-n', '--nmin', nargs='?', help='minimum worker id [0]',
                        type=int, default=0 )
    argparser.add_argument ( '-N', '--nmax', nargs='?', help='maximum worker id [10]',
                        type=int, default=10 )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?', 
            help='number of processes to split task up to, 0 means one per worker [1]',
            type=int, default=1 )
    argparser.add_argument ( '-f', '--cont', help='continue with saved states [""]',
                        type=str, default="" )
    argparser.add_argument ( '-D', '--dbpath', help='path to database ["../../smodels-database/"]',
                        type=str, default="../../smodels-database/" )
    args=argparser.parse_args()
    with open("run_walker.sh","rt") as f:
        lines=f.readlines()
    nmin, nmax, cont = args.nmin, args.nmax, args.cont
    nworkers = args.nmax - args.nmin + 1
    nprocesses = min ( args.nprocesses, nworkers )
    if nprocesses == 0:
        nprocesses = nworkers
    if nprocesses == 1:
        runOneJob ( 0, nmin, nmax, cont, args.dbpath, lines, args.dry_run,
                    args.keep )
    else:
        import multiprocessing
        nwalkers = int ( math.ceil ( nworkers / nprocesses ) )
        jobs = []
        for i in range(nprocesses):
            imin = nmin + i*(nwalkers)
            imax = imin + nwalkers
            p = multiprocessing.Process ( target = runOneJob, 
                    args = ( i, imin, imax, cont, args.dbpath, lines, args.dry_run,
                             args.keep ) )
            jobs.append ( p )
            p.start()

        for j in jobs:
            j.join()

main()
