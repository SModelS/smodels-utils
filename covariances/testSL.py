#!/usr/bin/python

from __future__ import print_function
import sys
import array
import time
import numpy
import random
from smodels.tools.SimplifiedLikelihoods import Model,UpperLimitComputer
from smodels.tools.physicsUnits import fb
import binned_model
import ROOT
import os
import glob

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

def run( bins, rmin, rmax ):
    #  from optparse import OptionParser
    #(options,args)=parser.parse_args()
    from ROOT import simplifiedLikelihoodLinear
    ROOT.outname="SL"

    ROOT.RMIN= rmin ## 200. / len(bins)
    ROOT.RMAX= rmax ## 200. / len(bins)

    # HERE we build up the elements for the SL from a python file
    # model = __import__(options.model)
    # bins = list ( map ( int, options.model.split(",") ) )
    print ( "bins=", bins )
    model = binned_model.create ( bins )
    print ( "model=", model.name )

    # CHECK we don't go over the max
    if model.nbins > ROOT.MAXBINS: sys.exit("Too many bins (nbins > %d), you should modify MAXBINS in .C code"%ROOT.MAXBINS)

    print ( "Simplified Likelihood for model file --> ", end="" )
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
    Files=glob.glob("SL.root*")
    for f in Files:
        os.unlink(f)
    return ret

def one_turn():
    n_run[0]=n_run[0]+1
    n=90
    b=range(n)
    random.shuffle ( b )
    nn=20 ## should be n
    nmax=int ( random.uniform(2,nn) )
    bins=b[:nmax]
    m=createBinnedModel ( bins )
    ulComp = UpperLimitComputer ( lumi = 1. / fb, ntoys=1000, cl=.95 )
    ulComp10K = UpperLimitComputer ( lumi = 1. / fb, ntoys=10000, cl=.95 )
    print ( "- Run #%d with %d bins:" % (n_run[0], len(bins)) )
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
    print ( "- nicks code" )
    rmax=10.
    if type(ul)==float:
        rmax=2.*ul/100.
    nick=None
    try:
        nick=run( bins, rmin=-.5, rmax=rmax )
    except Exception as e:
        print ( "Exception in Nicks code: %s" % e )
        nick=None
    t2=time.time()
    t_nick = t2-t1b
    nickn=None
    print ( "- nicks code, narrow" )
    try:
        nickn=run( bins, nick*.8, nick*1.2 )
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
    ret = { "#": n_run[0], "bins": bins, "ul_nick": 100.*nick, "t_nick": t_nick, "ul_marg10": ul10,
            "t_marg10": t_marg10, "ul_nickn": 100.*nickn, "t_nickn": t_nickn,
            "ul_marg": ul, "t_marg": t_marg, "ul_prof": ulP, "t_prof": t_prof, "nbins":len(bins) }
    return ret


iniNick()
R=10
f=open("results%d.py" % R,"w")
f.write ( "d=[" )
for i in range(R):
    r = one_turn()
    if r == None:
        continue
    print (r)
    f.write ( "%s,\n" % r )
    f.flush()
f.write ( "]\n" )
f.close()
