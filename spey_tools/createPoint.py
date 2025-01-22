#!/usr/bin/env python3

""" create a spey point, ready for jacks inspection """

from typing import Dict
from smodels.statistics import speyTools
from smodels_utils.helper.various import getValidationDataPathName, getValidationModuleFromPath
import os, sys, shutil

def runSModelS( args : Dict, slhafile : os.PathLike ):
    print ( f"[createPoint] running SModelS" )
    from smodels.decomposition import decomposer
    from smodels.base.physicsUnits import fb, GeV, TeV
    from smodels.matching.theoryPrediction import theoryPredictionsFor, TheoryPredictionsCombiner
    from smodels.experiment.databaseObj import Database
    from smodels.tools.particlesLoader import load
    BSMList = load()
    from smodels.share.models.SMparticles import SMList
    from smodels.base.model import Model
    dbpath = args["dbpath"]
    db = Database ( dbpath )
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=slhafile)
    sigmacut = 0.005*fb
    mingap = 5*GeV
    toplist = decomposer.decompose( model, sigmacut, massCompress=True,
                                    invisibleCompress=True, minmassgap=mingap)
    anaids = [ args["analysisname"].replace("-eff","") ]
    listOfExpRes = db.getExpResults( analysisIDs = anaids )
    speyTools._debug["writePoint"]=True ## this makes sure data.txt is created!!!
    for expResult in listOfExpRes:
        predictions = theoryPredictionsFor(db, toplist, combinedResults=True )
    npredictions=len(predictions)
    print ( f"[createPoint] {npredictions} predictions" )

def createSpeyCode( args : Dict ):
    filename = "forjack.py"
    f=open(filename,"wt")
    f.write( "#!/usr/bin/env python3\n\n" )
    f.write ( f"## produced via: {' '.join(sys.argv)}\n" )
    f.write ( f"## args are: {args}\n" )
    with open ( "data.txt", "rt" ) as g:
        f.write ( g.read() )
    shutil.move ( "data.txt", "data.old" )
    f.write (
"""
import spey

stat_wrapper = spey.get_backend("default_pdf.correlated_background")
speyModel = stat_wrapper( data = obsN, background_yields = bg,
    covariance_matrix = cov, signal_yields = nsig,
    xsection = [ x / lumi for x in nsig ], analysis = analysis )

expected = False # spey.ExpectationType.apriori
ul = speyModel.poi_upper_limit( expected = expected )
print ( f"[forjack] ul={ul}" )

""" )
    f.close()
    os.chmod ( filename, 0o755 )

def createSLHAFile ( args : Dict ) -> str:
    """ create the SLHA file that we need, extract it from
        validation slha tarballs
    :returns: slha file name
    """
    valfile = getValidationDataPathName ( args["dbpath"], args["analysisname"],
                            args["validationfile" ], args["validationfolder"] )
    module = getValidationModuleFromPath ( valfile, args["analysisname"] )
    ctSlhaFiles = 0
    slhafile = None
    for pt in module.validationData:
        if not "axes" in pt:
            continue
        axes = pt["axes"]
        isIn = True
        for coord,value in axes.items():
            if not coord in args or args[coord]==None:
                print ( f"[createPoint] error: need to specify the '{coord}' coordinate" )
                sys.exit()
            dx = .5 * abs ( value - args[coord] ) / ( value + args[coord] )
            if dx > 1e-5:
                isIn = False
        if isIn:
            slhafile = pt["slhafile"]
            # print ( f"[createPoint] we found {slhafile}" )
            ctSlhaFiles += 1
    if ctSlhaFiles > 1:
        print ( f"[createPoint] error we found too many matches for slhafiles" )
        sys.exit()
    if ctSlhaFiles == 0:
        print ( f"[createPoint] error we found no match for {args[coord]} in {valfile}" )
        sys.exit()
    from validation.validationHelpers import retrieveValidationFile
    retrieveValidationFile ( slhafile )
    print ( f"[createPoint] created {slhafile} {os.path.exists('data.txt')}" )
    return slhafile

def create ( args : Dict ):
    """ create the spey code given <args> """
    slhafile = createSLHAFile ( args )
    runSModelS ( args, slhafile ) ## need to run it so data.txt is produced
    createSpeyCode( args )

def main():
    import argparse
    ap = argparse.ArgumentParser(description="create a specific input point ready for jacks inspection" )
    defaultdbpath = "~/git/smodels-database/" # validation.pcl"
    ap.add_argument('-d', '--dbpath',
            help=f'database path [{defaultdbpath}]', default=defaultdbpath)
    defaultananame = "CMS-SUS-21-008-eff"
    ap.add_argument('-a', '--analysisname',
            help=f'analysis path [{defaultananame}]', default=None)
    defaultvalfile = "TChiWH_2EqMassAx_EqMassBy_combined.py"
    ap.add_argument('-v', '--validationfile',
            help=f'validation path [{defaultvalfile}]', default=None)
    defaultvalfolder = "validationSpey"
    ap.add_argument('-f', '--validationfolder',
            help=f'validation path [{defaultvalfolder}]', default=defaultvalfolder)
    ap.add_argument('-x', '--x',
            help='x-value', default=2075., type=float )
    ap.add_argument('-y', '--y',
            help='y-value', default=None, type=float )
    args = ap.parse_args()
    args.dbpath = os.path.expanduser ( args.dbpath )
    if args.validationfile == None:
        args.validationfile=defaultvalfile
    if args.analysisname == None:
        args.analysisname = defaultananame

    create ( vars(args) )

if __name__ == "__main__":
    main()
