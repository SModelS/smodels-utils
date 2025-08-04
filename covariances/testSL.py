#!/usr/bin/python3

from __future__ import print_function
import sys
import math
import array
import time
import random
from smodels.tools.simplifiedLikelihoods import Data,UpperLimitComputer
from smodels.base.physicsUnits import fb
from smodels.tools.runtime import nCPUs
import binned_model
import os
import glob
import numpy
import copy

def createBinnedModel(bins):
    """ create a sub-model with only <bins> (list of indices) """
    import model_90 as m9
    m=Data( m9.data, m9.background, m9.covariance, m9.third_moment, m9.signal,"o90", lumi = 1./fb)
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
    m = Data ( observed=D, backgrounds=B, covariance=C, third_moment=S,
                efficiencies=sig, name=f"model{int(n)}" )
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

    ROOT.RMIN=0.

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
    # print ( "[nick] bins=", bins )
    model = binned_model.create ( bins )
    # print ( "[nick] model=", model.name )

    # CHECK we don't go over the max
    if model.nbins > ROOT.MAXBINS: sys.exit(f"Too many bins (nbins > {int(ROOT.MAXBINS)}), you should modify MAXBINS in .C code")

    # print ( "[nick] Simplified Likelihood for model file --> ", end="" )
    #try : print ( model.name )
    #except : print ( " no named model file" )

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
    # print ( "Nick reports: %s" % ret )
    Files=glob.glob("SL.root*")
    for f in Files:
        try:
            os.unlink(f)
        except Exception as e:
            pass
    return ret

def one_turn( nrun, m=None, maxbins=50, algos=["all"] ):
    """ run one round with model m. If none,
        create it with random signal regions """

    def runAlgo ( name ):
        if "all" in algos:
            return True
        if name in algos:
            return True
        return False

    n=90
    b=list(range(n))
    random.shuffle ( b )
    nmax=int ( random.uniform(2,maxbins) )
    bins=b[:nmax]
    if not m:
        m=createBinnedModel ( bins )
    else:
        bins=m._bins
    ret = { "#": nrun, "bins": bins, "nbins": len(bins) }
    mc=copy.deepcopy ( m )
    mc.skewness = None
    mc.computeABC()
    ulComp100 = UpperLimitComputer ( lumi = 1. / fb, ntoys=100, cl=.95 )
    ulComp = UpperLimitComputer ( lumi = 1. / fb, ntoys=1000, cl=.95 )
    ulComp10K = UpperLimitComputer ( lumi = 1. / fb, ntoys=10000, cl=.95 )
    print ( f"- Run #{int(nrun)} with {len(bins)} bins:" )

    gul= [ None ]
    if runAlgo("profl"):
        print ( "- profiling linear" )
        ul = None
        t0=time.time()
        try:
            ul = ulComp.ulSigma ( mc, marginalize=False ).asNumber(fb)
        except Exception as e:
            print ( f"Exception at profiling: {e}" )
            ul=f"{type(e)} {str(e)}"
        ret["t_profl"]=time.time()-t0
        ret["ul_profl"]=ul
        gul[0]=ul

    if runAlgo("margl"):
        print ( "- marginalizing linear" )
        ul = None
        t0=time.time()
        try:
            ul = ulComp.ulSigma ( mc, marginalize=True ).asNumber(fb)
        except Exception as e:
            print ( f"Exception at profiling: {e}" )
            ul=f"{type(e)} {str(e)}"
        ret["t_margl"]=time.time()-t0
        ret["ul_margl"]=ul
        gul[0]=ul

    if runAlgo ( "marg100" ):
        print ( "- marginalizing 100" )
        ul = None
        tm=time.time()
        try:
            ul = ulComp100.ulSigma ( m ).asNumber(fb)
        except Exception as e:
            print ( f"Exception at marginalization 100: {e}" )
            ul=f"{type(e)} {str(e)}"
        t0=time.time()
        t_marg100 = t0-tm
        ret["ul_marg100"]=ul
        ret["t_marg100"]=t_marg100
        gul[0]=ul

    if runAlgo ( "marg" ):
        print ( "- marginalizing" )
        ul = None
        t0=time.time()
        try:
            ul = ulComp.ulSigma ( m ).asNumber(fb)
        except Exception as e:
            print ( f"Exception at marginalization: {e}" )
            ul=f"{type(e)} {str(e)}"
        ret["ul_marg"]=ul
        ret["t_marg"]=time.time()-t0
        gul[0]=ul

    if runAlgo ( "marg10" ):
        ul=None
        print ( "- marginalizing 10K" )
        t0=time.time()
        try:
            ul = ulComp10K.ulSigma ( m ).asNumber(fb)
        except Exception as e:
            print ( f"Exception at marginalization: {e}" )
            ul=f"{type(e)} {str(e)}"
        ret["ul_marg10"]=ul
        ret["t_marg10"]=time.time()-t0
        gul[0]=ul

    if runAlgo("prof"):
        print ( "- profiling" )
        ul = None
        t0=time.time()
        try:
            ul = ulComp.ulSigma ( m, marginalize=False ).asNumber(fb)
        except Exception as e:
            print ( f"Exception at profiling: {e}" )
            ul=f"{type(e)} {str(e)}"
        ret["t_prof"]=time.time()-t0
        ret["ul_prof"]=ul
        gul[0]=ul

    if runAlgo ( "nick" ):
        rmin,rmax=0.,2000.
        if type(gul[0])==float:
            rmin=0.
            rmax=5.*ul
        ul=None
        print ( f"- nicks code in [{rmin},{rmax}]" )
        t0=time.time()
        try:
            ctr=0
            while ul==None:
                ul=runNick( bins, rmin=rmin, rmax=rmax )
                delta_max = rmax - ul
                delta_min = ul - rmin
                if delta_max < .2:
                    print ( "hit the max on r, rerun with higher r" )
                    rmin,rmax=2.*rmin,4.*rmax
                    ul=None
                if delta_min < .2:
                    print ( "hit the min on r, rerun with lower r" )
                    rmin,rmax=.15*rmin,.3*rmax
                    ul=None
                if ctr>100:
                    # stop after 100
                    ul=-1.
                    break
        except Exception as e:
            print ( f"Exception in Nicks code: {e}" )
            ul=f"Exception {str(e)}"
        ret["t_nick"]=time.time()-t0
        ret["ul_nick"]=ul

    if runAlgo ( "nickn" ):
        rmin,rmax=0.,100.
        if type(gul[0])==float:
            rmin=.4*ul
            rmax=1.3*ul
        ul=None
        print ( f"- nicks code in narrow [{rmin},{rmax}]" )
        t0=time.time()
        try:
            ctr=0
            while ul==None:
                ul=runNick( bins, rmin=rmin, rmax=rmax )
                delta_max = rmax - ul
                delta_min = ul - rmin
                if delta_max < .2:
                    print ( "hit the max on r, rerun with higher r" )
                    rmin,rmax=2.*rmin,4.*rmax
                    ul=None
                if delta_min < .2:
                    print ( "hit the min on r, rerun with lower r" )
                    rmin,rmax=.15*rmin,.3*rmax
                    ul=None
                if ctr>100:
                    # stop after 100
                    ul=-1.
                    break
        except Exception as e:
            print ( f"Exception in Nicks code: {e}" )
            ul=f"Exception {str(e)}"
        ret["t_nickn"]=time.time()-t0
        ret["ul_nickn"]=ul


    if runAlgo ( "nickl" ):
        rmin,rmax=0.,42.
        if type(gul[0])==float:
            rmin,rmax=0.,2.1*ul
        ul=None
        print ( f"- nicks linear code in [{rmin},{rmax}]" )
        t0=time.time()
        try:
            ctr=0
            while ul==None:
                ctr+=1
                ul=runNick( bins, rmin, rmax, False )
                delta_max =  rmax - ul
                delta_min =  ul - rmin
                if delta_max < .2:
                    print ( "hit the max on r, rerun with higher r" )
                    rmin,rmax=3.*rmin,5*rmax
                    ul=None
                if delta_min < .2:
                    print ( "hit the minimum on r, rerun with lower r" )
                    rmin,rmax=.15*rmin,.3*rmax
                    ul=None
                if ctr>100:
                    # stop after 100
                    ul=-1.
                    break
        except Exception as e:
            print ( f"Exception in Nicks code: {e}" )
            ul=f"{type(e)} {str(e)}"
        ret["t_nickl"]=time.time()-t0
        ret["ul_nickl"]=ul

    return ret

