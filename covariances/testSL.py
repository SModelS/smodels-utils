#!/usr/bin/python

from __future__ import print_function
import sys
import array
import time
import random
from smodels.tools.SimplifiedLikelihoods import Model,UpperLimitComputer
from smodels.tools.physicsUnits import fb
import binned_model
import os
import glob
import numpy
import copy

n_run=[0]

def createBinnedModel(bins):
    """ create a sub-model with only <bins> (list of indices) """
    import model_90 as m9
    m=Model ( m9.data, m9.background, m9.covariance, m9.third_moment, m9.signal,  "tmp" )
    S=[]
    for i,s in enumerate ( m9.third_moment ):
        if i in bins:
            S.append ( s )
    D=[]
    for i,d in enumerate ( m9.data ):
        if i in bins:
            D.append ( d )
    B=[]
    for i,b in enumerate ( m9.background ):
        if i in bins:
            B.append ( b )
    sig=[]
    for i,s in enumerate ( m9.signal ):
        if i in bins:
            sig.append ( s/100. )
    n=len(m9.data)
    C=[]
    for i in range(n):
        if not i in bins:
            continue
        ## correct row, now pick correct columns
        col=[]
        for j,e in enumerate ( m.covariance[i] ):
            if j in bins:
                col.append ( e )
        C.append ( col )
    m = Model ( data=D, backgrounds=B, covariance=C, skewness=S,
                efficiencies=sig, name="model%d" % n )
    m._bins=bins
    return m

def iniNick():
    # initialisie Nicks stuff
    """
    if options.includeQuadratic:
      ROOT.gROOT.ProcessLine(".L simplifiedLikelihoodQuadratic.C")
      from ROOT import simplifiedLikelihoodQuadratic

    else:
      ROOT.gROOT.ProcessLine(".L simplifiedLikelihoodLinear.C")
      from ROOT import simplifiedLikelihoodLinear
    """
    import ROOT
    ROOT.gROOT.ProcessLine(".L simplifiedLikelihoodLinear.C")
    from ROOT import simplifiedLikelihoodLinear
    verbose=False

    if not verbose:
      ROOT.RooMsgService.instance().setSilentMode(True)
      ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.ERROR)

    # Default ROOT minimizer options
    #ROOT.Math.MinimizerOptions.SetDefaultStrategy(2);

    ROOT.RMIN=-.5

    ROOT.gMultiplicative=False
    ROOT.ignoreCorrelation=False
    ROOT.justCalcLimit=True
    ROOT.verb=verbose
    ROOT.globalNpoints=30
    ROOT.includeQuadratic=True # False
    ROOT.outname="SL"

def runNick( bins, rmin, rmax, quadratic=True ):
    #  from optparse import OptionParser
    #(options,args)=parser.parse_args()
    import ROOT
    from ROOT import simplifiedLikelihoodLinear
    ROOT.outname="SL"
    ROOT.includeQuadratic=quadratic

    # ROOT.RMIN= rmin ## 200. / len(bins)
    ROOT.RMAX= rmax ## 200. / len(bins)

    # HERE we build up the elements for the SL from a python file
    # model = __import__(options.model)
    # bins = list ( map ( int, options.model.split(",") ) )
    print ( "[nick] bins=", bins )
    model = binned_model.create ( bins )
    print ( "[nick] model=", model.name )

    # CHECK we don't go over the max
    if model.nbins > ROOT.MAXBINS: sys.exit("Too many bins (nbins > %d), you should modify MAXBINS in .C code"%ROOT.MAXBINS)

    print ( "[nick] Simplified Likelihood for model file --> ", end="" )
    try : print ( model.name )
    except : print ( " no named model file" )

    ROOT.globalNbins      = model.nbins

    for i in range(model.nbins):
      ROOT.globalData[i]       = model.data[i]
      ROOT.globalBackground[i] = model.background[i]
      ROOT.globalSignal[i]     = model.signal[i]
      if ROOT.includeQuadratic : ROOT.globalThirdMoments[i]     = model.third_moment[i]

    for j in range(model.nbins*model.nbins):
      ROOT.globalCovariance[j] = model.covariance[j]

    #if options.includeQuadratic: simplifiedLikelihoodQuadratic()
    #else: simplifiedLikelihoodLinear()
    ret=simplifiedLikelihoodLinear()
    print ( "Nick reports: %s" % ret )
    Files=glob.glob("SL.root*")
    for f in Files:
        os.unlink(f)
    return ret

