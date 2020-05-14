#!/usr/bin/env python3

""" draw Z as a function of a model parameter """

import numpy, sys, os, copy, time, subprocess, glob
from csetup import setup
from manipulator import Manipulator
from helpers import rthresholds

def getHiscore( force_copy = False ):
    """ get the hiscore from the picklefile
    :param force_copy: if True, force a cp command on the pickle file
    """
    import hiscore
    rundir = setup()
    # spids = str(pids).replace("[","").replace("]","").replace(" ","").replace(",","").replace("0","")
    picklefile =rundir + "hiscore2.pcl" # % spids
    backupfile = rundir+"hiscore.pcl"
    # picklefile =rundir + "hiscore.pcl" # % spids
    ## do this always
    h2Outdated = False
    if os.path.exists ( picklefile ) and os.path.exists ( backupfile ):
        if os.stat ( picklefile ).st_mtime < os.stat ( backupfile ).st_mtime:
            h2Outdated = True
    if force_copy or (not os.path.exists ( picklefile )) or h2Outdated:
        cmd = "cp %s %s" % ( backupfile, picklefile )
        import subprocess
        o = subprocess.getoutput ( cmd )
        print ( "[scanner] %s: %s" % ( cmd, o ) )
    elif os.stat ( picklefile ).st_size + 1025 < os.stat ( backupfile ).st_size:
        cmd = "cp %s %s" % ( backupfile, picklefile )
        import subprocess
        o = subprocess.getoutput ( cmd )
        print ( "[scanner] %s: %s" % ( cmd, o ) )
    import socket
    hostname = socket.gethostname().replace(".cbe.vbc.ac.at","")
    print ( "[scanner] retrieving hiscore object %s on %s .... " % \
             ( picklefile, hostname ) )
    hi = hiscore.Hiscore( walkerid=0, save_hiscores=False,
                          picklefile = picklefile )
    Z=hi.hiscores[0].Z
    K=hi.hiscores[0].K
    print ( "[scanner] done retrieving hiscore object, highest at K=%.2f, Z=%.2f" % \
             (K, Z ) )
    return hi

def predProcess ( args ):
    """ one thread that computes predictions for masses given in mrange
    """
    i = args["i"]
    import time
    # time.sleep(5*i) ## would that help??
    print ( "[scanner:%d] starting thread" % ( i ) )
    model = args["model"]
    model.walkerid = 100000+10000*i + model.walkerid
    pid = args["pid"]
    nevents = args["nevents"]
    mrange = args["mrange"]
    ret = {}
    for ctr,m in enumerate(mrange):
        model.createNewSLHAFileName ( prefix = "s%dp%d%.2f" % ( i, pid, m ) )
        model.masses[pid]=m
        ts = time.strftime("%H:%M:%S" )
        print ( "[scanner:%d-%s] start with %d/%d, m=%.1f (%d events)" % \
                ( i, ts, ctr, len(mrange), m, nevents ) )
        model.predict ( nevents = nevents )
        ret[m]=(model.Z,model.rmax)
    return ret

def printCombo ( combo, comment="" ):
    """ pretty print a theory pred combo """
    print ( "combination %s" % comment )
    for tp in combo:
        print( " `- %s" % tp.analysisId() )

def printXSecs ( xsecs, comment="" ):
    """ pretty print the list of xsecs """
    print ( "xsecs %s" % comment )
    for xsec in xsecs:
        print ( " `- %s, %s [%.30s]" % ( xsec.info, xsec.value, xsec.pid ) )

def printModel ( model, comment="" ):
    print ( "model %s" % comment )
    txt=""
    for pid,m in model.masses.items():
        if m>5e5:
            continue
        txt+="%d:%d, " % ( pid, m )
    print ( " `- m %s" % txt[:-2] )
    txt=""
    for pids,ssm in model.ssmultipliers.items():
        if abs(ssm-1)<1e-2:
            continue
        txt+="%s:%.2f, " % ( pids, ssm )
    print ( " `- ssm %s" % txt[:-2] )


