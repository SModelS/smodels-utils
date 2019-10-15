#!/usr/bin/env python3

from __future__ import print_function
import tempfile, argparse, stat, os
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

def runOneJob ( nmin, nmax, cont, dbpath, lines, dry_run ):
    """ prepare everything for a single job """
    runner = tempfile.mktemp(prefix="RUNNER",suffix=".py", dir="./" )
    with open ( runner, "wt" ) as f:
        f.write ( "#!/usr/bin/env python3\n\n" )
        f.write ( "import walkingWorker\n" )
        f.write ( "walkingWorker.main ( %d, %d, '%s', dbpath='%s' )\n" % \
                  ( nmin, nmax, cont, dbpath ) )
    os.chmod( runner, 0o755 ) # 1877 is 0o755

    tf = tempfile.mktemp(prefix="RUN_",suffix=".sh", dir="./" )
    with open(tf,"wt") as f:
        for line in lines:
            f.write ( line.replace("walkingWorker.py", runner.replace("./","") ) )
    os.chmod( tf, 0o755 )
    ram = max ( 50, 3 * ( nmax - nmin ) )
    cmd = [ "srun", "--mem", "%dG" % ram, "--time", "480", "%s" % tf ]
    print ( " ".join ( cmd ) )
    if not dry_run:
        a=subprocess.run ( cmd )
        print ( a )
            

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
    runOneJob ( nmin, nmax, cont, args.dbpath, lines, args.dry_run )
    remove ( tf, args.keep )
    remove ( runner, args.keep )

main()