def run ( R, n, sub, max_bins, algos ):
    """ one run. """
    import random
    random.seed(sub)
    f=open(f"results{int(R)}_{int(sub)}.py","w")
    # f.write ( "d=[" )
    for i in range(n):
        r = one_turn( i+n*sub, None, args.max_bins, algos )
        if r == None:
            continue
        print (r)
        f.write ( f"{r},\n" )
        f.flush()
    # f.write ( "]\n" )
    f.close()

if __name__ == "__main__":

    import argparse
    ap = argparse.ArgumentParser( description="Systematically test SL UL computer" )
    ap.add_argument('-b', '--bins', type=str, default="",
                    help='specify bins to be used (comma separated). If empty, choose randomly.' )
    ap.add_argument('-a', '--algos', type=str, default="all",
                    help='specify algos, "all" for all.' )
    ap.add_argument('-m', '--max_bins', type=int, default=40,
                    help='specify maximum number of bins, when choosing randomly.' )
    ap.add_argument('-c', '--ncpus', type=int, default=-1,
                    help='specify number of CPUs, -1 means all avbailable.' )
    ap.add_argument('-N', '--nruns', type=int, default=1000,
                    help='Number of runs. Effective only if bins is empty.' )
    args=ap.parse_args()
    algos = [ x.strip() for x in args.algos.split(",") ]
    iniNick()
    # print ( "args.bins=", type(args.bins) )
    if len(args.bins)>0:
        bins=list(map(int,args.bins.split(",")))
        m=createBinnedModel(bins)
        r=one_turn(0,m,50,algos)
        print("r=",r )
        sys.exit()
    ncpus = args.ncpus
    if ncpus == -1: ncpus = nCPUs()
    R=int(math.ceil( args.nruns / ncpus)) * ncpus
    n= int ( args.nruns / ncpus  )
    print ( f"Running {int(n)} jobs per process" )
    pids=[]
    for cpu in range(ncpus):
        pid=os.fork()
        if pid==0:
            run ( R, n, cpu, args.max_bins, algos )
            sys.exit()
        else:
            pids.append (pid)
    for pid in pids:
        os.waitpid ( pid, 0 )
