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
from smodels.statistics.basicStats import observed, apriori, \
         aposteriori, NllEvalType
from testAnalysisCombinations import createLlhds
import numpy as np
import pyslha
import smodels_utils.plotting.mpkitty as plt
from typing import Tuple
from math import isnan

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

    # Decompose input model
    sigmacut = parser.getfloat("parameters", "sigmacut") * fb
    smstoplist = decomposer.decompose(model, sigmacut,
                                      massCompress=parser.getboolean(
                                          "options", "doCompress"),
                                      invisibleCompress=parser.getboolean(
                                          "options", "doInvisible"),
                                      minmassgap=minmassgap)

    combineAnas = parser.get("options", "combineAnas").replace(" ","").split(",")
    def removeDS ( dsName : str ):
        if not ":" in dsName:
            return dsName
        return dsName[:dsName.find(":")]
    anasOnly = [ removeDS ( x ) for x in combineAnas ]
    withDSes = {}
    for x in combineAnas:
        if not ":" in x:
            continue
        p1 = x.find(":")
        anaId, dsId = x[:p1], x[p1+1:]
        if not anaId in withDSes:
            withDSes[anaId]=[]
        withDSes[anaId].append ( dsId )
    # Compute theory prediparser = modelTester.getParameters(parameterFile)ctions
    # Get theory prediction for each analysis and print basic output
    combineResults = False
    useBest = False
    combineResults = parser.getboolean("options", "combineSRs")
    allPredictions = theoryPredictionsFor(database, smstoplist,
                       useBestDataset=useBest, combinedResults=combineResults )
    filteredPredictions = []
    for tp in allPredictions:
        anaId = tp.dataset.globalInfo.id
        if not anaId in anasOnly:
            continue
        dsId = None
        if tp.dataType() != "combined":
            dsId = tp.dataset.dataInfo.dataId
        if anaId in withDSes:
            if not dsId in withDSes[anaId]:
                continue
        filteredPredictions.append ( tp )

    # Compute chi-square and likelihood
    if parser.getboolean("options", "computeStatistics"):
        for theoPred in filteredPredictions:
            theoPred.computeStatistics()


    # Define theory predictions list that collects all theoryPrediction objects 
    # which satisfy max condition.
    maxcond = parser.getfloat("parameters", "maxcond")
    theoryPredictions = theoryPrediction.TheoryPredictionList(\
            filteredPredictions, maxcond )

    combiner = TheoryPredictionsCombiner.selectResultsFrom(filteredPredictions,
                                                           anasOnly)
    return combiner,theoryPredictions

def normalizeLikelihoods ( llhds: dict, normalize : str ):
    """ normalize the likelihoods in llhds according to normalize 
    :param normalize: either max, or area
    """
    if normalize == "max":
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
    if normalize == "area":
        for Id,l in llhds.items():
            norm = 0
            # Compute the normalization factor
            for elem in l:
                if elem != None and not isnan(elem):
                    norm += elem
            for i,elem in enumerate(l):
                if elem != None and not isnan(elem):
                    if elem == 0.:
                        llhds[Id][i] = 0.
                    else:
                        llhds[Id][i] = elem/norm
    return llhds

