#!/usr/bin/env python3

""" simple script that perpetually updates hiscore list
    from H<n>.pcl, and trims leading model """

import time, types, sys, os

def setup():
    # codedir = "/mnt/hephy/pheno/ww/git/"
    codedir = "/scratch-cbe/users/wolfgan.waltenberger/git/"
    sys.path.insert(0,"%ssmodels/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/combinations/" % codedir )
    # rundir = "/mnt/hephy/pheno/ww/rundir/"
    rundir = "/scratch-cbe/users/wolfgan.waltenberger/rundir/"
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
    args.maxloss = .01
    args.nevents = 50000
    import hiscore
    import socket
    hostname = socket.gethostname().replace(".cbe.vbc.ac.at","")
    print ( "[updateHiscores] now update the hiscore.pcl file on %s" % hostname )
    D = hiscore.main ( args )
    return D
    #step,model = hiscore.main ( args )
    # return Z,step,model

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
    args.maxloss = .003
    args.nevents = 50000
    import hiscore
    print ( "[updateHiscores] now update the states.pcl file" )
    hiscore.main ( args )

def plot( Z, rundir ):
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
    args.notex = True
    args.keep = False
    args.commit = False
    if Z > 2.8:
        args.commit = True
    plotHiscore.runPlotting ( args )

def main():
    """ eternal loop that updates hiscore.pcl and states.pcl """
    rundir = setup()
    i = 0
    Z, Zold, step = 0., 0., 0
    Zfile = "%s/Zold.conf" % rundir 
    if os.path.exists ( Zfile ):
        with open ( Zfile, "rt" ) as f:
            Zold = float ( f.read().strip() )
    while True:
        i+=1
        # Z,step,model = updateHiscores( )
        D = updateHiscores( )
        Z,Zuntrimmed,step,model = D["Z"],D["Zuntrimmed"],D["step"],D["model"]
        if Z > Zold*1.0001:
            from manipulator import Manipulator
            with open ( Zfile, "wt" ) as f:
                f.write ( "%s\n" % str(Z) )
                f.close()
            m = Manipulator ( model )
            T=str(int(time.time()))
            m.writeDictFile ( "pmodel-%s.py" % T, comment="history keeper" )
            with open ( "%szhistory.txt" % rundir, "at" ) as f:
                f.write ( "%s,%d,%s,%s,%s\n" % ( time.asctime(),step,Z,Zuntrimmed,T) )
                f.close()
            plot ( Z, rundir )
            Zold = Z
        updateStates()
        time.sleep(60.)

if __name__ == "__main__":
    main()
