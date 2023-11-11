#!/usr/bin/env python3

""" create a spey point, ready for jacks inspection """

def hackForPython39():
    # no idea why python3.9 doesnt respect PYTHONPATH, but well, it doesnt
    # here is my way around, to check if the problem occurs also with 
    # python39 and anaconda3/2022.05 -- it does
    import sys
    sys.path.insert(0,"/users/wolfgan.waltenberger/git/smodels")
    sys.path.insert(0,"/users/wolfgan.waltenberger/git/smodels-utils")

from typing import Dict
from smodels.tools import speyTools
from smodels_utils.helper.various import getValidationDataPathName, getValidationModuleFromPath
speyTools._debug["writePoint"]=True
import os, sys, subprocess
    
speyfilename = "forjack.py"

def runSModelS( args : Dict, slhafile : os.PathLike ):
    from smodels.theory import decomposer 
    from smodels.tools.physicsUnits import fb, GeV, TeV                            
    from smodels.theory.theoryPrediction import theoryPredictionsFor, TheoryPredictionsCombiner                                                                   
    from smodels.experiment.databaseObj import Database
    from smodels.particlesLoader import BSMList                                    
    from smodels.share.models.SMparticles import SMList                            
    from smodels.theory.model import Model 
    import numpy
    numpy.random.seed(0)
    dbpath = args["dbpath"]
    db = Database ( dbpath )
    model = Model(BSMparticles=BSMList, SMparticles=SMList) 
    model.updateParticles(inputFile=slhafile)
    sigmacut = 0.005*fb
    mingap = 5*GeV
    toplist = decomposer.decompose( model, sigmacut, doCompress=True, 
                                    doInvisible=True, minmassgap=mingap)
    anaids = [ args["analysisname"].replace("-eff","") ]
    listOfExpRes = db.getExpResults( analysisIDs = anaids )
    for expResult in listOfExpRes:                                             
        predictions = theoryPredictionsFor(expResult, toplist, combinedResults=True )
    npredictions=len(predictions)
    print ( f"{npredictions} predictions: {predictions[0].getUpperLimitOnMu():.4g}" )

def runSpeyCode():
    cmd = f"./{speyfilename}"
    o = subprocess.getoutput ( cmd )
    print ( o )

def createSpeyCode():
    f=open(speyfilename,"wt")
    f.write( "#!/usr/bin/env python3\n\n" )
    with open ( "data.txt", "rt" ) as g:
        f.write ( g.read() )
    f.write (
"""
import spey

                                                                               
stat_wrapper = spey.get_backend("default_pdf.correlated_background")           
speyModel = stat_wrapper( data = obsN, background_yields = bg,
    covariance_matrix = cov, signal_yields = nsig,
    xsection = [ x / lumi for x in nsig ], analysis = analysis )

print ( f"spey oUL(mu)={speyModel.poi_upper_limit( ):.4f}" ) 
print ( f"spey eUL(mu)={speyModel.poi_upper_limit( expected = spey.ExpectationType.aposteriori ):.4f}" ) 

""" )
    f.close()
    os.chmod ( speyfilename, 0o755 )
    print ( "created", speyfilename )


def createSLHAFile ( args : Dict ) -> str:
    """ create the SLHA file that we need, extract it from 
        validation slha tarballs 
    :returns: slha file name
    """
    valfile = getValidationDataPathName ( args["dbpath"], args["analysisname"], 
                            args["validationfile" ], "validationSpey"  )
    module = getValidationModuleFromPath ( valfile, args["analysisname"] )
    ctSlhaFiles = 0
    slhafile, oUL, eUL, signalxsec = None, None, None, None
    for pt in module.validationData:
        if not "axes" in pt:
            continue
        axes = pt["axes"]
        isIn = True
        for coord,value in axes.items():
            if not coord in args:
                print ( f"error: need to specify {coord}" )
                sys.exit()
            dx = .5 * abs ( value - args[coord] ) / ( value + args[coord] )
            if dx > 1e-5:
                isIn = False
        if isIn:
            slhafile = pt["slhafile"]
            oUL = pt["UL"]
            eUL = pt["eUL"]
            signal = pt["signal"]
            # print ( f"we found {slhafile}" )
            ctSlhaFiles += 1
    if ctSlhaFiles > 1:
        print ( f"error we found too many matches for slhafiles" )
        sys.exit()
    if ctSlhaFiles == 0:
        print ( f"error we found no match for slhafile" )
        sys.exit()
    from validation.validationHelpers import retrieveValidationFile
    retrieveValidationFile ( slhafile )
    ulmu = oUL/signal
    ulmuexp = eUL/signal
    print ( "created", slhafile )
    print ( f"in {valfile}: oUL(mu)={ulmu:.4g} eUL(mu)={ulmuexp:.4f}" )
    return slhafile
    
def create ( args : Dict ):
    slhafile = createSLHAFile ( args )
    runSModelS ( args, slhafile )
    createSpeyCode()
    runSpeyCode()

def createParallel ( args : Dict ):
    """ run smodels in parallel, see if this changes anything """
    slhafile = createSLHAFile ( args )
    print ( "single process" )
    runSModelS ( args, slhafile )
    """
    print ( "multi process" )
    import multiprocessing
    nproc = 1
    pool = multiprocessing.Pool ( processes = nproc )
    children= []
    for i in range ( nproc ):
        p = pool.apply_async ( runSModelS, args = ( args, slhafile ) )
        children.append(p)
    pool.close()
    for c in children:
        p.get()
    """
    createSpeyCode()
    runSpeyCode()

def main():
    import argparse
    ap = argparse.ArgumentParser(description="create a specific point ready for jacks inspection" )
    defdbpath = f"{os.environ['HOME']}/git/smodels-database/validation.pcl"
    ap.add_argument('-d', '--dbpath',
            help=f'database path [{defdbpath}]]', default=None)
    defaultananame = "CMS-SUS-20-004-eff"
    ap.add_argument('-a', '--analysisname',
            help=f'analysis path [{defaultananame}]', default=None)
    defaultvalfile = "T5HH_2EqMassAx_EqMassBx-50_EqMassC1.0_combined.py"
    ap.add_argument('-v', '--validationfile',
            help=f'validation path [{defaultvalfile}]', default=None)
    ap.add_argument('-x', '--x',
            help='xvalue', default=2075., type=float )
    ap.add_argument('-y', '--y',
            help='yvalue', default=None, type=float )
    args = ap.parse_args()
    if args.dbpath == None:
        args.dbpath = defdbpath
    if args.validationfile == None:
        args.validationfile=defaultvalfile
    if args.analysisname == None:
        args.analysisname = defaultananame

    create ( vars(args) )

if __name__ == "__main__":
    main()
