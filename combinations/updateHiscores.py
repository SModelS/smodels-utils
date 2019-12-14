#!/usr/bin/env python3

""" simple script that perpetually updates hiscore list
    from H<n>.pcl, and trims leading model """

import time, types, sys, os

def setup():
    codedir = "/mnt/hephy/pheno/ww/git/"
    sys.path.insert(0,"%ssmodels/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/combinations/" % codedir )
    rundir = "/mnt/hephy/pheno/ww/rundir/"
    # rundir = "./"
    if os.path.exists ( "./rundir.conf" ):
        with open ( "./rundir.conf" ) as f:
            rundir = f.read().strip()
    rundir = rundir.replace ( "~", os.environ["HOME"] )
    os.chdir ( rundir )
    return rundir

def updateHiscores():
    args = types.SimpleNamespace()
    args.print = True
    args.interactive = False
    args.detailed = False
    args.trim_branchings = True
    args.trim = True
    args.fetch = False
    args.analysis_contributions = True
    args.check = False
    args.nmax = 1
    args.outfile = "hiscore.pcl"
    args.infile = None
    args.maxloss = .02
    import hiscore
    print ( "[updateHiscores] now update the hiscore.pcl file" )
    Z = hiscore.main ( args )

def updateStates():
    args = types.SimpleNamespace()
    args.print = True
    args.detailed = False
    args.interactive = False
    args.trim_branchings = False
    args.trim = False
    args.fetch = False
    args.analysis_contributions = False
    args.check = False
    args.nmax = 20
    args.outfile = "states.pcl"
    args.infile = None
    args.maxloss = .005
    import hiscore
    print ( "[updateHiscores] now update the states.pcl file" )
    hiscore.main ( args )

def main():
    rundir = setup()
    i = 0
    Z, Zold = 0., 0.
    Zoldfile = "%s/Zold.conf" % rundir 
    if os.path.exists ( Zoldfile ):
        with open ( Zoldfile, "rt" ) as f:
            Zold = float ( f.read() )
    while True:
        i+=1
        Zold = Z
        Z = updateHiscores()
        updateStates()
        if i % 10 == 0 and Z > Zold*1.0001:
            with open ( Zoldfile, "wt" ) as f:
                f.write ( "%s" % Z )
                f.close()
            import plotHiscore
            from argparse import Namespace
            args = Namespace()
            args.upload = "latest"
            args.number = 0
            args.detailed = False
            args.destinations = False
            args.picklefile = "%shiscore.pcl" % rundir 
            args.verbosity = "info"
            args.nohtml = False
            args.noruler = False
            args.nodecays = False
            args.nopredictions = False
            args.keep = False
            args.commit = False
            plotHiscore.runPlotting ( args )
        time.sleep(1200.)

main()
