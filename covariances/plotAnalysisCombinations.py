#!/usr/bin/env python3

"""
.. module:: testAnalysisCombinations
   :synopsis: Testbed for llhd combinations, plots likelihods

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import sys,os,time
sys.path.insert(0, "../")
sys.path.insert(0, os.path.expanduser("~/smodels"))
from smodels.tools import modelTester
from testAnalysisCombinations import createLlhds
import numpy as np

import smodels_utils.plotting.mpkitty as plt
# import matplotlib.pyplot as plt

def getCombination(inputFile, parameterFile):

    from smodels.tools.physicsUnits import fb, GeV, TeV, pb
    from smodels.theory.model import Model
    from smodels.share.models.SMparticles import SMList
    from smodels.theory.theoryPrediction import theoryPredictionsFor
    from smodels.tools.theoryPredictionsCombiner import TheoryPredictionsCombiner
    from smodels.theory import decomposer



    parser = modelTester.getParameters(parameterFile)
    database, databaseVersion = modelTester.loadDatabase(parser,None)
    listOfExpRes = modelTester.loadDatabaseResults(parser, database)



    sigmacut = parser.getfloat("parameters", "sigmacut") * fb
    minmassgap = parser.getfloat("parameters", "minmassgap") * GeV
    from smodels.particlesLoader import BSMList
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    promptWidth = None
    stableWidth = None
    if parser.has_option("particles", "promptWidth"):
        promptWidth = parser.getfloat("particles", "promptWidth")*GeV
    if parser.has_option("particles", "stableWidth"):
        stableWidth = parser.getfloat("particles", "stableWidth")*GeV
    model.updateParticles(inputFile=inputFile,
                          promptWidth=promptWidth, stableWidth=stableWidth)

    """
    Decompose input model
    =====================
    """
    sigmacut = parser.getfloat("parameters", "sigmacut") * fb
    smstoplist = decomposer.decompose(model, sigmacut,
                                      doCompress=parser.getboolean(
                                          "options", "doCompress"),
                                      doInvisible=parser.getboolean(
                                          "options", "doInvisible"),
                                      minmassgap=minmassgap)

    """
    Compute theory prediparser = modelTester.getParameters(parameterFile)ctions
    ====================================================
    """

    """ Get theory prediction for each analysis and print basic output """
    allPredictions = []
    combineResults = False
    useBest = True
    combineResults = parser.getboolean("options", "combineSRs")
    expFeatures = parser.getboolean("options", "experimentalFeatures")
    from smodels.tools import runtime
    runtime._experimental = expFeatures

    for expResult in listOfExpRes:
        theorypredictions = theoryPredictionsFor(expResult, smstoplist,
                                                 useBestDataset=useBest, combinedResults=combineResults,
                                                 marginalize=False)
        if not theorypredictions:
            continue
        allPredictions += theorypredictions._theoryPredictions

    """Compute chi-square and likelihood"""
    if parser.getboolean("options", "computeStatistics"):
        for theoPred in allPredictions:
            theoPred.computeStatistics()

    combineAnas = parser.get("options", "combineAnas").replace(" ","").split(",")
    combiner = TheoryPredictionsCombiner.selectResultsFrom(allPredictions,
                                                               combineAnas)
    return combiner

def getLlhds(combiner,setup):

    muvals = np.linspace(setup['murange'][0],setup['murange'][1],setup['nmu'])
    expected = setup["expected"]
    normalize = setup["normalize"]

    llhds = {'combined' : np.ones(len(muvals))}
    tpreds = combiner.theoryPredictions
    for t in tpreds:
        Id = t.analysisId()
        t.computeStatistics( expected = expected )
        lsm = t.lsm()
        l = np.array([t.likelihood(mu,expected=expected) for mu in muvals])
        llhds['combined'] = llhds['combined']*l
        llhds[Id]=l

    if normalize:
        for Id,l in llhds.items():
            llhds[Id] = l/np.sum(l)

    return muvals,llhds

def getPlot(inputFile, parameterFile,options):
    outputFile = options["output"]

    combiner = getCombination(inputFile, parameterFile)
    parser = modelTester.getParameters(parameterFile)
    setup = {'expected' : False,'normalize' : False,
              'murange' : (options["mumin"],options["mumax"]), 'nmu' : 100}

    if parser.has_section("setup"):
        setup = parser.get_section("setup").toDict()
    muvals,llhdDict = getLlhds(combiner, setup)

    plotOptions = {'xlog' : False, 'ylog' : True, 'yrange' : None,
                    'figsize' : (10,7),'legend' : True}
    if parser.has_section("plotoptions"):
        plotOptions = parser.get_section("plotoptions").toDict()

    fig = plt.figure(figsize=plotOptions['figsize'])
    for anaID,l in llhdDict.items():
        plt.plot(muvals,l,label=anaID)

    plt.xlabel ( r"$\mu$" )

    if plotOptions['xlog']:
        plt.xscale('log')
    if plotOptions['ylog']:
        plt.yscale('log')
    if plotOptions['yrange']:
        plt.ylim(plotOptions['yrange'][0],plotOptions['yrange'][1])
    if plotOptions['legend']:
        plt.legend()

    plt.savefig(outputFile)
    return fig

def main():
    import argparse
    """ Makes a likelihood plot for  a combination of analyses. """
    ap = argparse.ArgumentParser( description=
            "Makes a simple likelihood plot for  a combination of analyses. For more options, try out the plotLikelihoods.ipynb notebook." )
    ap.add_argument('-f', '--filename',
            help='name of SLHA input file', required=True)
    ap.add_argument('-o', '--output',
            help='name of output plot [likelihoods.png]', 
            default = "likelihoods.png" )
    ap.add_argument('-p', '--parameterFile',
            help='name of parameter file, where most options are defined', 
            required=True)
    ap.add_argument('-m', '--mumin',
            help='minimum mu [-3.]', type=float,
            default = -3. )
    ap.add_argument('-M', '--mumax',
            help='maximum mu [5.]', type=float,
            default = 5. )

    args = ap.parse_args()
    t0 = time.time()

    options = { "mumin": args.mumin, "mumax": args.mumax,
                "output": args.output }
    fig = getPlot(args.filename, args.parameterFile, options)
    print('Done in %1.2f s' %(time.time()-t0))

if __name__ == "__main__":
    main()
