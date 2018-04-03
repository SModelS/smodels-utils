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

    ROOT.RMIN= rmin ## 200. / len(bins)
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
      if ROOT.includeQuadratic: 
        ROOT.globalThirdMoments[i] = model.third_moment[i]
      else: 
        ROOT.globalThirdMoments[i] = 0.

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

def one_turn( m=None, maxbins=50, algos=["all"] ):
    """ run one round with model m. If none,
        create it with random signal regions """

    def runAlgo ( name ):
        if "all" in algos:
            return True
        if name in algos:
            return True
        return False

    n_run[0]=n_run[0]+1
    n=90
    b=range(n)
    random.shuffle ( b )
    nmax=int ( random.uniform(2,maxbins) )
    bins=b[:nmax]
    if not m:
        m=createBinnedModel ( bins )
    else:
        bins=m._bins
    ret = { "#": n_run[0], "bins": bins }
    mc=copy.deepcopy ( m )
    mc.skewness = None
    mc.computeABC()
    ulComp100 = UpperLimitComputer ( lumi = 1. / fb, ntoys=100, cl=.95 )
    ulComp = UpperLimitComputer ( lumi = 1. / fb, ntoys=1000, cl=.95 )
    ulComp10K = UpperLimitComputer ( lumi = 1. / fb, ntoys=10000, cl=.95 )
    print ( "- Run #%d with %d bins:" % (n_run[0], len(bins)) )

    if runAlgo ( "marg100" ):
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
        ret["ul_marg100"]=ul100
        ret["t_marg100"]=t_marg100

    if runAlgo ( "marg" ):
        print ( "- marginalizing" )
        ul = None
        t0=time.time()
        try:
            ul = ulComp.ulSigma ( m ).asNumber(fb)
        except Exception as e:
            print ( "Exception at marginalization: %s" % e )
            ul="%s %s" % (type(e), str(e) )
        ret["ul_marg"]=ul
        ret["t_marg"]=time.time()-t0

    if runAlgo ( "marg10" ):
        ul=None
        print ( "- marginalizing 10K" )
        t0=time.time()
        try:
            ul = ulComp10K.ulSigma ( m ).asNumber(fb)
        except Exception as e:
            print ( "Exception at marginalization: %s" % e )
            ul="%s %s" % (type(e), str(e) )
        ret["ul_marg10"]=ul
        ret["t_marg10"]=time.time()-t0

    if runAlgo ( "nick" ):
        rmax=10.
        if type(ul)==float:
            rmax=2.*ul/100.
        ul=None
        print ( "- nicks code with rmax=%s" % rmax )
        t0=time.time()
        try:
            ul=100.*runNick( bins, rmin=-.5, rmax=rmax )
        except Exception as e:
            print ( "Exception in Nicks code: %s" % e )
            ul="Exception %s" % str(e)
        ret["t_nick"]=time.time()-t0
        ret["ul_nick"]=ul

    if runAlgo ( "nickn" ):
        r=10.
        if type(ul)==float:
            r=2.*ul/100.
        ul=None
        print ( "- nicks code, linear, r=%s" % r )
        t0=time.time()
        try:
            ul=100.*runNick( bins, r*.1, r*2.1, False )
        except Exception as e:
            print ( "Exception in Nicks code: %s" % e )
            ul="%s %s" % ( type(e), str(e) )
        ret["t_nickn"]=time.time()-t0
        ret["ul_nickn"]=ul

    if runAlgo("prof"):
        print ( "- profiling" )
        ul = None
        t0=time.time()
        try:
            ul = ulComp.ulSigma ( m, marginalize=False ).asNumber(fb)
        except Exception as e:
            print ( "Exception at profiling: %s" % e )
            ul="%s %s" % (type(e), str(e) )
        ret["t_prof"]=time.time()-t0
        ret["ul_prof"]=ul

    if runAlgo("profl"):
        print ( "- profiling linear" )
        ul = None
        t0=time.time()
        try:
            ul = ulComp.ulSigma ( mc, marginalize=False ).asNumber(fb)
        except Exception as e:
            print ( "Exception at profiling: %s" % e )
            ul="%s %s" % (type(e), str(e) )
        ret["t_profl"]=time.time()-t0
        ret["ul_profl"]=ul

    if runAlgo("margl"):
        print ( "- marginalizing linear" )
        ul = None
        t0=time.time()
        try:
            ul = ulComp.ulSigma ( mc, marginalize=True ).asNumber(fb)
        except Exception as e:
            print ( "Exception at profiling: %s" % e )
            ul="%s %s" % (type(e), str(e) )
        ret["t_margl"]=time.time()-t0
        ret["ul_margl"]=ul

    return ret


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser( description="Systematically test SL UL computer" )
    ap.add_argument('-b', '--bins', type=str, default="",
                    help='specify bins to be used (comma separated). If empty, choose randomly.' )
    ap.add_argument('-a', '--algos', type=str, default="all",
                    help='specify algos, "all" for all.' )
    ap.add_argument('-m', '--max_bins', type=int, default=40,
                    help='specify maximum number of bins, when choosing randomly.' )
    ap.add_argument('-N', '--nruns', type=int, default=1000,
                    help='Number of runs. Effective only if bins is empty.' )
    args=ap.parse_args()
    algos = [ x.strip() for x in args.algos.split(",") ]
    iniNick()
    # print ( "args.bins=", type(args.bins) )
    if len(args.bins)>0:
        bins=map(int,args.bins.split(","))
        m=createBinnedModel(bins)
        r=one_turn(m,50,algos)
        print("r=",r )
        sys.exit()
    R=args.nruns
    f=open("results%d.py" % R,"w")
    f.write ( "d=[" )
    for i in range(R):
        r = one_turn( None, args.max_bins, algos )
        if r == None:
            continue
        print (r)
        f.write ( "%s,\n" % r )
        f.flush()
    f.write ( "]\n" )
    f.close()
