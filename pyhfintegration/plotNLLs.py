#!/usr/bin/env python3

""" Plot NLLs for various approximations of the likelihood """

import matplotlib.pyplot as plt
import random
import matplotlib
import pyslha, math
import tarfile
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
from smodels.tools.physicsUnits import GeV, pb, fb
from smodels.tools.statistics import likelihoodFromLimits

def main():
    import argparse
    argparser = argparse.ArgumentParser( description = "plot NLLs for various approximations of the likelihood" )
    argparser.add_argument ( "-a", "--analysis",
            help="analysis [ATLAS-SUSY-2018-14]",
            type=str, default="ATLAS-SUSY-2018-14" )
    argparser.add_argument ( "-l", "--lifetime",
            help="lifetime string [3.4e-16]",
            type=str, default="3.4e-16" )
    args = argparser.parse_args()
    db = Database ( "../../smodels-database" )
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    slhafile = "../slha/TSelSelDisp_1000_1.4e-14_0_1000_1.4e-14_0.slha"
    model.updateParticles(inputFile=slhafile)

    for txname in [ "TSelSelDisp" ]: # , "TSmuSmuDisp" ]:
        tarball="../slha/%s.tar.gz" % txname
        tar = tarfile.open(tarball,"r:gz")
        files = [f for f in tar.getnames() if '.slha' in f and args.lifetime in f ]
        erf = db.getExpResults ( analysisIDs = [ args.analysis ], useNonValidated=True,
                                 dataTypes = [ "efficiencyMap" ], txnames = [ txname ] )[0]
        #era = db.getExpResults ( analysisIDs = [ args.analysis ], useNonValidated=True,
        #                         dataTypes = [ "all" ], txnames = [ txname ] )
        #print ( "era", len(era) )
        x,yUL,yBestSR,yPyhf=[],[],[],[]
        for f in files:
            fobj = tar.extractfile(f)
            txt = fobj.read()# .replace("\\n","\n" )
            model.updateParticles ( inputFile="../slha/" + f )
            pyfile=pyslha.readSLHA( txt.decode("ascii") )
            masses=pyfile.blocks["MASS"]
            mslep = masses[1000011]
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
            fobj.close()
            massvec = [[ (mslep*GeV, 3.4e-16*GeV), 1*GeV ] ] * 2
            toplist = decomposer.decompose ( model, 0.01*fb, True, True, 5.*GeV )
            preds = theoryPredictionsFor ( erf, toplist, combinedResults=False,
                                           useBestDataset=True )
            if type(preds) != type(None):
                # llhd = preds[0].llhd
                x.append ( mslep )
                lumi = preds[0].dataset.globalInfo.lumi
                llhd = preds[0].getLikelihood()
                oul = float ( preds[0].getUpperLimit()*lumi )
                eul = float ( preds[0].getUpperLimit( expected = True )*lumi )
                nsig = (xsec * lumi).asNumber() #  * preds[0].eff
                ulllhd = likelihoodFromLimits ( oul, eul, nsig, nll=True ) 
                if type(llhd) == type(None):
                    yBestSR.append ( float("nan") )
                else:
                    print ( "best SR mass", mslep, "nll", - math.log ( llhd ) )
                    yBestSR.append ( - math.log ( llhd ) * random.uniform(.9,1.1 ) )
                if type(ulllhd) == type(None):
                    yUL.append ( float("nan") )
                else:
                    # print ( "UL-based mass", mslep, "nll", ulllhd )
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
                    print ( "comb mass", mslep, "nll", - math.log ( cllhd ) )
                    yPyhf.append ( - math.log ( cllhd ) )
            # oul = eru.getUpperLimitFor ( None, expected=False, txname=txname, mass = massvec )
            # print ( oul )
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

main()
