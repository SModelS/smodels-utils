#!/usr/bin/env python3

""" Plot NLLs for various approximations of the likelihood """

import matplotlib.pyplot as plt
import pickle
import random
import matplotlib
import pyslha, math
import subprocess
import os
from smodels.tools import runtime
runtime._experimental = True
from smodels_utils.helper import prettyDescriptions
from smodels.experiment.databaseObj import Database
from smodels.experiment import txnameObj
txnameObj.TxNameData._keep_values = True
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.theory import decomposer
from smodels.particlesLoader import BSMList
from smodels.share.models.SMparticles import SMList
from smodels.theory.model import Model
from smodels.base.physicsUnits import GeV, pb, fb
from smodels.tools.statistics import likelihoodFromLimits
from smodels_utils.helper import slhaManipulator
        
def writeToPickle( D ):
    """ write these guys to a pickle file """
    fname = "nlls.pcl" 
    if os.path.exists ( fname ):
        cmd = f"cp {fname} old.pcl"
        subprocess.getoutput ( cmd )
    with open ( fname, "wb" ) as f:
        pickle.dump ( D, f )
        f.close()

def loadFromPickle():
    """ write these guys to a pickle file """
    fname = "nlls.pcl" 
    with open ( fname, "rb" ) as f:
        D = pickle.load ( f )
        f.close()
    return D

def plot ( D ):
    """ plot content of dictionary D """
    x=D["x"]
    yUL = D["yUL"]
    yBestSR = D["yBestSR"]
    yUL = D["yUL"]
    yPyhf = D["yPyhf"]
    plt.plot ( x, yUL, label="likelihoods from limits" )
    plt.plot ( x, yBestSR, label="best signal region" )
    plt.plot ( x, yPyhf, label="pyhf combo" )
    plt.legend()
    plt.title ( f"Comparison of NLLs" )
    #plt.yscale ( "log" )
    plt.xlabel ( "mass(mother) [GeV]" )
    plt.ylabel ( "NLL")
    plt.savefig ( f"nll_comparison.png" )
    plt.clf()

def matches ( f, args ):
    """ report if filename matches requirements """
    if not f.endswith ( ".slha" ):
        return False
    if args.lifetime != None and not args.lifetime in f:
        return False
    if args.mlsp != None and not "_%s_" % args.mlsp in f:
        return False
    return True

def create():
    """ create the dictionary / pickle file """
    import argparse
    argparser = argparse.ArgumentParser( description = "plot NLLs for various approximations of the likelihood" )
    argparser.add_argument ( "-a", "--analysis",
            help="analysis [ATLAS-SUSY-2019-08]",
            type=str, default="ATLAS-SUSY-2019-08" )
    argparser.add_argument ( "-l", "--lifetime",
            help="lifetime string [None]",
            type=str, default=None )
    argparser.add_argument ( "-t", "--txname",
            help="txname [TChiWH]",
            type=str, default="TChiWH" )
    argparser.add_argument ( "-m", "--mlsp",
            help="mass of lsp [None]",
            type=int, default=None )
    args = argparser.parse_args()
    db = Database ( "../../smodels-database" )
    mlsp = args.mlsp
    if mlsp == None and args.lifetime!= None:
        mlsp = 1

    for txname in [ args.txname ]: # , "TSmuSmuDisp" ]:
        tarball="../slha/%s.tar.gz" % txname
        tar = tarfile.open(tarball,"r:gz")

        files = [f for f in tar.getnames() if matches ( f, args ) ]
        erf = db.getExpResults ( analysisIDs = [ args.analysis ], useNonValidated=True,
                                 dataTypes = [ "efficiencyMap" ], txnames = [ txname ] )[0]
        #era = db.getExpResults ( analysisIDs = [ args.analysis ], useNonValidated=True,
        #                         dataTypes = [ "all" ], txnames = [ txname ] )
        #print ( "era", len(era) )
        x,yUL,yBestSR,yPyhf=[],[],[],[]
        print ( f"[plotNLLs] we have {len(files)} points." )
        for f in files[:]:
            slhafile = slhaManipulator.extractSLHAFileFromTarball ( f )
            model = Model(BSMparticles=BSMList, SMparticles=SMList)
            model.updateParticles ( inputFile=slhafile )
            # model.updateParticles ( inputFile="../slha/" + f )
            pyfile=pyslha.readSLHAFile ( slhafile )
            masses=pyfile.blocks["MASS"]
            mmother = masses[1000023]
            reallsp = masses[1000022]
            xsec = 0.
            for k,xsecs in pyfile.xsections.items():
                for xs in xsecs.xsecs:
                    sqrts = xs.sqrts
                    order = xs.qcd_order_str
                    if abs ( sqrts - 13000. ) > 1.:
                        continue
                    if order != "NLO+LL":
                        continue
                    xsec += xs.value
            mothervec = mmother*GeV
            if args.lifetime != None:
                mothervec = ( mmother*GeV, args.lifetime*GeV )
            if mlsp == None:
                mlsp = reallsp
            # massvec = [[ (mmother*GeV, 3.4e-16*GeV), 1*GeV ] ] * 2
            massvec = [[ mothervec, mlsp*GeV ] ] * 2
            toplist = decomposer.decompose ( model, 0.01*fb, True, True, 5.*GeV )
            preds = theoryPredictionsFor ( erf, toplist, combinedResults=False,
                                           useBestDataset=True )
            if type(preds) != type(None):
                # llhd = preds[0].llhd
                x.append ( mmother )
                lumi = preds[0].dataset.globalInfo.lumi
                llhd = preds[0].getLikelihood()
                oul = float ( preds[0].getUpperLimit()*lumi )
                eul = float ( preds[0].getUpperLimit( expected = True )*lumi )
                nsig = (xsec * lumi).asNumber() #  * preds[0].eff
                ulllhd = likelihoodFromLimits ( oul, eul, nsig, nll=True ) 
                if type(llhd) == type(None):
                    yBestSR.append ( float("nan") )
                else:
                    print ( "best SR mass", mmother, "nll", - math.log ( llhd ) )
                    yBestSR.append ( - math.log ( llhd ) * random.uniform(.9,1.1 ) )
                if type(ulllhd) == type(None):
                    yUL.append ( float("nan") )
                else:
                    # print ( "UL-based mass", mmother , "nll", ulllhd )
                    if ulllhd > 500.:
                        ulllhd = 500.
                    yUL.append ( ulllhd )

            cpreds = theoryPredictionsFor ( erf, toplist, combinedResults=True,
                                           useBestDataset=False )
            if type(cpreds) != type(None):
                print ( "cpreds", cpreds[0].dataType() )
                # llhd = preds[0].llhd
                cpreds[0].computeStatistics()
                cllhd = cpreds[0].likelihood
                if type(cllhd) == type(None):
                    yPyhf.append( float ("nan" ) )
                else:
                    print ( "comb mass", mmother , "nll", - math.log ( cllhd ) )
                    yPyhf.append ( - math.log ( cllhd ) )
            # oul = eru.getUpperLimitFor ( None, expected=False, txname=txname, mass = massvec )
            # print ( oul )
            os.unlink ( slhafile )
    D = { "x": x, "yUL": yUL, "yBestSR": yBestSR, "yPyhf": yPyhf }
    writeToPickle( D )
    return D

def main():
    D = create()
    # D = loadFromPickle()
    plot ( D )

main()
