#!/usr/bin/env python3

""" draw Z as a function of a model parameter """

import numpy, sys, os

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


def produce( pid=1000022, nevents = 100000 ):
    import hiscore
    rundir = setup()
    picklefile =rundir + "hiscore.pcl" 
    hi = hiscore.Hiscore( 0, False, picklefile = picklefile )
    model = hi.trimmed[0]
    mass = model.masses[pid]
    Zs = {}
    for m in numpy.arange ( .6*mass, 1.3*mass, .02*mass ):
        print ( "mass at", m )
        model.masses[pid] = m
        model.predict ( nevents = nevents )
        Zs[m]=model.Z
    import pickle
    with open ( "scan.pcl", "wb" ) as f:
        pickle.dump ( Zs, f )
        pickle.dump ( mass, f )
        pickle.dump ( nevents, f )
        f.close()

def draw( pid= 1000022 ):
    from matplotlib import pyplot as plt
    import helpers
    import pickle
    with open ( "scanM%s.pcl" % pid, "rb" ) as f:
        Zs = pickle.load( f )
    x = list(Zs.keys())
    y = list(Zs.values())
    pname = helpers.toLatex ( pid, addDollars=True )
    plt.plot ( x, y )
    plt.ylabel ( "Z" )
    plt.title ( "Significance Z=Z(%s)" % pname )
    plt.xlabel ( "m(%s) [GeV]" % pname )
    plt.savefig ( "M%d.png" % pid )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='script that takes care of the Z(m) plots' )
    argparser.add_argument ( '-p', '--pid',
            help='pid to consider. If zero, then consider a predefined list [1000022]',
            type=int, default=1000022 )
    argparser.add_argument ( '-P', '--produce',
            help='produce the pickle file',
            action="store_true" )
    argparser.add_argument ( '-d', '--draw',
            help='produce the plot',
            action="store_true" )
    args = argparser.parse_args()
    pids = args.pid
    if args.produce:
        if pids > 0:
            produce( pids )
        else:
            pids = [ 1000022, 1000021, 1000006, 2000006, 1000024 ]
            for pid in pids:
                produce ( pid )
    if args.draw:
        draw( args.pid )
