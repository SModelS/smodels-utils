#!/usr/bin/env python3

""" create a spey point, ready for jacks inspection """
import numpy
print ( "numpy", numpy.__version__ )
import scipy
print ( "scipy", scipy.__version__ )
from colorama import Fore


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
    if npredictions!=1:
        print ( f"{Fore.RED}{npredictions} predictions!{Fore.RESET}" )
    else:
        print ( f"{Fore.GREEN}prediction: oUL(mu)={predictions[0].getUpperLimitOnMu():.4g} eUL(mu)={predictions[0].getUpperLimitOnMu(expected=True):.4g}{Fore.RESET}" )

def runSpeyCode():
    cmd = f"./{speyfilename}"
    o = subprocess.getoutput ( cmd )
    print ( o )

def createSpeyCode( args, slhafile ):
    f=open(speyfilename,"wt")
    f.write( "#!/usr/bin/env python3\n\n" )
    f.write( f"# validationfile: {args['validationfile']}\n" )
    f.write( f"# slhafile: {slhafile}\n" )
    f.write( f"# mother mass: {args['x']}\n" )
    f.write( f"# daughter mass: {args['y']}\n" )
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

def extractPoint ( valfile : str, args : Dict ) -> Dict:
    """ given the validation file and the arguments
    extract the relevant point """
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
    ret = { "slhafile": slhafile, "oUL": oUL, "eUL": eUL, "signal": signal }
    ret["oULmu"] = oUL/signal
    ret["eULmu"] = eUL/signal
    from validation.validationHelpers import retrieveValidationFile
    retrieveValidationFile ( slhafile )
    return ret

def createSLHAFile ( args : Dict ) -> str:
    """ create the SLHA file that we need, extract it from 
        validation slha tarballs 
    :returns: slha file name
    """
    valfile = getValidationDataPathName ( args["dbpath"], args["analysisname"], 
                            args["validationfile" ], "validationSpey"  )
    origvalfile = getValidationDataPathName ( args["dbpath"], args["analysisname"], 
                            args["validationfile" ], "validation"  )
    ret = extractPoint ( valfile, args )
    origret = extractPoint ( origvalfile, args )
    print ( "extracted", ret["slhafile"] )
    print ( f"in {Fore.GREEN}{valfile}: oUL(mu)={ret['oULmu']:.4g} eUL(mu)={ret['eULmu']:.4f}{Fore.RESET}" )
    print ( f"in {Fore.GREEN}{origvalfile}: oUL(mu)={origret['oULmu']:.4g} eUL(mu)={origret['eULmu']:.4f}{Fore.RESET}" )
    # print ( f"in {origvalfile}: oUL(mu)={ulmu:.4g} eUL(mu)={ulmuexp:.4f}" )
    return ret["slhafile"]
    
def create ( args : Dict ):
    slhafile = createSLHAFile ( args )
    runSModelS ( args, slhafile )
    createSpeyCode( args, slhafile )
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
    createSpeyCode( args, slhafile )
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
    ap.add_argument('-2', '--p2', help="second point", action="store_true" )
    args = ap.parse_args()
    if args.dbpath == None:
        args.dbpath = defdbpath
    if args.validationfile == None:
        args.validationfile=defaultvalfile
    if args.analysisname == None:
        args.analysisname = defaultananame
    if args.p2:
        args.validationfile="T2tt_2EqMassAx_EqMassBy_combined.py"
        args.analysisname = "CMS-SUS-16-050-eff"
        args.x = 980.
        args.y = 400.
        #args.x = 880.
        #args.y = 350.

    create ( vars(args) )

if __name__ == "__main__":
    main()