def ssmProcess ( args ):
    """ one thread that computes predictions for ssms given in ssmrange
    """
    i = args["i"]
    import time
    # time.sleep(5*i) ## would that help??
    print ( "[scanner:%d] starting thread" % ( i ) )
    model = args["model"]
    pids = args["pids"]
    nevents = args["nevents"]
    ssmrange = args["ssmrange"]
    ssm = args["ssm"]
    model.walkerid = 200000+10000*i + model.walkerid
    model.createNewSLHAFileName ( prefix = "ssm%dp%d%d%.2f" % ( i, pids[0], pids[1], ssm ) )
    if not pids in model.ssmultipliers:
        print ( "[scanner:%d] error cannot find pids %s" % (i, str(pids) ) )
        return
    ret = {}
    ts = time.strftime("%H:%M:%S" )
    model.delXSecs()
    model.predict ( nevents = nevents, recycle_xsecs = True )
    print ( "[scanner:%d-%s] before we begin, Z is %.3f" % ( i, ts, model.Z ) )

    for ctr,ssm in enumerate(ssmrange):
        ssmold = model.ssmultipliers[pids]
        print ( "[scanner:%d] we change the ssm from %.3f to %.3f" % \
                ( i, ssmold, ssm ) )
        ma = Manipulator ( model )
        ma.changeSSM ( pids, ssm )
        model = ma.M
        ts = time.strftime("%H:%M:%S" )
        print ( "[scanner:%d-%s] start with %d/%d, ssm=%.2f (%d events)" % \
                ( i, ts, ctr, len(ssmrange), ssm, nevents ) )
        model.predict ( nevents = nevents, recycle_xsecs = True )
        print ( "[scanner:%d-%s]   `- Z=%.3f" % ( i, ts, model.Z ) )
        ret[ssm]=(model.Z,model.rmax)
    return ret

