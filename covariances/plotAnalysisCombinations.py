#!/usr/bin/env python3

"""
.. module:: testAnalysisCombinations
   :synopsis: Testbed for llhd combinations, plots likelihods

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import sys,os,timeit
sys.path.insert(0, "../")
sys.path.insert(0, os.path.expanduser("~/smodels"))
from smodels.tools import modelTester
from testAnalysisCombinations import createLlhds
import numpy as np
import pyslha
import smodels_utils.plotting.mpkitty as plt
from labellines import *
import seaborn as sns


def getCombination(inputFile, parameterFile):

    from smodels.tools.physicsUnits import fb, GeV, TeV, pb
    from smodels.theory.model import Model
    from smodels.share.models.SMparticles import SMList
    from smodels.theory.theoryPrediction import theoryPredictionsFor, TheoryPredictionsCombiner
    from smodels.theory import decomposer
    from smodels.theory import theoryPrediction



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
                                                 #marginalize=False
                                                 )
        if not theorypredictions:
            continue
        allPredictions += theorypredictions._theoryPredictions

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
    expected = setup["expected"]
    normalise = setup["normalise"]
    llhds = {'combined' : np.ones(len(muvals))}
    # llhds['combined_prev'] = np.ones(len(muvals))
    tpreds = combiner.theoryPredictions
    for t in tpreds:
        Id = t.analysisId()
        #t.computeStatistics( expected = expected )
        lsm = t.lsm()
        l = np.array([t.likelihood(mu,expected=expected,return_nll=False) for mu in muvals])
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
    if normalise:
        for Id,l in llhds.items():
            norm = 0
            # Compute the normalization factor
            for elem in l:
                if elem != None and not isnan(elem):
                    # if elem > norm:
                    #     norm = elem
                    norm += elem*setup['step_mu']
            for i,elem in enumerate(l):
                if elem != None and not isnan(elem):
                    llhds[Id][i] = elem/norm


    return muvals,llhds

def getPlot(inputFile,parameterFile,options):
    from scipy.interpolate import interp1d
    outputFile = options["output"]

    combiner,tPredsList = getCombination(inputFile, parameterFile)
    parser = modelTester.getParameters(parameterFile)
    step_mu = .1
    step_mu = 0.05 #(options["mumax"] - options["mumin"] ) / 100.
    setup = {'expected' : False, 'normalise' : True,
              'murange' : (options["mumin"],options["mumax"]), 'step_mu' : step_mu}

    if parser.has_section("setup"):
        setup = parser.get_section("setup").toDict()
    muvals,llhdDict = getLlhds(combiner, setup)

    plotOptions = {'xlog' : False, 'ylog' : False, 'yrange' : None,
                    'figsize' : (11.5,7),'legend' : True}
    if parser.has_section("plotoptions"):
        plotOptions = parser.get_section("plotoptions").toDict()

    tpDict = {}
    for ana in tPredsList:
        idDict = {}
        idDict['ulmu'] = ana.getUpperLimitOnMu(expected = setup["expected"])
        idDict['ulmu_obs'] = ana.getUpperLimitOnMu(expected = False)
        idDict['ulmu_exp'] = ana.getUpperLimitOnMu(expected = True)
        idDict['r_obs'] = ana.getRValue(expected = False)
        idDict['r_exp'] = ana.getRValue(expected = True)
        tpDict[ana.dataset.globalInfo.id] = idDict

    r_exps = [(tpDict[ana]['r_exp'], ana) for ana in tpDict]
    r_exps.sort(reverse=True)
    llhdDict_ordered = {'combined': llhdDict['combined']}
    print("mu values:",muvals)
    print("Combined likelihood:",llhdDict['combined'])
    for r_exp,ana in r_exps:
        llhdDict_ordered[ana] = llhdDict[ana]

    colors = sns.color_palette("tab10")
    colorsB = sns.color_palette("Paired",12)
    colorsC = sns.color_palette("colorblind",9)
    colorDict = {'ATLAS-SUSY-2018-41' : 'indianred',
                 'ATLAS-SUSY-2019-08' : colors[2],
                 'ATLAS-SUSY-2019-09' : '#ff7f0e',
                 'ATLAS-SUSY-2018-05-ewk' : colors[4],
                 'ATLAS-SUSY-2018-32' : colors[8],
                 'ATLAS-SUSY-2017-03' : 'darkslategrey',
                 'ATLAS-SUSY-2013-11' : colorsB[2],
                 'ATLAS-SUSY-2013-12' : colorsB[8],
                 'ATLAS-SUSY-2019-02' : colors[9],
                 'ATLAS-SUSY-2018-06' : colors[1],
                 'ATLAS-SUSY-2016-24' : 'gold',
                 'CMS-SUS-16-039-agg' : colorsB[4],
                 'CMS-SUS-21-002' : colorsB[1],
                 'CMS-SUS-16-048' : 'darkred',
                 'CMS-SUS-20-004' : colorsB[10],
                 'CMS-SUS-13-012' : colors[6]
                 }

    # muhat = combiner.muhat(expected = setup["expected"])
    # lmax = combiner.lmax(expected = setup["expected"])
    # lsm = combiner.lsm(expected = setup["expected"])
    # lbsm = combiner.likelihood(mu=1.0,expected = setup["expected"])
    ymin = 0.
    i = 1

    fig = plt.figure(figsize=plotOptions['figsize'])
    for anaID,l in llhdDict_ordered.items():
        likelihoodInterp = interp1d(muvals,l)
        if anaID == 'combined_prev':
            zorder = 100
            linestyle = '-.'
            lbl=r'$\mu_{UL}$'
            ulmu = combiner.getUpperLimitOnMu(expected = setup["expected"])
            ulmu_comb = ulmu
            #Draw vertical lines for muhat
            if setup['murange'][0] <= muhat <= setup['murange'][1]:
                plt.vlines(muhat,ymin=ymin,ymax=likelihoodInterp(muhat),linestyle='-.', label=r'$\hat{\mu}_{\mathrm{Comb}}$',color='black',alpha=0.7)
            x = plt.plot(muvals,l,label=anaID,zorder=zorder,linestyle=linestyle,linewidth=2)
        elif anaID == 'combined':
            zorder = 99
            linestyle = '--'
            lbl=r'$\mu_{UL}$'
            ulmu_comb = combiner.getUpperLimitOnMu(expected = setup["expected"])
            ulmu = ulmu_comb
            ulmu_obs = combiner.getUpperLimitOnMu(expected = False)
            ulmu_exp = combiner.getUpperLimitOnMu(expected = True)
            robs = combiner.getRValue(expected = False)
            rexp = combiner.getRValue(expected = True)
            # x = plt.plot(muvals,l,label=anaID + '\n' + r'$r_{obs} = $ %1.2f, $r_{exp} = $ %1.2f' %(robs,rexp),zorder=zorder,linestyle=linestyle,linewidth=2)
            x = plt.plot(muvals,l,label=anaID + '\n' + r'$r_{\rm obs} = $ %1.2f, $r_{\rm exp} = $ %1.2f' %(robs,rexp),zorder=zorder,linestyle=linestyle,linewidth=3,color='black')
            #Draw vertical lines for muhat
            # if muvals[0] <= muhat <= muvals[-1]:
            #     plt.vlines(muhat,ymin=ymin,ymax=likelihoodInterp(muhat),linestyle='-.', label=r'$\hat{\mu}_{\mathrm{Comb}}$'+f' = {round(muhat,3)}',color='black',alpha=0.7)
        else:
            if 'prev' in anaID:
                linestyle = ':'
                zorder = 98
                x = plt.plot(muvals,l,label=anaID,zorder=zorder,linestyle=linestyle,linewidth=2)
            else:
                linestyle = '-'
                zorder = None
                i += 1
                ulmu = tpDict[anaID]['ulmu']
                ulmu_obs = tpDict[anaID]['ulmu_obs']
                ulmu_exp = tpDict[anaID]['ulmu_exp']
                robs = tpDict[anaID]['r_obs']
                rexp = tpDict[anaID]['r_exp']
                # x = plt.plot(muvals,l,label=anaID + '\n' + r'$r_{obs} = $ %1.2f, $r_{exp} = $ %1.2f' %(robs,rexp),zorder=zorder,linestyle=linestyle,linewidth=2)
                x = plt.plot(muvals,l,label=anaID.replace('-ewk','').replace('-agg','') + '\n' + r'$r_{\rm obs} = $ %1.2f, $r_{\rm exp} = $ %1.2f' %(robs,rexp),zorder=zorder,linestyle=linestyle,linewidth=3,color=colorDict[anaID])
            lbl=None

        #Draw vertical lines for ulmu
        if muvals[0] <= ulmu <= muvals[-1]:
            xulmu = ulmu
            if i == 1:
                offset = 0.3
            elif i == 2:
                offset = 0.2
            elif i == 3:
                offset = 0.2
            elif i == 4:
                offset = 0.2
            elif i == 5:
                offset = 0.2
            elif i == 6:
                offset = 0.2
            elif i == 8:
                offset = 0.2
            else:
                offset = 0.2

            # plt.vlines(ulmu,ymin=ymin,ymax=likelihoodInterp(ulmu),linestyle='dotted',color=x[-1].get_color(),label=None)
            plt.vlines(ulmu,ymin=ymin,ymax=likelihoodInterp(ulmu)+offset,linestyle='dotted',color=x[-1].get_color(),label=None,alpha=1,linewidth=2)
            lines = plt.gca().get_lines()
            l1=lines[-1]
            # i#    xulmu = ulmu - 0.2
            labelLine(l1,xulmu,yoffset=offset,label=r"$\mu_{UL}$="+"{:.2f}".format(ulmu).format(l1.get_label()),ha='left',va='bottom',align=False,fontsize=16.96,backgroundcolor="white")

    plt.xlabel( r"signal strength $\mu$", fontsize=16.96)
    if setup["expected"] == "posteriori":
        expType = 'Post-fit expected '
        shortExpType = 'apost'
    elif setup["expected"]:
        # expType = 'pre-fit expected '
        expType = 'Expected'
        shortExpType = 'exp'
    else:
        expType = 'Observed'
        shortExpType = 'obs'
    if setup["normalise"]:
        ylab = 'normalised likelihood'
        plt.ylabel(ylab, fontsize=16.96)
    else:
        ylab = 'likelihood'
        plt.ylabel(ylab, fontsize=16.96)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)


    endFileName = parser.get("database", "dataselector")
    if endFileName == 'all':
        endFileName = 'UL+EM'
    CSR = False
    if parser.has_option("options", "combineSRs"):
        if parser.getboolean("options", "combineSRs"):
            endFileName = 'combined'
            CSR = True

    outputFile = outputFile.replace('.png','_'+endFileName+'_'+shortExpType+'.png')
    data = pyslha.read(inputFile)
    M1 = data.blocks['EXTPAR'][1]
    M2 = data.blocks['EXTPAR'][2]
    Mu = data.blocks['EXTPAR'][23]
    tanB = data.blocks['EXTPAR'][25]

    mN1 = abs(data.blocks['MASS'][1000022])
    mN2 = abs(data.blocks['MASS'][1000023])
    mN3 = abs(data.blocks['MASS'][1000025])
    mN4 = abs(data.blocks['MASS'][1000035])
    mC1 = abs(data.blocks['MASS'][1000024])
    mC2 = abs(data.blocks['MASS'][1000037])


    # plt.title( rf'$M_1$ = {round(m1)} GeV, $\; M_2$ = {round(m2)} GeV, $\; \mu$ = {round(mu)} GeV' + f' combined SR = {CSR}'+ '\n' +
    #            r'$\hat{\mu}_{\mathrm{Comb}} = $ %1.2f, $\mu_{\mathrm{UL comb}} = $ %1.2f, $L_{BSM} =$ %1.2e, $L_{max} =$ %1.2e, $L_{SM} =$ %1.2e' %(muhat,ulmu_comb,lbsm,lmax,lsm)
    #           ,fontsize=20)

    plt.gcf().text(0.069,1.02,'SModelS v2.3',va='top',ha='left',fontsize=16.96)
    plt.gcf().text(0.668,1.02,os.path.basename(inputFile),va='top',ha='right',fontsize=16.96)

    plt.tick_params(which="major", length=5, direction="in", bottom=True, top=True, left=True, right=True)
    plt.tick_params(labelbottom=True, labelleft=True, labeltop=False, labelright=False)
    plt.grid(alpha=0.6)
    # plt.vlines(-1,ymin=-1,ymax=-0.5,linestyle='dotted',color='black',label=r'$\mu_{UL}$',linewidth=1.75)

    if plotOptions['xlog']:
        plt.xscale('log')
    if plotOptions['ylog']:
        plt.yscale('log')
    if plotOptions['yrange']:
        plt.ylim(plotOptions['yrange'][0],plotOptions['yrange'][1])
    if plotOptions['legend']:
        plt.legend(bbox_to_anchor=(1,1.023), loc="upper left", fontsize=16.96)

    plt.ylim(0)
    plt.xlim(options["mumin"],options["mumax"]-step_mu)

    # plt.gcf().text(0.997,0.475,rf'$M_1 \approx \!$ {round(M1)} GeV' + '\n'
    #                         + rf'$M_2 \approx \!$ {round(M2)} GeV' + '\n'
    #                         + rf'$\mu \approx \!$ {round(Mu)} GeV' + '\n'
    #                         + rf'$\tan \beta \approx \!$ {round(tanB)}' + '\n\n'
    #                         #+ rf'$m(\tilde\chi_4^0) \approx \!$ {round(mN4)} GeV' + '\n'
    #                         #+ rf'$m(\tilde\chi_2^\pm) \approx \!$ {round(mC2)} GeV' + '\n'
    #                         + rf'$m(\tilde\chi_3^0) \approx \!$ {round(mN3)} GeV' + '\n'
    #                         + rf'$m(\tilde\chi_2^0) \approx \!$ {round(mN2)} GeV' + '\n'
    #                         + rf'$m(\tilde\chi_1^\pm) \approx \!$ {round(mC1)} GeV' + '\n'
    #                         + rf'$m(\tilde\chi_1^0) \approx \!$ {round(mN1)} GeV' + '\n\n'
    #                         #+ r'$BR(\tilde\chi_4^0 \rightarrow h + \tilde\chi_1^0) \approx \!$ 0.26' + '\n'
    #                         #+ r'$BR(\tilde\chi_4^0 \rightarrow Z + \tilde\chi_1^0) \approx \!$ 0.16' + '\n'
    #                         #+ r'$BR(\tilde\chi_2^\pm \rightarrow W^\pm + \tilde\chi_1^0) \approx \!$ 0.39' + '\n'
    #                         # + r'$BR(\tilde\chi_2^\pm \rightarrow Z + \tilde\chi_1^\pm) \approx \!$ 0.26' + '\n'
    #                         # + r'$BR(\tilde\chi_2^\pm \rightarrow h + \tilde\chi_1^\pm) \approx \!$ 0.24' + '\n'
    #                         # + r'$BR(\tilde\chi_3^0 \rightarrow W^\mp + \tilde\chi_1^\pm) \approx \!$ 0.51' + '\n'
    #                         #+ r'$BR(\tilde\chi_3^0 \rightarrow h + \tilde\chi_1^0) \approx \!$ 0.16' + '\n'
    #                         + r'$BR(\tilde\chi_3^0 \rightarrow Z + \tilde\chi_1^0) \approx \!$ 0.76' + '\n'
    #                         #+ r'$BR(\tilde\chi_2^0 \rightarrow W^\mp + \tilde\chi_1^\pm) \approx \!$ 0.90'
    #                         + r'$BR(\tilde\chi_2^0 \rightarrow h + \tilde\chi_1^0) \approx \!$ 0.78'
    #                         #+ r'$BR(\tilde\chi_2^0 \rightarrow \ell \ell + \tilde\chi_1^0) \approx \!$ 0.07' + '\n'
    #                         #+ r"$BR(\tilde\chi_1^\pm \rightarrow q \bar q^' + \tilde\chi_1^0) \approx \!$ 0.67" + '\n'
    #                         #+ r"$BR(\tilde\chi_1^\pm \rightarrow \ell \nu_{\ell} + \tilde\chi_1^0) \approx \!$ 0.22" + '\n\n'
    #                         #+ r"$\ell \in \{e,\mu\}$"
    #                , fontsize=16.96)

    plt.gcf().text(0.52,0.9,expType,fontsize = 17, weight='bold')

    plt.tight_layout()
    plt.savefig(outputFile,bbox_inches='tight',dpi=750)
    return fig

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
    ap.add_argument('-M', '--mumax',
            help='maximum mu [5.]', type=float,
            default = 5. )

    args = ap.parse_args()
    t0 = timeit.default_timer()

    if args.output == 'Likelihoods.png':
        args.output = os.path.basename(args.filename).replace('.slha','_llhds.png')

    options = { "mumin": args.mumin, "mumax": args.mumax,
                "output": args.output }
    fig = getPlot(args.filename, args.parameterFile, options)
    print('Done in %1.2f s' %(timeit.default_timer()-t0))

if __name__ == "__main__":
    main()
