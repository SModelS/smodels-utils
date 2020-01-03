#!/usr/bin/env python3

""" draw Z as a function of a model parameter """

import numpy, sys, os, copy

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
    ## do this always
    if True: # not os.path.exists ( picklefile ):
        cmd = "cp %s %s" % ( rundir+"hiscore.pcl", picklefile )
        import subprocess
        subprocess.getoutput ( cmd )
    print ( "[scanner] retrieving hiscore object %s .... " % picklefile )
    hi = hiscore.Hiscore( walkerid=0, save_hiscores=False, 
                          picklefile = picklefile )
    print ( "[scanner] done retrieving hiscore object!" )
    return hi

def predProcess ( args ):
    """ one thread that computes predictions for masses given in mrange 
    """
    model = args["model"]
    pid = args["pid"]
    i = args["i"]
    print ( "[scanner:%d] starting thread" % ( i ) )
    model.createNewSLHAFileName ( prefix = "s%dp%d" % ( i, pid ) )
    nevents = args["nevents"]
    mrange = args["mrange"]
    ret = {}
    for m in mrange:
        model.masses[pid]=m
        print ( "[scanner:%d] start with m=%.1f" % ( i, m ) )
        model.predict ( nevents = nevents )
        ret[m]=model.Z
    return ret


def produce( hi, pid=1000022, nevents = 100000, dryrun=False,
             nproc=40, fac = 1.005 ):
    """ produce pickle files for pid, with nevents
    :param hi: hiscore list object
    :param nproc: number of processes
    :param fac: factor with which to multiply interval
    """
    model = hi.trimmed[0]
    mass = model.masses[pid]
    if mass > 9e5:
        print ( "mass %d too high. Wont produce." % mass ) 
        return
    #model.createNewSLHAFileName ( prefix = "scan%s" % pid )
    Zs = {}
    fm = .6 ## lower bound (relative) on mass
    mrange = numpy.arange ( mass * fm, mass / fm, .008*mass )
    mrangetot = [ mass ]
    m1,m2 = mass, mass
    dm = 1.003
    while m1 > fm * mass:
        m1 = mass/dm
        m2 = mass*dm
        mrangetot.append( m1 )
        mrangetot.append( m2 )
        dm = dm * fac
    mrangetot.sort()
    mranges = [ mrangetot[i::nproc] for i in range(nproc) ]
    print ( "[scanner] start scanning with m(%d)=%.1f with %d procs, %d mass points, %d events" % \
            ( pid, mass, nproc, len(mrangetot), nevents ) )
    import multiprocessing
    pool = multiprocessing.Pool ( processes = len(mranges) )
    args = [ { "model": copy.deepcopy(model), "pid": pid, "nevents": nevents, 
               "i": i, "mrange": x } for i,x in enumerate(mranges) ]
    Zs={}
    tmp = pool.map ( predProcess, args )
    for r in tmp:
        Zs.update(r)
    if dryrun:
        return
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
    # print ( "Zs", Zs )
    x = list(Zs.keys())
    x.sort()
    y = []
    for i in x:
        y.append ( Zs[i] )
    pname = helpers.toLatex ( pid, addDollars=True )
    plt.plot ( x, y )
    plt.plot ( [ cmass, cmass ], [ 0.9*min(y), 1.05*max(y) ] )
    plt.ylabel ( "Z" )
    plt.title ( "Significance Z=Z(%s)" % pname )
    plt.xlabel ( "m(%s) [GeV]" % pname )
    plt.text ( .9*min(x)+.1*(max(x)-min(x)), 1.*max(y), "%d events" % nevents )
    figname = "M%d.png" % pid 
    print ( "[scanner] creating %s" % figname )
    plt.savefig ( figname )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='script that takes care of the Z(m) plots' )
    argparser.add_argument ( '-p', '--pid',
            help='pid to consider. If zero, then consider a predefined list [1000022]',
            type=int, default=1000022 )
    argparser.add_argument ( '-n', '--nproc',
            help='number of processes [40]',
            type=int, default=40 )
    argparser.add_argument ( '-f', '--factor',
            help='multiplication factor [1.005]',
            type=float, default=1.005 )
    argparser.add_argument ( '-e', '--nevents',
            help='number of events [100000]',
            type=int, default=100000 )
    argparser.add_argument ( '-P', '--produce',
            help='produce the pickle file',
            action="store_true" )
    argparser.add_argument ( '-D', '--dry_run',
            help='dry_run, dont produce',
            action="store_true" )
    argparser.add_argument ( '-d', '--draw',
            help='produce the plot',
            action="store_true" )
    args = argparser.parse_args()
    allpids = [ 1000021, 1000006, 2000006, 1000024, 1000022 ]
    if args.produce:
        hi = getHiscore()
        if args.pid > 0:
            produce( hi, args.pid, args.nevents, args.dry_run, args.nproc, args.factor )
    if args.draw:
        if args.pid > 0:
            draw( args.pid )
        else:
            for pid in allpids:
                draw( pid )