def produce( hi, pid=1000022, nevents = 100000, dryrun=False,
             nproc=5, fac = 1.005 ):
    """ produce pickle files for pid, with nevents
    :param hi: hiscore list object
    :param nproc: number of processes
    :param fac: factor with which to multiply interval
    """
    if type(pid) in [ list, tuple ]:
        for p in pid:
            produce ( hi, p, nevents, dryrun, nproc, fac )
        return
    model = hi.hiscores[0]
    if model == None:
        print ( "[scanner] cannot find a model in %s" % hi.pickleFile )
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
    dm = fac
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
    args = [ { "model": model, "pid": pid, "nevents": nevents,
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
        pickle.dump ( time.asctime(), f )
        f.close()

def produceSSMs( hi, pid1, pid2, nevents = 100000, dryrun=False,
             nproc=5, fac = 1.005 ):
    """ produce pickle files for ssm scan, for (pid1,pid2), with nevents
    :param hi: hiscore list object
    :param nproc: number of processes
    :param fac: factor with which to multiply interval
    """
    model = hi.hiscores[0]
    pids = ( pid1, pid2 )
    if pid2 < pid1:
        pids = ( pid2, pid1 )
    if not pids in model.ssmultipliers:
        print ( "[scanner] could not find pids %s in multipliers" % ( str(pids) ) )
        print ( "only", model.ssmultipliers )
        return
    ssm = model.ssmultipliers[pids]
    # print ( "[scanner] starting with %s: %.2f" % ( pids, ssm ) )
    Zs = {}
    fm = .6 ## lower bound (relative) on mass
    mrange = numpy.arange ( ssm * fm, ssm / fm, .01*ssm )
    ssmrangetot = [ ssm ]
    ssm1,ssm2 = ssm, ssm
    dssm = fac
    while ssm1 > fm * ssm:
        ssm1 = ssm/dssm
        ssm2 = ssm*dssm
        ssmrangetot.append( ssm1 )
        ssmrangetot.append( ssm2 )
        dssm = dssm * fac
    ssmrangetot.sort()
    if nproc > len(ssmrangetot):
        nproc = len(ssmrangetot)
    ssmranges = [ ssmrangetot[i::nproc] for i in range(nproc) ]
    print ( "[scanner] start scanning with ssm(%d,%d)=%.2f with %d procs, %d ssm points, %d events" % \
            ( pid1, pid2, ssm, nproc, len(ssmrangetot), nevents ) )
    import multiprocessing
    pool = multiprocessing.Pool ( processes = len(ssmranges) )
    args = [ { "model": model, "pids": pids, "nevents": nevents, "ssm": ssm,
               "i": i, "ssmrange": x } for i,x in enumerate(ssmranges) ]
    Zs={}
    tmp = pool.map ( ssmProcess, args )
    for r in tmp:
        Zs.update(r)
    if dryrun:
        return
    import pickle
    filename = "ssm%d%d.pcl" % (pids[0],pids[1])
    if os.path.exists ( filename ):
        subprocess.getoutput ( "cp %s %sold" % ( filename, filename ) )
    with open ( filename, "wb" ) as f:
        pickle.dump ( Zs, f )
        pickle.dump ( ssm, f )
        pickle.dump ( nevents, f )
        pickle.dump ( time.asctime(), f )
        f.close()

def findPidPairs ():
    """ search for ssm*pcl files, report the corresponding pid pairs.
    :returns: list of tuple of pids
    """
    ret = []
    files = glob.glob("ssm*pcl")
    for f in files:
        p = f.find("ssm")
        s = f[p+3:]
        s = s.replace(".pcl","")
        split = 7
        if s[0]=="-":
            split = 8
        pids = ( ( int(s[:split]), int(s[split:]) ) )
        ret.append ( pids )
    return ret

def draw( pid= 1000022, interactive=False, pid2=0, copy=False ):
    """ draw plots
    :param copy: copy final plots to ../../smodels.github.io/protomodels/latest
    """
    if pid2 == 0: ## means all
        pidpairs = findPidPairs()
        for pids in pidpairs:
            try:
                draw ( pids[0], interactive, pids[1], copy )
            except Exception as e:
                print ( "[scanner] %s" % e )
        return

    def isSSMPlot():
        ## is this an ssm or a mass plot
        return pid2!=-1
        
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    import helpers
    import pickle
    rundir = setup()
    if False:
        rundir = ""
    picklefile = "%sscanM%s.pcl" % (rundir, pid )
    if isSSMPlot():
        picklefile = "%sssm%s%d.pcl" % ( rundir, pid, pid2 )
    with open ( picklefile, "rb" ) as f:
        Zs = pickle.load( f )
        cmass = pickle.load ( f ) ## cmass is pids
        nevents = pickle.load ( f )
        timestamp = pickle.load ( f )
    x = list(Zs.keys())
    x.sort()
    y, yr = [], []
    rs = []
    rsarea = []
    for i in x:
        y_ = Zs[i]
        if type(y_)==tuple:
            if y_[1] > rthresholds[0]:
                rsarea.append ( y_[1] )
            else:
                rsarea.append ( 0. )
            rs.append ( y_[1] )
            y_ = y_[0]
        y2_ = y_
        if y2_ < 0.:
            y2_ = float("nan")
        y.append ( y_ )
        yr.append ( y2_ )
    pname = helpers.toLatex ( pid, addDollars=True )
    if isSSMPlot():
        pname = helpers.toLatex ( pid, addDollars=True, addSign=True )+","+\
                helpers.toLatex ( pid2, addDollars=True, addSign=True )
    fig,ax1 = plt.subplots()
    plt.plot ( x, yr, label="Z(%s), %d events" % ( pname, nevents ), c="tab:blue", zorder=0 )
    ax1.tick_params ( axis="y", labelcolor="tab:blue", labelleft=True )
    ax1.set_ylabel ( "Z", c="tab:blue" )
    ax1.set_xlabel ( "m [GeV]" )
    ax1.set_ylim ( bottom = 2., top=max(yr)*1.03 )
    if len(rs) == len(x):
        ax2 = ax1.twinx()
        ax1.plot ([], [], label="$r_\mathrm{max}$", c="tab:red", zorder=1 )
        ax2.plot ( x, rs, label="$r_\mathrm{max}$", c="tab:red", zorder=2 )
        ax2.tick_params ( axis="y", labelcolor="tab:red" )
        ax2.set_ylim ( bottom=min(rs)*.7, top = 1.9 )
        ax2.set_ylabel ( "$r_\mathrm{max}$", c="tab:red" )
    if len(rsarea) == len(x):
        # ax3 = ax1.twinx()
        ax2.fill ( x, rsarea, lw=0, edgecolor="white", alpha=.2, facecolor="tab:red", zorder=-1 )
    ymax = max(y)
    imax = y.index ( ymax )
    xmax = x[imax]
    param="%d GeV" % xmax
    if isSSMPlot():
        param="%.3f" % xmax
    ax1.scatter ( [ xmax ], [ ymax ], label="maximum Z, Z(%s)=%.2f" % (param, ymax ), s=130, c="k", marker="*", zorder=5 )
    if type(cmass)==tuple:
        cmass = x[int(len(x)/2)]
    param = "%d GeV" % cmass
    if isSSMPlot():
        param="%.3f" % cmass
    Zmax = Zs[cmass]
    if type(Zmax)==tuple:
        Zmax=Zmax[0]
    ax1.scatter ( [ cmass ], [ Zmax ], label="protomodel, Z(%s)=%.2f" % (param, Zmax ), marker="*", s=130, c="g", zorder=10 )
    plt.title ( "Significance Z=Z(%s)" % pname )
    # plt.text ( .8 * max(x),-.17, timestamp )
    plt.text ( .8 * max(x),-.21, timestamp )
    ax1.legend()
    if isSSMPlot():
        plt.xlabel ( "ssm(%s) [GeV]" % pname )
        ax1.set_xlabel ( "ssm(%s) [GeV]" % pname )
    else:
        plt.xlabel ( "m(%s) [GeV]" % pname )

    # plt.text ( .9*min(x)+.1*(max(x)-min(x)), 1.*max(y), "%d events" % nevents )
    figname = "M%d.png" % pid
    if isSSMPlot():
        figname = "ssm_%d_%d.png" % ( pid, pid2 )
    stdvar =  numpy.std ( y )

    if interactive:
        import IPython
        IPython.embed()

    if stdvar < 1e-10:
        print ( "[scanner] standard deviation is a %.2f. Not plotting." % stdvar )
        return

    print ( "[scanner] creating %s" % figname )
    plt.savefig ( figname )
    plt.close()
    if copy:
        dest = os.path.expanduser ( "~/git/smodels.github.io" )
        cmd = "cp %s/%s %s/protomodels/latest/" % ( rundir,figname, dest )
        o = subprocess.getoutput ( cmd )
        print ( "[scanner] %s: %s" % ( cmd, o ) )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='script that takes care of the Z(m) plots' )
    argparser.add_argument ( '-p', '--pid', '--pid1',
            help='pid to consider. If zero, then consider a predefined list [0]',
            type=int, default=0 )
    argparser.add_argument ( '-q', '--pid2',
            help='pid 2. if -1, then scan masses, If not, then scan signal strength multipliers. If zero, then scan all ssms [-1]',
            type=int, default=-1 )
    argparser.add_argument ( '-n', '--nproc',
            help='number of processes [10]',
            type=int, default=10 )
    argparser.add_argument ( '-f', '--factor',
            help='multiplication factor [1.007]',
            type=float, default=1.007 )
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
    argparser.add_argument ( '-I', '--interactive',
            help='interactive mode, starts ipython (only works with -d, and not in bulk mode)',
            action="store_true" )
    argparser.add_argument ( '-F', '--force_copy',
            help='force copying the hiscore.pcl file',
            action="store_true" )
    argparser.add_argument ( '-c', '--copy',
            help='copy plots to ~/git/smodels.github.io/protomodels/latest/',
            action="store_true" )
    args = argparser.parse_args()
    allpids = [ 1000001, 2000005, 1000021, 1000006, 2000006, 1000024, 1000022, 1000005, 1000002, 1000003 ]
    pids = args.pid
    if pids == 0:
        pids = allpids
    if args.produce:
        hi = getHiscore( args.force_copy )
        if args.pid2 > 0:
            produceSSMs( hi, args.pid, args.pid2, args.nevents, args.dry_run, args.nproc, args.factor )
        else:
            produce( hi, pids, args.nevents, args.dry_run, args.nproc, args.factor )
    if args.draw:
        if args.pid != 0:
            draw( pids, args.interactive, args.pid2, args.copy )
        else:
            for pid in allpids:
                try:
                    draw( pid, args.interactive, args.pid2, args.copy )
                except Exception as e:
                    print ( "[scanner] skipping %d: %s" % ( pid, e ) )
