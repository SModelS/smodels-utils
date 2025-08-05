#!/usr/bin/env python3

"""
.. module:: listOfAnalyses
  :synopsis: Small script to produce the ListOfAnalyses wiki page, markdown syntax,
             see https://smodels.github.io/docs/ListOfAnalyses

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

import setPath
try:
    import subprocess as C
except:
    import commands as C
import sys, os, time
from smodels.experiment.databaseObj import Database
from smodels.experiment.expResultObj import ExpResult
from smodels.base.smodelsLogging import setLogLevel
from smodels.base.physicsUnits import TeV
from smodels_utils.helper.various import hasLLHD, removeAnaIdSuffices
from smodels_utils.helper import databaseManipulations as manips
from typing import Union

class Lister:
    def __init__ ( self ):
        self.n_homegrown = 0
        self.stats = set()
        self.github_io = "../../smodels.github.io/"

    def metaStatisticsPlot ( self ):
        # return ## FIXME remove
        import sys
        sys.path.insert(0,"../../protomodels/ptools")
        sys.path.insert(0,"../../protomodels")
        sys.path.insert(0,"../../")
        from protomodels.ptools import expResModifier
        # print ( "[listOfAnalyses] starting roughviz" )
        options = { "compute_ps": True, "suffix": "temp" }
        # options["database"]="../../smodels-database" 
        options["dbpath"]=self.dbpath
        options["outfile"]="none"
        modifier = expResModifier.ExpResModifier ( options )
        from protomodels.plotting import plotDBDict
        poptions = { "topologies": None, "roughviz": False }
        poptions["dictfile"] = "./temp.dict"
        poptions["show"] = True
        poptions["title"] = ""
        # poptions["Zmax"] = 3.25
        poptions["nbins"] = 29
        poptions["options"] = {'ylabel':'# signal regions', 'plot_averages': False,\
           'plotStats': True }
        # poptions["roughviz"] = False
        poptions["pvalues"] = False
        poptions["outfile"] = "tmp.png"
        poptions["nosuperseded"]= not self.includeSuperseded
        poptions["nofastlim"]= not self.includeFastlim
        plotter = plotDBDict.Plotter ( poptions )
        #print ( "[listOfAnalyses] ending roughviz" )
        sigsplot = self.significancesPlotFileName()
        cmd = f"mv tmp.png {self.github_io}/{sigsplot}"
        os.system ( cmd )
        print ( f"[listOfAnalyses] {cmd}" )
        if os.path.exists ( poptions["dictfile"] ) and not self.keep:
            os.unlink ( poptions["dictfile"] )
        if self.fudged:
            options["fudge"]=0.7
            options["suffix"]="fudge"
            options["outfile"]="none"
            del plotter
            del modifier
            modifier = expResModifier.ExpResModifier ( options )
            from protomodels.plotting import plotDBDict
            poptions = { "topologies": None, "roughviz": False }
            poptions["dictfile"] = "./fudge.dict"
            poptions["show"] = True
            poptions["title"] = ""
            # poptions["Zmax"] = 4.25
            poptions["nbins"] = 29
            poptions["options"] = {'ylabel':'# signal regions', \
                'plot_averages': False, 'plotStats': True }
            # poptions["roughviz"] = False
            poptions["pvalues"] = False
            poptions["outfile"] = "tmp.png"
            poptions["nosuperseded"]=not self.includeSuperseded
            plotter = plotDBDict.Plotter ( poptions )
            #print ( "[listOfAnalyses] ending roughviz" )
            sigsplot = self.significancesPlotFileName( "fudged" )
            cmd = f"mv tmp.png {self.github_io}/{sigsplot}"
            os.system ( cmd )
            print ( f"[listOfAnalyses] {cmd}" )
            if os.path.exists ( poptions["dictfile"] ) and not self.keep:
                os.unlink ( poptions["dictfile"] )

    def convert ( self, string ):
        ret = string.replace ( ">=", "&ge;" )
        ret = ret.replace ( "alphaT", "&alpha;<sub>T</sub>" )
        ret = ret.replace ( "phi", "&phi;" )
        ret = ret.replace ( "\\Phi", "&Phi;" )
        ret = ret.replace ( "\\Delta", "&Delta;" )
        ret = ret.replace ( "alpha_T", "&alpha;<sub>T</sub>" )
        ret = ret.replace ( "_T", "<sub>T</sub>" )
        ret = ret.replace ( "_T2", "<sub>T2</sub>" )
        ret = ret.replace ( "MT2", "M<sub>T2</sub>" )
        ret = ret.replace ( "_CT", "<sub>CT</sub>" )
        return ret

    def whatLlhdInfo ( self, B : ExpResult ) -> str:
        """ what llhd info does that analysis have, if any? """
        if hasattr ( B.globalInfo, "jsonFiles" ):
            return "json"
        if hasattr ( B.globalInfo, "covariance" ):
            if hasattr ( B.datasets[0].dataInfo, "thirdMoment" ) and B.datasets[0].dataInfo.thirdMoment != None:
                return "SLv2"
            return "SLv1"
        return ""

    def header( self ):
        """
        :params f: file handle
        :params database: database handle
        """
        version = self.database.databaseVersion
        if "+" in version:
            version = version [ :version.find("+") ]
        titleplus = ""
        referToOther = f"Link to list of results [including superseded and fastlim results](ListOfAnalyses{self.dotlessv}WithSuperseded)"
        if self.includeSuperseded:
            referToOther = f"Link to list of results [without superseded results](ListOfAnalyses{self.dotlessv})"
            add=", including superseded results."
            titleplus = "(including superseded results)"
            if self.includeFastlim:
                add=", including superseded and fastlim results"
                titleplus = "(including superseded and fastlim results)"
                referToOther = f"Link to list of results [without superseded and fastlim results](ListOfAnalyses{self.dotlessv})"
        n_maps = 0
        n_results = 0
        n_topos = set()
        n_anas = set()
        hasAgg = []
        for expR in self.expRes:
            if "-agg" in expR.id():
                ## when we have -agg results, we dont count the maps
                ## of the non-aggregated ones
                anaId = removeAnaIdSuffices ( expR.id() )
                hasAgg.append ( anaId )
        for expR in self.expRes:
            self.stats.add ( expR.id() )
            expId = removeAnaIdSuffices ( expR.id() )
            if expR.id() in hasAgg and expR.datasets[0].dataInfo.dataId != None:
                # we have the non-aggregate result here, skip it. count only
                # the aggregate
                continue
            n_anas.add ( expId )
            for t in expR.getTxNames():
                n_topos.add ( t.txName )
            #dataIds = expR.getValuesFor ( "dataId" )
            #print ( ">>> dataIds", dataIds )
            dataIds = [ x.dataInfo.dataId for x in expR.datasets if x != None ]
            # print ( ">>> XataIds", dataIds )
            for d in dataIds:
                #if "CMS" in expR.id():
                #    print ( f"now at {expR.id()}:{d}" )
                ds = expR.getDataset ( d )
                n_results += 1
                if ds == None:
                    print ( f"warning, {expR.id()},{d} is empty" )
                    # sys.exit(-1)
                    continue
                topos = set()
                for i in ds.txnameList:
                    if i.validated in [ True, "N/A", "n/a" ]:
                        topos.add ( i.txName )
                    else:
                        print ( f"[listOfAnalyses] skipping {expRes.globalInfo.id}:{dataset.dataInfo.dataId}:{i}: validated={i.validated}" )
                n_maps += len(topos)
                # n_maps += len ( ds.txnameList )
        self.f.write ( f"# List Of Analyses {version} {titleplus}\n" )
        self.f.write ( "List of analyses and topologies in the SMS results database, " )
        self.f.write ( f"comprising {n_maps} individual maps from {n_results} distinct signal regions, ")
        self.f.write ( f"{len(n_topos)} different SMS topologies, from a total of {len(n_anas)} analyses.\n" )
        self.f.write ( f"The list has been created from the database version `{version}.`\n")
        if self.includeFastlim:
            self.f.write ( "Results from FastLim are included. " )
        self.f.write ( f"There is also an  [sms dictionary](SmsDictionary{self.dotlessv}) and a [validation page](Validation{self.dotlessv}).\n" )
        self.f.write ( f"{referToOther}.\n" )
        sigsplot = self.significancesPlotFileName()
        self.f.write ( f"\n<p align='center'><img src='../{sigsplot}?{time.time()}' alt='plot of significances' width='400' /><br><sub>Plot: Significances with respect to the Standard Model hypothesis, for all signal regions in the database. A standard normal distribution is expected if no new physics is in the data. New physics would manifest itself as an overabundance of large (positive) significances.</sub></p>\n" )
        # self.f.write ( f"\n![../{pvaluesplot}](../{pvaluesplot}?{time.time()})\n" )

    def significancesPlotFileName ( self, postfix : str = "" ):
        """ the name of the significances plot.

        :param postfix: allows to specify a postfix to the name
        """
        sinc = ""
        if self.includeSuperseded:
            sinc = "iss"
        directory = f"validation/{self.dotlessv}"
        fullname = f"{self.github_io}/{directory}"
        if not os.path.exists ( fullname ):
            os.mkdir ( fullname )
        pvaluesplot = f"{directory}/significances{sinc}{postfix}.png"
        return pvaluesplot

    def footer ( self ):
        # previous version self.f.write ( "\n\n<a name='A1'>(1)</a> Expected upper limits ('exp. ULs'): Can be used to compute a crude approximation of a likelihood, modelled as a truncated Gaussian.\n\n" )
        self.f.write ( "\n\n<a name='A1'>(1)</a> Expected upper limits ('exp. ULs'): allow SModelS to determine the sensitivity of UL results. Moreover, they may be used to compute a crude approximation of a likelihood, modelled as a truncated Gaussian (currently an experimental feature).\n\n" )
        self.f.write ( "<a name='A2'>(2)</a> Likelihood information for combination of signal regions ('SR comb.'): 'SLv1' = a covariance matrix for a simplified likelihood v1. 'SLv2' = a covariance matrix plus third momenta for simplified likelihood v2. 'json' = full likelihoods as pyhf json files.\n\n" )
        self.f.write ( "<a name='A3'>(3)</a> ''Home-grown'' result, i.e. produced by SModelS collaboration, using recasting tools like MadAnalysis5 or CheckMATE.\n\n" )
        self.f.write ( "<a name='A4'>(4)</a> Aggregated result; the results are the public ones, but aggregation is done by the SModelS collaboration.\n\n" )
        if self.includeFastlim:
            self.f.write ( "<a name='A5'>(5)</a> Please note that by default we discard zeroes-only results from FastLim. To remain firmly conservative, we consider efficiencies with relative statistical uncertainties > 25% to be zero.\n\n" )
        self.f.write ( f"\nThis page was created {time.asctime()}.\n" )
        self.f.close()

    def listTables ( self ):
        """ Example:
        Run 1 - 8 TeV
        In total, we have results from 15 ATLAS and 18 CMS 8 TeV searches.
        ATLAS upper limits: 13 analyses, 34 results
        """
        self.f.write ( "\n## Stats by run, experiment, type\n" )
        for sqrts in [ 13, 8 ]:
            run = 1
            if sqrts == 13: run = 2
            self.f.write ( f"\n### Run {run} - {sqrts} TeV\n" )
            anas = { "CMS": set(), "ATLAS": set() }
            for exp in [ "ATLAS", "CMS" ]:
                for tpe in [ "efficiency maps", "upper limits" ]:
                    stpe = tpe.replace(" ", "" )
                    a = self.selectAnalyses ( sqrts, exp, tpe )
                    for ana in a:
                        shortid = removeAnaIdSuffices ( ana.globalInfo.id )
                        anas[exp].add ( shortid )
            self.f.write ( f"In total, we have results from {len(anas['ATLAS'])} ATLAS and {len(anas['CMS'])} CMS {sqrts} TeV searches.\n" )

            for exp in [ "ATLAS", "CMS" ]:
                for tpe in [ "efficiency maps", "upper limits" ]:
                    nMaps = 0
                    stpe = tpe.replace(" ", "" )
                    a = self.selectAnalyses ( sqrts, exp, tpe )
                    aids = set ( [ removeAnaIdSuffices ( x.globalInfo.id ) for x in a ] )
                    if tpe == "efficiency maps" and False:
                        print ( f"{exp}{sqrts}={list(aids)}" )
                    a_fastlim = 0
                    nres = 0
                    nres_hscp = set()
                    nfastlim = 0
                    for A in a:
                        topos = set ( [ x.txName for x in A.getTxNames() ] )
                        for _ in A.getTxNames():
                            if hasattr ( _, "finalState" ):
                                fState = _.finalState
                                nonMet = False
                                if fState is not None:
                                    for fs in fState:
                                        if fs != "MET":
                                            nonMet = True
                                if nonMet:
                                    nres_hscp.add ( _.txName )
                        for ds in A.datasets:
                            nMaps += len ( ds.txnameList )
                        nres+= len ( topos )
                        if hasattr ( A.globalInfo, "contact" ) and "fastlim" in \
                            A.globalInfo.contact:
                                nfastlim += len(topos)
                                a_fastlim += 1
                    if len(a) == 0: continue
                    nres_hscp = len ( nres_hscp )
                    flim=""
                    aflim=""
                    llp=""
                    if nfastlim:
                        flim = f" (of which {nfastlim} FastLim)"
                        aflim = f" (of which {a_fastlim} FastLim)"
                    if nres_hscp>0:
                        llp= f" (of which {nres_hscp} LLP)"
                    mapsCountS = ""
                    if "efficiency" in tpe:
                        mapsCountS = f", {nMaps} individual maps"

                    line = f" * [{exp} {tpe}](#{exp}{sqrts}): {len(aids)}{aflim} analyses, {nres}{flim}{llp} results{mapsCountS}\n"
                    self.f.write ( line )


    def fields ( self ):
        """ get list of all columns.
        :returns: list
        """
        ret = [ "ID", "short description", "L [1/fb]", "Tx names" ]
        # fields = [ "ID", "short description", "&radic;s", "L", "Tx names" ]
        if self.includeSuperseded:
            ret.append ( "superseded by" )
        ret.append ( "obs. ULs" )
        if self.likelihoods:
            ret.append ( "exp. ULs [(1)](#A1)" )
        ret.append ( "EMs" )
        if self.likelihoods:
            ret.append ( "SR comb. [(2)](#A2)" )
        return ret

    def moveToGithub( self ):
        """ move files to smodels.github.io """
        # return ## fixme remove
        import os
        # fixme move not copy!
        cmd=f"mv {self.filename} {self.github_io}/docs/{self.filename}.md"
        os.system ( cmd )
        print ( f"[listOfAnalyses] {cmd}" )

    def experimentHeader ( self, experiment : str, sqrts : int, nr : int ):
        """ e.g.:
        ATLAS, upper limits, 13 TeV (35 analyses)
        """
        self.f.write ( "\n" )
        self.f.write ( f'<a name="{experiment}{sqrts}"></a>\n' )
        self.f.write ( f"## {experiment}, {sqrts} TeV ({nr} analyses)\n\n" )
        lengths = []
        for i in self.fields ( ):
            # f.write ( f"||<#EEEEEE:> '''{i}'''" )
            self.f.write ( f"| **{i}** " )
            # lengths.append ( len(i)+2 ) # for mdcat
            lengths.append ( len(i)+6 ) # ideal for direct viewing
        self.f.write ( "|\n" )
        for l in lengths:
            self.f.write ( f"|{'-' * l}" )
        self.f.write ( "|\n" )

    def getLabel ( self, ana_name ):
        """ get the type of ana: Publication, PAS, conf note """
        label = "Publications"
        if "PAS" in ana_name:
            label = "Physics Analysis Summaries"
            label = "PAS"
            label = "Preliminary results"
        if "CONF" in ana_name:
            label = "Conf Notes"
            label = "Preliminary results"
        return label

    def emptyLine( self, ana_name : Union [ None, str]  = None ):
        """ write a header line in the matrix 
        :param ana_name: the analysis name of the next analysis, so we
        can choose an approriate title. If none given, use self.previous
        """
        if ana_name == None:
            ana_name = self.previous
        label = self.getLabel ( ana_name )
        self.f.write ( f"| **{label}**" )
        self.f.write ( " |"*( len(self.fields( ) ) ) )
        self.f.write ( "\n" )

    def writeOneTable ( self, experiment : str, sqrts : int, anas : list ):
        """ e.g.:
        ATLAS, upper limits, 13 TeV (35 analyses)

        (table)
        """
        version = self.database.databaseVersion
        dotlessv = ""
        if self.add_version:
            dotlessv = version.replace(".","")
        keys, anadict = [], {}
        for ana in anas:
            id = removeAnaIdSuffices ( ana.globalInfo.id )
            xsqrts = int ( ana.globalInfo.sqrts.asNumber ( TeV ) )
            if xsqrts != sqrts:
                continue
            if not experiment in id:
                continue
            keys.append ( id )
            if not id in anadict:
                anadict[id] = []
            anadict[id].append ( ana )
        keys = list ( set ( keys ) )
        if len(keys) == 0:
            return
        self.experimentHeader ( experiment, sqrts, len(keys) )
        def sorter(key):
            tuples = key.split("-")
            ct=0
            number=0
            for t in tuples[::-1]:
                if t in [ "SUS", "EXO", "B2G", "HIG" ]:
                    continue
                if t in [ "PAS", "CONF" ]:
                    number -= 10**9
                    continue
                try:
                    number += int(t) * 1000**ct
                    ct+=1
                except:
                    pass
            return number
        ## now we need to sort the analysis ids
        keys.sort( key = sorter, reverse=True ) ## sorting purely by the numbers
        self.previous = keys[0]

        self.emptyLine( )

        for ana_name in keys:
            self.writeOneAnalysis ( ana_name, anadict )

    def writeOneAnalysis ( self, ana_name : str, anadict : dict ):
        """ one entry in the table, one line, one analysis """
        if self.getLabel ( ana_name ) != self.getLabel ( self.previous ):
            self.emptyLine( ana_name )
        self.previous = ana_name
        canas = anadict[ana_name]
        ana = canas[0]
        try:
            comment = ana.globalInfo.comment
        except Exception as e:
            comment = ""
        fastlim = ( "created from fastlim" in comment )
        topos = list ( set ( map ( str, ana.getTxNames() ) ) )
        homegrownd = {}
        has = { "oul": False, "eul": False, "em": False, "agg": False }
        for cana in canas:
            for ds in cana.datasets:
                if ds.getType() == "efficiencyMap":
                    has["em"]=True
                if ds.getType() == "upperLimit":
                    has["oul"]=True
                    for txn in ds.txnameList:
                        if hasattr ( txn, "txnameDataExp" ):
                            has["eul"] = True
            if "-agg" in cana.globalInfo.id:
                has [ "agg" ] = True
            for i in cana.getTxNames():
                if not self.ignore and i.validated not in [ True, "n/a", "N/A" ]:
                    print ( f"Error: validated is {i.validated} in {ana.globalInfo.id}:{i}. Don't know how to handle. Use '-i' if you want me to skip this issue." )
                    sys.exit(-1)
                homegrownd[str(i)] = ""
                if hasattr ( i, "source" ) and "SModelS" in i.source:
                    homegrownd[str(i)] = " [(3)](#A3)"
                if has["agg"]:
                # if hasattr ( i, "source" ) and "SModelS" in i.source and "agg" in ana_name:
                    homegrownd[str(i)] = " [(4)](#A4)"

        topos.sort()
        topos_s = ""
        topos_names = set()
        for i in topos:
            topos_names.add ( i )
            homegrown = homegrownd[i]

            if homegrown !="" : self.n_homegrown+=1
            topos_s += f", [{i}](SmsDictionary{self.dotlessv}#{i}){homegrown}"
        topos_s = topos_s[2:]
        if fastlim:
            # topos_s += " (from FastLim (2))"
            topos_s += " (from FastLim [(5)](#A5))"
            pass
        url = ana.globalInfo.url
        if url.find ( " " ) > 0:
            url = url[:url.find(" ") ]
        Id = ana.globalInfo.id
        ssuperseded = ""
        if hasattr ( ana.globalInfo, "supersededBy" ):
            s = ana.globalInfo.supersededBy
            t = s
            if t.find(" " ) > 0:
                t=t[:t.find(" ")]
            ssuperseded = f"[{s}](#{t})"
        Id = removeAnaIdSuffices ( Id )
        self.f.write ( f'| [{Id}]({url})<a name="{Id}"></a>' )
        if not hasattr ( ana.globalInfo, "prettyName" ):
            print ( f"Analysis {ana.globalInfo.id} has no pretty name defined." )
            print ( "Please add a pretty name and repeat." )
            sys.exit()
        short_desc = self.convert ( ana.globalInfo.prettyName )
        self.f.write ( f" | {short_desc} | {ana.globalInfo.lumi.asNumber()} | {topos_s} |" )
        if self.includeSuperseded:
            self.f.write ( f"{ssuperseded} |" )
        hasoUL = self.linkIfYes ( has["oul"], ana.globalInfo.id, "ul" )
        haseUL = self.linkIfYes ( has["oul"], ana.globalInfo.id, "ul" )
        hasEM = self.linkIfYes ( has["em"], ana.globalInfo.id, "em" )
        self.f.write ( f" {hasoUL} |" ) 
        if self.likelihoods:
            self.f.write ( f" {haseUL} |" )
        self.f.write ( f" {hasEM} |" ) 
        if self.likelihoods:
            llhd = "".join ( set ( [ self.whatLlhdInfo ( x ) for x in canas ] ) )
            self.f.write ( f" {llhd} |" )
        self.f.write ( "\n" )

    def linkIfYes ( self, B : bool, anaId : str, linkTo : str ) -> str:
        """ if B is True, then link to validation plot
        :param anaId: analysis Id, e.g. CMS-SUS-20-004
        :param linkTo: what to link to, e.g. "UL"
        """
        if B in [ False, "False" ]: return ""
        baseUrl = f"https://smodels.github.io/docs/Validation{self.dotlessv}#"
        if B in [ True, "True" ]: 
            return f"[&#x1F517;]({baseUrl}{anaId}_{linkTo})"
            # return f"[&#10004;]({baseUrl}{anaId}_{linkTo})"
        return f"[?]({baseUrl}{anaId}_{linkTo})"

    def yesno ( self, B ):
        if B in [ True, "True" ]: return "&#10004;"
        if B in [ False, "False" ]: return ""
        return "?"

    def writeStatsFile ( self ):
        """ write out the stats file """
        if not self.write_stats:
            return
        statsfile = "analyses.py"
        print ( f"[listOfAnalyses] Writing stats file {statsfile}." )
        f = open ( statsfile, "wt" )
        f.write ( f"# superseded: {self.includeSuperseded}\n" )
        f.write ( f"A={self.stats!s}\n" )
        f.close()

    def selectAnalyses ( self, sqrts, experiment, Type ):
        ret = []
        T=Type.replace(" ","" ).lower().replace("maps","map").replace("limits","limit" )
        for ana in self.expRes:
            xsqrts = int ( ana.globalInfo.sqrts.asNumber ( TeV ) )
            id = ana.globalInfo.id
            if sqrts != xsqrts:
                continue
            ds0 = ana.datasets[0]
            dt = ana.datasets[0].dataInfo.dataType.lower().replace("maps","map")
            if not experiment in id or not T == dt:
                continue
            ret.append ( ana )
        return ret

    def writeExperiment ( self,  experiment : str, sqrts : int ):
        """ e.g.:
        ATLAS, upper limits, 13 TeV (35 analyses)

        (table)
        """
        print ( f"[listOfAnalyses] {experiment}, {sqrts} TeV" )
        anas = []
        for ana in self.expRes:
            id = ana.globalInfo.id
            xsqrts = int ( ana.globalInfo.sqrts.asNumber ( TeV ) )
            if sqrts != xsqrts:
                continue
            # print ( id )
            ds0 = ana.datasets[0]
            dt = ana.datasets[0].dataInfo.dataType
            if not experiment in id:
                continue
            anas.append ( ana )
        self.writeOneTable ( experiment, sqrts, anas )

    def backup( self ):
        if not os.path.exists ( self.filename ):
            return
        o = C.getoutput ( f"cp {self.filename} Old{self.filename}" )
        if len(o):
            print ( f"backup: {o}" )

    def diff( self ):
        o = C.getoutput ( f"diff {self.filename} Old{self.filename}" )
        if len(o)==0:
            print ( f"No changes in {self.filename} since last call." )
            return
        print ( f"[listOfAnalyses] {self.filename} has changed ({len(o.split())} changes)" )

    def createSuperseded ( self ):
        """ create the database of superseded results """
        print ( "[listOfAnalyses] creating database of superseded results" )
        manips.createSupersededPickle ( self.dbpath, "superseded.pcl", False )

    def main( self ):
        import argparse
        argparser = argparse.ArgumentParser(description='Create list of analyses in wiki format, see https://smodels.github.io/docs/ListOfAnalyses')
        argparser.add_argument ( '-n', '--no_superseded', action='store_true',
                                 help='ignore (filter out) superseded results' )
        argparser.add_argument ( '-d', '--database',
                                 help='path to database [../../smodels-database]',
                                 type=str, default='../../smodels-database' )
        argparser.add_argument ( '-v', '--verbose',
                                 help='verbosity level (error, warning, info, debug) [info]',
                                 type=str, default='info' )
        argparser.add_argument ( '-i', '--ignore', action='store_true',
                                  help='ignore the validation flags of analysis '\
                                  '(i.e. also add non-validated results)' )
        argparser.add_argument ( '-s', '--no_pngs', action='store_true',
                                  help='do not regenerate the significances plots'\
                                  '(i.e. also add non-validated results)' )
        argparser.add_argument ( '-l', '--likelihoods', action='store_true',
                                 help='add info about likelihoods' )
        argparser.add_argument ( '-f', '--fastlim', action='store_true',
                                 help='add fastlim results' )
        argparser.add_argument ( '-k', '--keep', action='store_true',
                                 help='keep temporary files, like temp.dict' )
        argparser.add_argument ( '--fudged', action='store_true',
                                 help='create also fudged version of significance plot' )
        argparser.add_argument ( '-a', '--add_version', action='store_true',
                                 help='add version labels to links' )
        argparser.add_argument ( '-S', '--write_stats', action='store_true',
                                 help='write the analyses.py stats file' )
        args = argparser.parse_args()
        setLogLevel ( args.verbose )
        self.keep = args.keep
        self.fudged = args.fudged
        self.includeSuperseded = not args.no_superseded
        self.likelihoods = args.likelihoods
        self.write_stats = args.write_stats
        self.dbpath = args.database
        self.createSuperseded()
        dbpath = self.dbpath
        if self.includeSuperseded:
            dbpath += "+./superseded.pcl"
        self.database = Database ( dbpath )
        ver = ""
        if args.add_version:
            ver = self.database.databaseVersion.replace(".","")
        if "+" in ver:
            ver = ver [ :ver.find("+") ]
        filename = f"ListOfAnalyses{ver}"
        if self.includeSuperseded:
            filename += "WithSuperseded"
        self.filename = filename
        self.add_version = args.add_version ## add version number
        self.dotlessv = ""
        if self.add_version:
            self.dotlessv = ver
        self.ignore = args.ignore ## ignore validation flags
        self.includeFastlim = args.fastlim
        self.expRes = self.database.getExpResults ( useNonValidated = self.ignore  )
        if not self.includeSuperseded:
            self.expRes = manips.filterSupersededFromList ( self.expRes )
        if not self.includeFastlim:
            self.expRes = manips.filterFastLimFromList ( self.expRes )
        self.backup()
        self.f = open ( filename, "w" )
        self.header()
        self.listTables ( )
        print ( "[listOfAnalyses] Database:", self.database.databaseVersion )
        experiments=[ "ATLAS", "CMS" ]
        for sqrts in [ 13, 8 ]:
            for experiment in experiments:
                self.writeExperiment ( experiment, sqrts )
        print ( f"[listOfAnalyses] {self.n_homegrown} home-grown now" )
        self.footer ( )
        self.diff()
        if not args.no_pngs:
            self.metaStatisticsPlot()
        self.moveToGithub( )
        self.writeStatsFile()

if __name__ == '__main__':
    lister = Lister()
    lister.main()
