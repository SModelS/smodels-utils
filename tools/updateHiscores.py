#!/usr/bin/env python3

""" simple script that perpetually updates hiscore list
    from H<n>.pcl """

import time, types, sys, os

def setup( rundir = None ):
    # codedir = "/mnt/hephy/pheno/ww/git/"
    codedir = "/scratch-cbe/users/wolfgan.waltenberger/git/"
    sys.path.insert(0,"%ssmodels/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/protomodels/" % codedir )
    if rundir != None:
        rundir = rundir.replace ( "~", os.environ["HOME"] )
        os.chdir ( rundir )
        return rundir
    rundir = "/scratch-cbe/users/wolfgan.waltenberger/rundir/"
    # rundir = "/mnt/hephy/pheno/ww/rundir/"
    # rundir = "./"
    if os.path.exists ( "./rundir.conf" ):
        with open ( "./rundir.conf" ) as f:
            rundir = f.read().strip()
    rundir = rundir.replace ( "~", os.environ["HOME"] )
    os.chdir ( rundir )
    return rundir


def updateHiscores( rundir=None ):
    args = types.SimpleNamespace()
    args.print = True
    args.interactive = False
    args.detailed = False
    args.fetch = False
    args.check = False
    args.nmax = 1
    args.dbpath = "%s/default.pcl" % rundir
    args.outfile = "hiscore.hi"
    if rundir != None:
        args.outfile = "%s/hiscore.hi" % rundir
    args.infile = None
    args.rundir = rundir
    # args.maxloss = .01
    # args.nevents = 50000
    import hiscoreTools 
    import socket
    hostname = socket.gethostname().replace(".cbe.vbc.ac.at","")
    print ( "[updateHiscores] now update %s on %s:%s" % \
            ( args.outfile, hostname, rundir ) )
    D = hiscoreTools.main ( args )
    return D

def updateStates( rundir=None):
    args = types.SimpleNamespace()
    args.print = True
    args.rundir = rundir
    args.detailed = False
    args.interactive = False
    args.fetch = False
    args.check = False
    args.dbpath = "%s/default.pcl" % rundir
    args.nmax = 20
    args.outfile = "states.dict"
    if rundir != None:
        args.outfile = "%s/states.dict" % rundir
    args.infile = None
    # args.maxloss = .003
    # args.nevents = 50000
    import hiscoreTools
    print ( )
    print ( "[updateHiscores] now update %s" % args.outfile )
    hiscoreTools.main ( args )
    print ( "[updateHiscores] done updating %s" % args.outfile )
    print ( )

def plot( Z, K, rundir ):
    from plotting import plotHiscore
    from argparse import Namespace
    args = Namespace()
    args.upload = "latest"
    args.number = 0
    args.detailed = False
    args.destinations = False
    args.picklefile = "%s/hiscore.hi" % rundir 
    args.dbpath = "%s/default.pcl" % rundir
    args.verbosity = "info"
    args.horizontal = False
    args.html = True
    args.ruler = True
    args.decays = True
    args.predictions = True
    args.tex = False
    args.keep = False
    args.commit = False
    if K > 5.0:
        args.commit = True
    plotHiscore.runPlotting ( args )

def main( rundir = None ):
    """ eternal loop that updates hiscore.hi and states.dict """
    rundir = setup( rundir )
    i = 0
    Z, Zold, step, K, Kold = 0., 0., 0, -90., -90.
    Zfile = "%s/Zold.conf" % rundir 
    if os.path.exists ( Zfile ):
        with open ( Zfile, "rt" ) as f:
            Zold = float ( f.read().strip() )
    Kfile = "%s/Kold.conf" % rundir 
    if os.path.exists ( Kfile ):
        with open ( Kfile, "rt" ) as f:
            Kold = float ( f.read().strip() )
    while True:
        i+=1
        D = updateHiscores( rundir )
        Z,step,model,K = D["Z"],D["step"],D["model"],D["K"]
        if K > Kold + .001:
            from builder.manipulator import Manipulator
            m = Manipulator ( model )
            T=str(int(time.time()))
            m.writeDictFile ( "pmodel-%s.py" % T, comment="history keeper" )
            with open ( "%shistory.txt" % rundir, "at" ) as f:
                f.write ( "%s, step=%d, Z=%.4f, K=%.4f, t=%s\n" % ( time.asctime(),step,Z,K,T) )
                f.close()
            plot ( Z, K, rundir )
            with open ( Zfile, "wt" ) as f:
                f.write ( "%s\n" % str(Z) )
                f.close()
            with open ( Kfile, "wt" ) as f:
                f.write ( "%s\n" % str(K) )
                f.close()
            Zold = Z
            Kold = K
        updateStates( rundir )
        time.sleep(60.)
        if os.path.exists ( Kfile ): ## so we can meddle from outside
            with open ( Kfile, "rt" ) as f:
                Kold = float ( f.read().strip() )

if __name__ == "__main__":
    main()