def getLlhds(combiner,setup):
    if "murange" in setup:
        setup["mumin"]=setup["murange"][0]
        setup["mumax"]=setup["murange"][1]
        setup["nsteps"]=setup["murange"][2]
    if not "evaluationtype" in setup:
        setup["evaluationtype"]="observed"

    step_mu = ( setup["mumax"]-setup["mumin"] )/ setup["nsteps"]
    muvals = np.arange(setup['mumin'],setup['mumax'],step_mu)
    evaluationType = setup["evaluationtype"]
    normalize = setup["normalize"]
    llhds = {'combined' : np.zeros(len(muvals))}
    # llhds['combined_prev'] = np.ones(len(muvals))
    tpreds = combiner.theoryPredictions
    for t in tpreds:
        Id = t.analysisId()
        if t.dataType() != "combined":
            Id += ":" + t.dataset.dataInfo.dataId
        #t.computeStatistics( expected = expected )
        lsm = t.lsm()
        l = np.array([t.nll(mu,evaluationType=evaluationType) for mu in muvals])
        for i in range(len(muvals)):
            # If the fit did not converge, set the combined likelihood to nan
            if l[i] == None:
                llhds['combined'][i] = float("nan")
            else:
                llhds['combined'][i] = llhds['combined'][i]+l[i]
        llhds[Id]=l

    # Replace the points that did not converge by None in the combined likelihood
    llhds['combined'] = np.array([llCombined if llCombined != 1 else None for \
                                  llCombined in llhds['combined'].tolist()])

    ## we switch from nlls to likelihoods here
    for anaId,llhd in llhds.items():
        llhds[anaId] = np.exp ( - llhd )

    llhds = normalizeLikelihoods ( llhds, normalize )

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
    # step_mu = (mumax - mumin ) / nsteps
    setup = {'evaluationtype' : apriori ,'normalize' : "none",
             'mumin': -5, 'mumax': 5, 'nsteps': 20, 'title' : None,
             'ulinlegend': True }

    if not "setup" in parser:
        print ( f"[plotAnalysisCombinations] you do not have a 'setup' section in {parameterFile}. will fall back to defaults" )
    else:
    # if parser.has_section("setup"):
        # setup = parser.get_section("setup").toDict()
        for k,v in parser["setup"].items():
            k = k.lower()
            if not k in setup:
                print ( f"[plotAnalysisCombinations] do not know of entry {k} in setup" )
                sys.exit(-1)
            if k == "evaluationType":
                v= NllEvalType ( v )
            elif k in [ "mumin", "mumax" ]:
                v = float ( v )
            elif k in [ "nsteps" ]:
                v = int ( v )
            elif k in [ "ulinlegend" ]:
                if v.lower() in [ "false", "0", "no" ]:
                    v = False
                else:
                    v = True
            elif k == "normalize":
                if v not in [ "none", "max", "area" ]:
                    print ( f"[plotAnalysisCombinations] v has to be one of: none, max, area" )
                    sys.exit()
            setup[k]=v
                
        # setup.update ( dict ( parser["setup"] ) )
    muvals,llhdDict = getLlhds(combiner, setup)

    plotOptions = {'xlog' : False, 'ylog' : False, 'yrange' : None,
                    'figsize' : (13,8),'legend' : True}
    if "plotoptions" in parser:
    # if parser.has_section("plotoptions"):
        # plotOptions = parser.get_section("plotoptions").toDict()
        plotOptions = dict ( parser["plotoptions"] )

    tpDict = {}
    for ana in tPredsList:
        idDict = {}
        idDict['ulmu'] = ana.getUpperLimitOnMu( evaluationType = setup["evaluationtype"])
        idDict['mu_obs'] = 1. / ana.getRValue( evaluationType = observed )
        rexp = ana.getRValue( evaluationType = apriori )
        idDict['mu_exp'] = float("nan") if rexp is None else  1. / rexp
        Id = ana.dataset.globalInfo.id
        if ana.dataType() != "combined" and ana.dataType() != "upperLimit":
            # print ( f"@@X Id {Id} dataId {ana.dataset.dataInfo.dataId} dt {ana.dataType()}" )
            Id += ":" + ana.dataset.dataInfo.dataId
        tpDict[Id] = idDict
        tpDict


    evType = setup["evaluationtype"]
    muhat = combiner.muhat( evaluationType = evType )
    nllmin = combiner.lmax( evaluationType = evType, return_nll = True )
    nllsm = combiner.lsm( evaluationType = evType, return_nll = True )
    nllbsm = combiner.likelihood(mu=1.0, evaluationType = evType, return_nll = True )
    ymin = 0.

    fig = plt.figure(figsize=plotOptions['figsize'])
    for anaID,l in llhdDict.items():
        likelihoodInterp = interp1d(muvals,l)
        if anaID == 'combined_prev':
            zorder = 100
            linestyle = '-.'
            ulmu = combiner.getUpperLimitOnMu( evaluationType = evType )
            ulmu_comb = ulmu
            # lbl=rf'$\mu^{{UL}}={ulmu:.2f}$'
            lbl = None
            #Draw vertical lines for muhat
            if setup['murange'][0] <= muhat <= setup['murange'][1]:
                plt.vlines(muhat,ymin=ymin,ymax=likelihoodInterp(muhat),
                           linestyle='-.', label=r'$\hat{\mu}_{\mathrm{Comb}}$',
                           color='black',alpha=0.7)
            x = plt.plot(muvals,l,label=anaID,zorder=zorder,linestyle=linestyle,
                         linewidth=2 )
        elif anaID == 'combined':
            zorder = 99
            linestyle = '-'
            ulmu = combiner.getUpperLimitOnMu( evaluationType= evType)
            ulmu_comb = ulmu
            # lbl=rf'$\mu^{{UL}}={ulmu:.2f}$'
            lbl=None
            muobs = 1. / combiner.getRValue( evaluationType = observed )
            muexp = 1. / combiner.getRValue( evaluationType = apriori )
            #Draw vertical lines for muhat
            if muvals[0] <= muhat <= muvals[-1]:
                plt.vlines(muhat,ymin=ymin,ymax=likelihoodInterp(muhat),
                           linestyle='-.', label=r'$\hat{\mu}_{\mathrm{Comb}}$',
                           color='black',alpha=0.7)
            label = "combined"
            if setup["ulinlegend"]==True:
                label = f"combined\n{'$\\mu^{ul}_{obs} = $ %1.2f, $\\mu^{ul}_{exp} = $ %1.2f' % (muobs, muexp)}"
            x = plt.plot( muvals,l,label=label,zorder=zorder,
                          linestyle=linestyle,linewidth=2,color="black" )
        else:
            if 'prev' in anaID:
                linestyle = ':'
                zorder = 98
                x = plt.plot( muvals,l,label=anaID,zorder=zorder,
                              linestyle=linestyle, linewidth=2 )
            else:
                linestyle = '-'
                """
                if "CMS" in anaID:
                    linestyle = "dashdot"
                if "ATLAS" in anaID:
                    linestyle = "dotted"
                """
                zorder = None
                ulmu = tpDict[anaID]['ulmu']
                muobs = tpDict[anaID]['mu_obs']
                muexp = tpDict[anaID]['mu_exp']
                label = anaID
                if setup["ulinlegend"]==True:
                    label = f"{anaID}\n{'$\\mu^{ul}_{obs} = $ %1.2f, $\\mu^{ul}_{exp} = $ %1.2f' % (muobs, muexp)}"
                x = plt.plot( muvals,l,label=label,zorder=zorder,
                              linestyle=linestyle,linewidth=3 )
            lbl=None

        #Draw vertical lines for ulmu
        if ulmu is not None and muvals[0] <= ulmu <= muvals[-1]:
            plt.vlines(ulmu,ymin=ymin,ymax=likelihoodInterp(ulmu),
                       linestyle='dotted',color=x[-1].get_color(),label=lbl,
                       alpha=0.7)

    plt.xlabel( r"Signal Strength $\mu$", fontsize=18)
    print ( f"[plotAnalysisCombinations] we plot with" )
    for k,v in setup.items():
        print ( f"      {k}={v}" )
    if setup["evaluationtype"] == aposteriori:
        ylab = 'post-fit expected '
        shortExpType = 'apost'
    elif setup["evaluationtype"] == apriori:
        ylab = 'pre-fit expected '
        shortExpType = 'exp'
    else:
        ylab = 'observed '
        shortExpType = 'obs'
    if setup["normalize"]=="area":
        ylab = f"{ylab}normalized"
        plt.ylabel(ylab, fontsize=18)
    elif setup["normalize"]=="max":
        ylab = rf"{ylab}normalized to l($\hat\mu$)=1"
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

    title = setup["title"]
    if title == None:
        title = rf'$M_1$ = {m1:.2f} GeV, $M_2$ = {m2:.2f} GeV, $\mu$ = {mu:.2f} GeV,' + f' combined SR = {CSR}\n'
        title += r'$\hat{\mu}_{\mathrm{Comb}} = $ %s, $\mu^\mathrm{UL}_{comb} = $ %1.2f, $\mathrm{nll_{BSM}} =$ %1.1f, $\mathrm{nll_{min}} =$ %1.1f, $\mathrm{nll_{SM}} =$ %1.1f' %(smuhat,ulmu_comb,nllbsm,nllmin,nllsm)

    plt.title( title, fontsize = 20 ) 

    if plotOptions['xlog']:
        plt.xscale('log')
    if plotOptions['ylog']:
        plt.yscale('log')
    if plotOptions['yrange']:
        plt.ylim(plotOptions['yrange'][0],plotOptions['yrange'][1])
    if plotOptions['legend']:
        plt.legend(fontsize=14)

    from smodels_utils.helper.various import pngMetaInfo
    metadata = pngMetaInfo()
    plt.savefig(outputFile, metadata = metadata )
    return fig, outputFile

