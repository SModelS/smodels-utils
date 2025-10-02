#!/usr/bin/env python3

"""
.. module:: testAnalysisCombinations
   :synopsis: Testbed for llhd combinations, plots likelihods

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import sys,os,timeit
sys.path.insert(0, "../")
sys.path.insert(0, os.path.expanduser("~/smodels"))
from smodels.matching import modelTester
from smodels.statistics.basicStats import observed, apriori, aposteriori
from testAnalysisCombinations import createLlhds
import numpy as np
import pyslha
import smodels_utils.plotting.mpkitty as plt
from typing import Tuple

def getCombination( inputFile : str , parameterFile : str ) -> Tuple:
    """ get the combination of analyses for inputFile, parameter.ini
    """

    from smodels.base.physicsUnits import fb, GeV, TeV, pb
    from smodels.base.model import Model
    from smodels.share.models.SMparticles import SMList
    from smodels.matching.theoryPrediction import theoryPredictionsFor, TheoryPredictionsCombiner
    from smodels.decomposition import decomposer
    from smodels.matching import theoryPrediction



    parser = modelTester.getParameters(parameterFile)
    database = modelTester.loadDatabase(parser,None)
    modelTester.loadDatabaseResults(parser, database)
    listOfExpRes = database.getExpResults()

    sigmacut = parser.getfloat("parameters", "sigmacut") * fb
    minmassgap = parser.getfloat("parameters", "minmassgap") * GeV
    from smodels.tools.particlesLoader import load
    from smodels.base import runtime
    runtime.modelFile = "smodels.share.models.mssm"
    BSMList = load()
    # from smodels.particlesLoader import BSMList
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
                                      massCompress=parser.getboolean(
                                          "options", "doCompress"),
                                      invisibleCompress=parser.getboolean(
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
#    expFeatures = parser.getboolean("options", "experimentalFeatures")
#    print ( "expFeatures", expFeatures )
#    from smodels.base import runtime
#    runtime._experimental = expFeatures
    allPredictions = theoryPredictionsFor(database, smstoplist,
                       useBestDataset=useBest, combinedResults=combineResults )

    """
    for pred in predictions:
    #for expResult in database.getExpResultList():
    #    theorypredictions = theoryPredictionsFor(expResult, smstoplist,
    #                                             useBestDataset=useBest, combinedResults=combineResults,
    #                                             )
        if not pred:
            continue
        allPredictions += pred # ._theoryPredictions
    """

    """Compute chi-square and likelihood"""
    if parser.getboolean("options", "computeStatistics"):
        for theoPred in allPredictions:
            theoPred.computeStatistics()


    """ Define theory predictions list that collects all theoryPrediction objects which satisfy max condition."""
    maxcond = parser.getfloat("parameters", "maxcond")
    theoryPredictions = theoryPrediction.TheoryPredictionList(allPredictions, maxcond)


    combineAnas = parser.get("options", "combineAnas").replace(" ","").split(",")
    combiner = TheoryPredictionsCombiner.selectResultsFrom(allPredictions,
                                                               combineAnas)
    return combiner,theoryPredictions

def getLlhds(combiner,setup):
    from math import isnan

    muvals = np.arange(setup['murange'][0],setup['murange'][1],setup['step_mu'])
    evaluationType = setup["evaluationType"]
    normalize = setup["normalize"]
    llhds = {'combined' : np.ones(len(muvals))}
    # llhds['combined_prev'] = np.ones(len(muvals))
    tpreds = combiner.theoryPredictions
    for t in tpreds:
        Id = t.analysisId()
        #t.computeStatistics( expected = expected )
        lsm = t.lsm()
        l = np.array([t.likelihood(mu,evaluationType=evaluationType,return_nll=False) for mu in muvals])
        # l_prev = np.array([t.likelihood(mu,expected=expected,useCached=False,previous=True) for mu in muvals])
        for i in range(len(muvals)):
            # If the fit did not converge, set the combined likelihood to nan
            if l[i] == None:
                llhds['combined'][i] = float("nan")
            else:
                llhds['combined'][i] = llhds['combined'][i]*l[i]
            # if l_prev[i] != None:
            #     llhds['combined_prev'][i] = llhds['combined_prev'][i]*l_prev[i]
            # else:
            #     llhds['combined_prev'][i] = 0
        llhds[Id]=l
        # llhds[Id+' prev']=l_prev

    # Replace the points that did not converge by None in the combined likelihood
    llhds['combined'] = np.array([llCombined if llCombined != 1 else None for llCombined in llhds['combined'].tolist()])
    # llhds['combined_prev'] = np.array([llCombined_prev if llCombined_prev!=1 and llCombined_prev!=0 else None for llCombined_prev in llhds['combined_prev'].tolist()])
    if normalize:
        for Id,l in llhds.items():
            norm = 0
            # Compute the normalization factor
            for elem in l:
                if elem != None and not isnan(elem):
                    if elem > norm:
                        norm = elem
                    # norm += elem
            for i,elem in enumerate(l):
                if elem != None and not isnan(elem):
                    llhds[Id][i] = elem/norm


    return muvals,llhds

def getPlot( options : dict ) -> Tuple:
    """ plot the likelihood.

    :returns: tuple with matplotlib figure and output file name
    """
    inputFile = options["filename"]
    parameterFile = options["parameterFile"]
    from scipy.interpolate import interp1d
    outputFile = options["output"]

    combiner,tPredsList = getCombination(inputFile, parameterFile)
    parser = modelTester.getParameters(parameterFile)
    step_mu = (options["mumax"] - options["mumin"] ) / options["nsteps"]
    setup = {'evaluationType' : apriori ,'normalize' : True,
              'murange' : (options["mumin"],options["mumax"]), 'step_mu' : step_mu}

    if parser.has_section("setup"):
        setup = parser.get_section("setup").toDict()
    muvals,llhdDict = getLlhds(combiner, setup)

    plotOptions = {'xlog' : False, 'ylog' : False, 'yrange' : None,
                    'figsize' : (13,8),'legend' : True}
    if parser.has_section("plotoptions"):
        plotOptions = parser.get_section("plotoptions").toDict()

    tpDict = {}
    for ana in tPredsList:
        idDict = {}
        idDict['ulmu'] = ana.getUpperLimitOnMu( evaluationType = setup["evaluationType"])
        idDict['mu_obs'] = 1. / ana.getRValue( evaluationType = observed )
        idDict['mu_exp'] = 1. / ana.getRValue( evaluationType = apriori )
        tpDict[ana.dataset.globalInfo.id] = idDict
        tpDict


    muhat = combiner.muhat( evaluationType = setup["evaluationType"])
    nllmin = combiner.lmax( evaluationType = setup["evaluationType"], return_nll = True )
    nllsm = combiner.lsm( evaluationType = setup["evaluationType"], return_nll = True )
    nllbsm = combiner.likelihood(mu=1.0, evaluationType = setup["evaluationType"], return_nll = True )
    ymin = 0.

    fig = plt.figure(figsize=plotOptions['figsize'])
    for anaID,l in llhdDict.items():
        likelihoodInterp = interp1d(muvals,l)
        if anaID == 'combined_prev':
            zorder = 100
            linestyle = '-.'
            ulmu = combiner.getUpperLimitOnMu( evaluationType = setup["evaluationType"])
            ulmu_comb = ulmu
            # lbl=rf'$\mu^{{UL}}={ulmu:.2f}$'
            lbl = None
            #Draw vertical lines for muhat
            if setup['murange'][0] <= muhat <= setup['murange'][1]:
                plt.vlines(muhat,ymin=ymin,ymax=likelihoodInterp(muhat),linestyle='-.', label=r'$\hat{\mu}_{\mathrm{Comb}}$',color='black',alpha=0.7)
            x = plt.plot(muvals,l,label=anaID,zorder=zorder,linestyle=linestyle,linewidth=2)
        elif anaID == 'combined':
            zorder = 99
            linestyle = '--'
            ulmu = combiner.getUpperLimitOnMu( evaluationType= setup["evaluationType"])
            ulmu_comb = ulmu
            # lbl=rf'$\mu^{{UL}}={ulmu:.2f}$'
            lbl=None
            muobs = 1. / combiner.getRValue( evaluationType = observed )
            muexp = 1. / combiner.getRValue( evaluationType = apriori )
            #Draw vertical lines for muhat
            if muvals[0] <= muhat <= muvals[-1]:
                plt.vlines(muhat,ymin=ymin,ymax=likelihoodInterp(muhat),linestyle='-.', label=r'$\hat{\mu}_{\mathrm{Comb}}$',color='black',alpha=0.7)
            x = plt.plot(muvals,l,label=f"combined\n{'$\\mu^{ul}_{obs} = $ %1.2f, $\\mu^{ul}_{exp} = $ %1.2f' % (muobs, muexp)}",zorder=zorder,linestyle=linestyle,linewidth=2,color="black")
        else:
            if 'prev' in anaID:
                linestyle = ':'
                zorder = 98
                x = plt.plot(muvals,l,label=anaID,zorder=zorder,linestyle=linestyle,linewidth=2)
            else:
                linestyle = '-'
                zorder = None
                ulmu = tpDict[anaID]['ulmu']
                muobs = tpDict[anaID]['mu_obs']
                muexp = tpDict[anaID]['mu_exp']
                x = plt.plot(muvals,l,label=f"{anaID}\n{'$\\mu^{ul}_{obs} = $ %1.2f, $\\mu^{ul}_{exp} = $ %1.2f' % (muobs, muexp)}",zorder=zorder,linestyle=linestyle,linewidth=2)
            lbl=None

        #Draw vertical lines for ulmu
        if muvals[0] <= ulmu <= muvals[-1]:
            plt.vlines(ulmu,ymin=ymin,ymax=likelihoodInterp(ulmu),linestyle='dotted',color=x[-1].get_color(),label=lbl,alpha=0.7)

    plt.xlabel( r"Signal Strength $\mu$", fontsize=18)
    if setup["evaluationType"] == aposteriori:
        ylab = 'post-fit expected '
        shortExpType = 'apost'
    elif setup["evaluationType"] == apriori:
        ylab = 'pre-fit expected '
        shortExpType = 'exp'
    else:
        ylab = 'observed '
        shortExpType = 'obs'
    if setup["normalize"]:
        ylab = f"{ylab}normalized likelihood"
        plt.ylabel(ylab, fontsize=18)
    else:
        ylab = f"{ylab}likelihood"
        plt.ylabel(ylab, fontsize=18)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)


    endFileName = parser.get("database", "dataselector")
    if endFileName == 'all':
        endFileName = 'UL+EM'
    if parser.has_option("options", "combineSRs"):
        if parser.getboolean("options", "combineSRs"):
            endFileName = 'combined'
            CSR = True

    outputFile = outputFile.replace('.png',f"_{endFileName}_{shortExpType}.png")
    data = pyslha.read(inputFile)
    m1 = data.blocks['EXTPAR'][1]
    m2 = data.blocks['EXTPAR'][2]
    mu = data.blocks['EXTPAR'][23]
    smuhat = f"{muhat:1.2f}"
    if muhat == 0:
        smuhat = 0

    plt.title( rf'$M_1$ = {m1:.2f} GeV, $M_2$ = {m2:.2f} GeV, $\mu$ = {mu:.2f} GeV,' + f' combined SR = {CSR}'+ '\n' +
              r'$\hat{\mu}_{\mathrm{Comb}} = $ %s, $\mu^\mathrm{UL}_{comb} = $ %1.2f, $\mathrm{nll_{BSM}} =$ %1.1f, $\mathrm{nll_{min}} =$ %1.1f, $\mathrm{nll_{SM}} =$ %1.1f' %(smuhat,ulmu_comb,nllbsm,nllmin,nllsm),fontsize=20)

    if plotOptions['xlog']:
        plt.xscale('log')
    if plotOptions['ylog']:
        plt.yscale('log')
    if plotOptions['yrange']:
        plt.ylim(plotOptions['yrange'][0],plotOptions['yrange'][1])
    if plotOptions['legend']:
        plt.legend(fontsize=14)

    plt.savefig(outputFile)
    return fig, outputFile

def main():
    import argparse
    """ Makes a likelihood plot for  a combination of analyses. """
    ap = argparse.ArgumentParser( description=
            "Makes a simple likelihood plot for  a combination of analyses. For more options, try out the plotLikelihoods.ipynb notebook." )
    ap.add_argument('-f', '--filename',
            help='name of SLHA input file', required=True);
    ap.add_argument('-o', '--output',
            help='name of output plot [likelihoods.png]',
            default = 'Likelihoods.png' )
    ap.add_argument('-p', '--parameterFile',
            help='name of parameter file, where most options are defined',
            required=True)
    ap.add_argument('-m', '--mumin',
            help='minimum mu [-3.]', type=float,
            default = -3. )
    ap.add_argument('-n', '--nsteps',
            help='number of steps [100]', type=int,
            default = 100 )
    ap.add_argument('-M', '--mumax',
            help='maximum mu [5.]', type=float,
            default = 5. )
    ap.add_argument('-s', '--show', help='show final plot',
            action = "store_true" )

    args = ap.parse_args()

    if args.output == 'Likelihoods.png':
        args.output = os.path.basename(args.filename).replace('.slha','_llhds.png')

    options = vars(args)

    t0 = timeit.default_timer()
    fig, outputFile = getPlot(options)
    print(f'[plotAnalysisCombinations] plotted {args.filename} in {timeit.default_timer() - t0:1.2f} s')
    if args.show:
        from smodels_utils.plotting.mpkitty import timg
        timg ( outputFile )

if __name__ == "__main__":
    main()
