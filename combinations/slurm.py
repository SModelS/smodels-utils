#!/usr/bin/env python

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
    argparser.add_argument ( '-f', '--cont', help='continue with saved states [""]',
                        type=str, default="" )
    argparser.add_argument ( '-D', '--dbpath', help='path to database ["../../smodels-database/"]',
                        type=str, default="../../smodels-database/" )
    args=argparser.parse_args()
    with open("run_walker.sh","rt") as f:
        lines=f.readlines()
    runner = tempfile.mktemp(prefix="RUNNER",suffix=".py", dir="./" )
    nmin, nmax, cont = args.nmin, args.nmax, args.cont
    with open ( runner, "wt" ) as f:
        f.write ( "#!/usr/bin/env python3\n\n" )
        f.write ( "import walkingWorker\n" )
        f.write ( "walkingWorker.main ( %d, %d, '%s', dbpath='%s' )\n" % \
                  ( nmin, nmax, cont, args.dbpath ) )
    os.chmod( runner, 0o755 ) # 1877 is 0o755

    tf = tempfile.mktemp(prefix="RUN_",suffix=".sh", dir="./" )
    with open(tf,"wt") as f:
        for line in lines:
            f.write ( line.replace("walkingWorker.py", runner.replace("./","") ) )
    os.chmod( tf, 0o755 )
    ram = max ( 50, 3 * ( nmax - nmin ) )
    cmd = "srun --mem %dG --time 480 %s" % ( ram, tf )
    print ( cmd )
    if False: # not args.dry_run:
        a=subprocess.getoutput ( cmd )
        print ( a )
    remove ( tf, args.keep )
    remove ( runner, args.keep )

main()