def main():
    import argparse
    """ Makes a 1d likelihood plot for a combination of analyses. """
    ap = argparse.ArgumentParser( description=
            "Makes a simple likelihood plot for  a combination of analyses. For more options, try out the plotLikelihoods.ipynb notebook." )
    ap.add_argument('-f', '--filename',
            help='name of SLHA input file', required=True);
    ap.add_argument('-o', '--output',
            help='name of output plot [likelihoods.png]',
            default = 'Likelihoods.png' )
    ap.add_argument('-p', '--parameterFile',
            help='name of parameter file, where most options are defined. this is a normal smodels ini file, but do make sure that combineAnas is defined. also an extra [setup] section may be defined see pac.ini in this folder',
            default="pac.ini" )
            #required=True)
    ap.add_argument('-s', '--show', help='show final plot',
            action = "store_true" )

    args = ap.parse_args()

    if args.output == 'Likelihoods.png':
        args.output = os.path.basename(args.filename).replace('.slha','_llhds.png')

    options = vars(args)

    t0 = timeit.default_timer()
    fig, outputFile = getPlot(options)
    print(f'[plotAnalysisCombinations] plotted {args.filename} to {outputFile} in {timeit.default_timer() - t0:1.2f} s')
    if args.show:
        from smodels_utils.plotting.mpkitty import timg
        timg ( outputFile )

if __name__ == "__main__":
    main()