def one_turn( m=None, maxbins=50 ):
    """ run one round with model m. If none,
        create it with random signal regions """
    n_run[0]=n_run[0]+1
    n=90
    b=range(n)
    random.shuffle ( b )
    nmax=int ( random.uniform(2,maxbins) )
    bins=b[:nmax]
    if not m:
        m=createBinnedModel ( bins )
        mc=copy.deepcopy ( m )
        mc.skewness = None
        mc.computeABC()
    else:
        bins=m._bins
    ulComp100 = UpperLimitComputer ( lumi = 1. / fb, ntoys=100, cl=.95 )
    ulComp = UpperLimitComputer ( lumi = 1. / fb, ntoys=1000, cl=.95 )
    ulComp10K = UpperLimitComputer ( lumi = 1. / fb, ntoys=10000, cl=.95 )
    print ( "- Run #%d with %d bins:" % (n_run[0], len(bins)) )
    print ( "- marginalizing 100" )
    ul100 = None
    tm=time.time()
    try:
        ul100 = ulComp100.ulSigma ( m ).asNumber(fb)
    except Exception as e:
        print ( "Exception at marginalization 100: %s" % e )
        ul100="%s %s" % (type(e), str(e) )
    t0=time.time()
    t_marg100 = t0-tm
    print ( "- marginalizing" )
    ul = None
    t0=time.time()
    try:
        ul = ulComp.ulSigma ( m ).asNumber(fb)
    except Exception as e:
        print ( "Exception at marginalization: %s" % e )
        ul="%s %s" % (type(e), str(e) )
    t1=time.time()
    t_marg = t1-t0
    ul10=None
    print ( "- marginalizing 10K" )
    try:
        ul10 = ulComp10K.ulSigma ( m ).asNumber(fb)
    except Exception as e:
        print ( "Exception at marginalization: %s" % e )
        ul10="%s %s" % (type(e), str(e) )
    t1b=time.time()
    t_marg10 = t1b-t1
    rmax=10.
    if type(ul)==float:
        rmax=2.*ul/100.
    nick=None
    print ( "- nicks code with rmax=%s" % rmax )
    try:
        nick=runNick( bins, rmin=-.5, rmax=rmax )
    except Exception as e:
        print ( "Exception in Nicks code: %s" % e )
        nick=None
    t2=time.time()
    t_nick = t2-t1b
    nickn=None
    print ( "- nicks code, narrow" )
    try:
        nickn=runNick( bins, nick*.6, nick*1.3, False )
        # nickn=runNick( bins, rmin=nick*.8, rmax=nick*1.2 )
    except Exception as e:
        print ( "Exception in Nicks code: %s" % e )
        nickn="%s %s" % ( type(e), str(e) )
    t2b=time.time()
    t_nickn = t2b-t2
    print ( "- profiling" )
    ulP = None
    try:
        ulP = ulComp.ulSigma ( m, marginalize=False ).asNumber(fb)
    except Exception as e:
        print ( "Exception at profiling: %s" % e )
        ulP="%s %s" % (type(e), str(e) )
    t3=time.time()
    t_prof = t3-t2b
    print ( "- profiling linear" )
    ulPlin = None
    try:
        ulPlin = ulComp.ulSigma ( mc, marginalize=False ).asNumber(fb)
    except Exception as e:
        print ( "Exception at profiling: %s" % e )
        ulPlin="%s %s" % (type(e), str(e) )
    t4=time.time()
    t_proflin = t4-t3

    print ( "- marginalizing linear" )
    ulMlin = None
    try:
        ulMlin = ulComp.ulSigma ( mc, marginalize=True ).asNumber(fb)
    except Exception as e:
        print ( "Exception at profiling: %s" % e )
        ulMlin="%s %s" % (type(e), str(e) )
    t5=time.time()
    t_marglin = t5-t4
    ret = { "#": n_run[0], "bins": bins, "ul_nick": 100.*nick, "t_nick": t_nick, 
            "ul_marg10": ul10, "t_marg10": t_marg10, "ul_nickn": 100.*nickn, 
            "t_nickn": t_nickn, "ul_marg100": ul100, "t_marg100": t_marg100, 
            "ul_profl": ulPlin, "t_profl": t_proflin, "ul_marg": ul, "t_marg": t_marg, 
            "ul_prof": ulP, "t_prof": t_prof, "nbins":len(bins), "t_margl": t_marglin,
            "ul_margl": ulMlin }
    return ret


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser( description="Systematically test SL UL computer" )
    ap.add_argument('-b', '--bins', type=str, default="",
                    help='specify bins to be used (comma separated). If empty, choose randomly.' )
    ap.add_argument('-m', '--max_bins', type=int, default=40,
                    help='specify maximum number of bins, when choosing randomly.' )
    ap.add_argument('-N', '--nruns', type=int, default=1000,
                    help='Number of runs. Effective only if bins is empty.' )
    args=ap.parse_args()
    iniNick()
    # print ( "args.bins=", type(args.bins) )
    if len(args.bins)>0:
        bins=map(int,args.bins.split(","))
        m=createBinnedModel(bins)
        r=one_turn(m)
        print("r=",r )
        sys.exit()
    R=args.nruns
    f=open("results%d.py" % R,"w")
    f.write ( "d=[" )
    for i in range(R):
        r = one_turn( None, args.max_bins )
        if r == None:
            continue
        print (r)
        f.write ( "%s,\n" % r )
        f.flush()
    f.write ( "]\n" )
    f.close()
