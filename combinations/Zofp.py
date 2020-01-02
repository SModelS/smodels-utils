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

def getHiscore():
    import hiscore
    rundir = setup()
    picklefile =rundir + "scanHiscore.pcl"
    if not os.path.exists ( picklefile ):
        cmd = "cp %s %s" % ( rundir+"hiscore.pcl", picklefile )
        import subprocess
        subprocess.getoutput ( cmd )
    print ( "retrieving hiscore object %s .... " % picklefile )
    hi = hiscore.Hiscore( walkerid=0, save_hiscores=False, 
                          picklefile = picklefile )
    print ( "done retrieving hiscore object!" )
    return hi

def produce( hi, pid=1000022, nevents = 100000, dryrun=False ):
    """ produce pickle files for pid, with nevents
    :param hi: hiscore list object
    """
    model = hi.trimmed[0]
    mass = model.masses[pid]
    model.createNewSLHAFileName ( prefix = "scan%s" % pid )
    print ( "start probing pid %d with central mass of %.1f" % ( pid, mass ) )
    Zs = {}
    fm = .6 ## lower bound (relative) on mass
    mrange = numpy.arange ( mass * fm, mass / fm, .008*mass )
    mrange = [ mass ]
    m1,m2 = mass, mass
    dm = 1.003
    while m1 > fm * mass:
        m1 = mass/dm
        m2 = mass*dm
        mrange.append( m1 )
        mrange.append( m2 )
        dm = dm * 1.005
    mrange.sort()
    for m in mrange:
        print ( "probe pid %d with mass of %.2f" % ( pid, m ), end="." )
        model.masses[pid] = m
        if not dryrun:
            model.predict ( nevents = nevents )
        print ( "Z=%.2f" % model.Z )
        Zs[m]=model.Z
    if dryrun:
        sys.exit()
    import pickle
    with open ( "scanM%s.pcl" % pid, "wb" ) as f:
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
        cmass = pickle.load ( f )
        nevents = pickle.load ( f )
    x = list(Zs.keys())
    y = list(Zs.values())
    pname = helpers.toLatex ( pid, addDollars=True )
    plt.plot ( x, y )
    plt.plot ( [ cmass, cmass ], [ 0.9*min(y), 1.05*max(y) ] )
    plt.ylabel ( "Z" )
    plt.title ( "Significance Z=Z(%s)" % pname )
    plt.xlabel ( "m(%s) [GeV]" % pname )
    plt.text ( .9*min(x)+.1*(max(x)-min(x)), 1.*max(y), "%d events" % nevents )
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
    allpids = [ 1000021, 1000006, 2000006, 1000024, 1000022 ]
    if args.produce:
        hi = getHiscore()
        if args.pid > 0:
            produce( hi, args.pid )
        else:
            import multiprocessing
            ps = []
            for pid in allpids:
                p = multiprocessing.Process(target=produce,args=(hi,pid) )
                p.start()
                ps.append ( p )
            for p in ps:
                p.join()
    if args.draw:
        if args.pid > 0:
            draw( args.pid )
        else:
            for pid in allpids:
                draw( pid )
