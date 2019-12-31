#!/usr/bin/env python3

""" draw Z as a function of a model parameter """

import numpy, sys, os
from matplotlib import pyplot as plt

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


def produce():
    import hiscore
    rundir = setup()
    picklefile =rundir + "hiscore.pcl" 
    hi = hiscore.Hiscore( 0, False, picklefile = picklefile )
    pid = 1000022
    nevents = 1000
    model = hi.trimmed[0]
    mass = model.masses[pid]
    Zs = {}
    for m in numpy.arange ( .6*mass, 1.3*mass, .1*mass ):
        print ( "mass at", m )
        model.masses[pid] = m
        Z = model.predict ( nevents = nevents )
        Zs[m]=Z
    with open ( "scan.pcl", "wb" ) as f:
        pickle.dump ( Zs, f )
        pickle.close()

def draw():
    with open ( "saved.pcl", "rb" ) as f:
        Zs = pickle.load( f )
    plt.plot ( Zs.keys(), Zs.values() )
    plt.savefig ( "irst.png" )

if __name__ == "__main__":
    produce()
    draw()
