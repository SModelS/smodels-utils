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
from smodels.tools.smodelsLogging import setLogLevel
from smodels.tools.physicsUnits import TeV
from smodels_utils.helper.various import hasLLHD, removeAnaIdSuffices
from smodels_utils.helper import databaseManipulations as manips

class Lister:
    def __init__ ( self ):
        self.n_homegrown = 0
        self.stats = set()

    def metaStatisticsPlot ( self ):
        sys.path.insert(0,"../../protomodels/ptools")
        sys.path.insert(0,"../../protomodels")
        sys.path.insert(0,"../../")
        from protomodels.ptools import expResModifier
        # print ( "[listOfAnalyses] starting roughviz" )
        options = { "compute_ps": True, "suffix": "temp" }
        # options["database"]="../../smodels-database" 
        options["dbpath"]=self.dbpath
        modifier = expResModifier.ExpResModifier ( options )
        from protomodels.plotting import plotDBDict
        poptions = { "topologies": None, "roughviz": True }
        poptions["dictfile"] = "./dbtemp.dict"
        poptions["show"] = True
        poptions["title"] = ""
        poptions["Zmax"] = 3.25
        poptions["nbins"] = 13
        poptions["options"] = {'ylabel':'# signal regions'}
        # poptions["roughviz"] = False
        poptions["significances"] = True
        poptions["outfile"] = "tmp.png"
        plotter = plotDBDict.Plotter ( poptions )
        #print ( "[listOfAnalyses] ending roughviz" )
        pvaluesplot = self.pvaluesPlotFileName()
        cmd = f"mv tmp.png ../../smodels.github.io/{pvaluesplot}"
        os.system ( cmd )
        print ( f"[listOfAnalyses] {cmd}" )
        os.unlink ( "dbtemp.dict" )

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

    def whatLlhdInfo ( self, B ):
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
        dotlessv = ""
        if self.add_version:
            dotlessv = version.replace(".","")
        self.dotlessv = dotlessv
        titleplus = ""
        referToOther = "Link to list of results [including superseded and fastlim results](ListOfAnalyses%sWithSuperseded)" % dotlessv
        if self.includeSuperseded:
            referToOther = "Link to list of results [without superseded results](ListOfAnalyses%s)" % dotlessv
            add=", including superseded results."
            titleplus = "(including superseded results)"
            if self.includeFastlim:
                add=", including superseded and fastlim results"
                titleplus = "(including superseded and fastlim results)"
                referToOther = "Link to list of results [without superseded and fastlim results](ListOfAnalyses%s)" % dotlessv
        n_maps = 0
        n_results = 0
        n_topos = set()
        n_anas = set()
        for expR in self.expRes:
            self.stats.add ( expR.id() )
            expId = removeAnaIdSuffices ( expR.id() )
            n_anas.add ( expId )
            for t in expR.getTxNames():
                n_topos.add ( t.txName )
            #dataIds = expR.getValuesFor ( "dataId" )
            #print ( ">>> dataIds", dataIds )
            dataIds = [ x.dataInfo.dataId for x in expR.datasets if x != None ]
            # print ( ">>> XataIds", dataIds )
            for d in dataIds:
                ds = expR.getDataset ( d )
                n_results += 1
                if ds == None:
                    print ( f"warning, {expR.id()},{d} is empty" )
                    # sys.exit(-1)
                    continue
                n_maps += len ( ds.txnameList )
        self.f.write ( f"# List Of Analyses {version} {titleplus}\n" )
        self.f.write ( "List of analyses and topologies in the SMS results database, " )
        self.f.write ( f"comprising {n_maps} individual maps from {n_results} distinct signal regions, ")
        self.f.write ( f"{len(n_topos)} different SMS topologies, from a total of {len(n_anas)} analyses.\n" )
        self.f.write ( f"The list has been created from the database version `{version}.`\n")
        if self.includeFastlim:
            self.f.write ( "Results from FastLim are included. " )
        self.f.write ( f"There is also an  [sms dictionary](SmsDictionary{dotlessv}) and a [validation page](Validation{dotlessv}).\n" )
        self.f.write ( referToOther + ".\n" )
        pvaluesplot = self.pvaluesPlotFileName()
        self.f.write ( f"\n<p align='center'><img src='../{pvaluesplot}?{time.time()}' alt='p-values plot' width='400' /></p>\n" )
        # self.f.write ( f"\n![../{pvaluesplot}](../{pvaluesplot}?{time.time()})\n" )

    def pvaluesPlotFileName ( self ):
        sinc = ""
        if self.includeSuperseded:
            sinc = "iss"
        #pngname = f"pvalues{sinc}{self.dotlessv}.png"
        #pvaluesplot = f"images/{pngname}"
        pvaluesplot = f"validation/{self.dotlessv}/pvalues{sinc}.png"
        return pvaluesplot

    def footer ( self ):
        self.f.write ( "\n\n<a name='A1'>(1)</a> ''Home-grown'' result, i.e. produced by SModelS collaboration, using recasting tools like MadAnalysis5 or CheckMATE.\n\n" )
        self.f.write ( "<a name='A2'>(2)</a> Aggregated result; the results are the public ones, but aggregation is done by the SModelS collaboration.\n\n" )
        self.f.write ( "<a name='A3'>(3)</a> Expected upper limits ('exp. ULs'): Can be used to compute a crude approximation of a likelihood, modelled as a truncated Gaussian.\n\n" )
        self.f.write ( "<a name='A4'>(4)</a> Likelihood information for combination of signal regions ('SR comb.'): 'SLv1' = a covariance matrix for a simplified likelihood v1. 'SLv2' = a covariance matrix plus third momenta for simplified likelihood v2. 'json' = full likelihoods as pyhf json files.\n" )
        if self.includeFastlim:
            self.f.write ( "<a name='A5'>(5)</a> Please note that by default we discard zeroes-only results from FastLim. To remain firmly conservative, we consider efficiencies with relative statistical uncertainties > 25% to be zero.\n\n" )
        self.f.write ( "\nThis page was created %s.\n" % ( time.asctime() ) )
        self.f.close()

    def listTables ( self ):
        self.f.write ( "\n## Individual tables\n" )
        for sqrts in [ 13, 8 ]:
            run = 1
            if sqrts == 13: run = 2
            self.f.write ( "\n### Run %d - %d TeV\n" % ( run, sqrts ) )
            anas = { "CMS": set(), "ATLAS": set() }
            for exp in [ "ATLAS", "CMS" ]:
                for tpe in [ "upper limits", "efficiency maps" ]:
                    stpe = tpe.replace(" ", "" )
                    a = self.selectAnalyses ( sqrts, exp, tpe )
                    for ana in a:
                        shortid = removeAnaIdSuffices ( ana.globalInfo.id )
                        anas[exp].add ( shortid )
            self.f.write ( "In total, we have results from %d ATLAS and %d CMS %d TeV searches.\n" % (len(anas["ATLAS"]), len(anas["CMS"]), sqrts ) )

            for exp in [ "ATLAS", "CMS" ]:
                for tpe in [ "upper limits", "efficiency maps" ]:
                    nMaps = 0
                    stpe = tpe.replace(" ", "" )
                    a = self.selectAnalyses ( sqrts, exp, tpe )
                    aids = set ( [ removeAnaIdSuffices ( x.globalInfo.id ) for x in a ] )
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
                        flim = " (of which %d FastLim)" % nfastlim
                        aflim = " (of which %d FastLim)" % a_fastlim
                    if nres_hscp>0:
                        llp=" (of which %d LLP)" % nres_hscp
                    mapsCountS = ""
                    if "efficiency" in tpe:
                        mapsCountS = ", %d individual maps" % nMaps

                    line = f" * [{exp} {tpe}](#{exp}{stpe}{sqrts}): {len(aids)}{aflim} analyses, {nres}{flim}{llp} results{mapsCountS}\n"
                    self.f.write ( line )


    def fields ( self, isEffMap ):
        """ get list of all columns.
        :param isEffMap: is efficiency map table? In which case we might add a column
                         for the likelihoods.
        :returns: list
        """
        ret = [ "ID", "short description", "L [1/fb]", "Tx names" ]
        # fields = [ "ID", "short description", "&radic;s", "L", "Tx names" ]
        if self.includeSuperseded:
            ret.append ( "superseded by" )
        if self.likelihoods:
            if isEffMap:
                ret.append ( "SR comb. [(4)](#A4)" )
            else:
                ret.append ( "exp. ULs [(3)](#A3)" )
            # ret.append ( "likeli- hoods" )
        return ret

    def moveToGithub( self ):
        """ move files to smodels.github.io """
        import os
        cmd="mv %s ../../smodels.github.io/docs/%s.md" % \
             ( self.filename, self.filename )
        os.system ( cmd )
        print ( f"[listOfAnalyses] {cmd}" )

    def experimentHeader ( self, experiment, Type, sqrts, nr ):
        self.f.write ( "\n" )
        stype = "efficiency maps"
        isEffMap = True
        if Type == "upperLimit":
            isEffMap = False
            stype = "upper limits"
        self.f.write ( '<a name="%s%s%d"></a>\n' % \
                  (experiment, stype.replace(" ",""), sqrts) )
        self.f.write ( "## %s, %s, %d TeV (%d analyses)\n\n" % \
                  (experiment,stype,sqrts,nr ) )
        lengths = []
        for i in self.fields ( isEffMap  ):
            # f.write ( "||<#EEEEEE:> '''%s'''" % i )
            self.f.write ( "| **%s** " % i )
            lengths.append ( len(i)+6 )
        self.f.write ( "|\n" )
        for l in lengths:
            self.f.write ( "|" +"-"*l )
        self.f.write ( "|\n" )

    def getLabel ( self, ana_name ):
        """ get the type of ana: Publication, PAS, conf note """
        label = "Publications"
        if "PAS" in ana_name:
            label = "Physics Analysis Summaries"
            label = "PAS"
        if "CONF" in ana_name:
            label = "Conf Notes"
        return label

    def emptyLine( self, ana_name, isEffMap ):
        label = self.getLabel ( ana_name )
        self.f.write ( "| %s" % "**%s**" % label )
        self.f.write ( " |"*( len(self.fields( isEffMap ) ) ) )
        self.f.write ( "\n" )

    def writeOneTable ( self, experiment, Type, sqrts, anas ):
        version = self.database.databaseVersion
        dotlessv = ""
        isEffMap = True
        if Type == "upperLimit":
            isEffMap = False
        if self.add_version:
            dotlessv = version.replace(".","")
        keys, anadict = [], {}
        for ana in anas:
            id = removeAnaIdSuffices ( ana.globalInfo.id )
            xsqrts = int ( ana.globalInfo.sqrts.asNumber ( TeV ) )
            # print ( "sqrts,xsqrts=", sqrts, xsqrts )
            if xsqrts != sqrts:
                continue
            if not experiment in id:
                continue
            keys.append ( id )
            anadict[id] = ana
        keys = list ( set ( keys ) )
        if len(keys) == 0:
            return
        self.experimentHeader ( experiment, Type, sqrts, len(keys) )
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
        # keys.sort( reverse=True ) # sorting, but taking into account sus, exo, pas,
        # print ( "xxxx keys", keys )
        previous = keys[0]

        self.emptyLine( previous, isEffMap )

        for ana_name in keys:
            #print ( "ana_name", ana_name, "previous", previous, len ( ana_name ) != len ( previous ) )
            if self.getLabel ( ana_name ) != self.getLabel ( previous ):
                self.emptyLine( ana_name, isEffMap )
            previous = ana_name
            ana = anadict[ana_name]
            try:
                comment = ana.globalInfo.comment
            except Exception as e:
                comment = ""
            fastlim = ( "created from fastlim" in comment )
            topos = list ( set ( map ( str, ana.getTxNames() ) ) )
            homegrownd = {}
            for i in ana.getTxNames():
                if not self.ignore and i.validated not in [ True, "n/a", "N/A" ]:
                    print ( "Error: validated is %s in %s. Don't know how to handle. Use '-i' if you want me to skip this issue." % ( i.validated, ana.globalInfo.id ) )
                    sys.exit(-1)
                homegrownd[str(i)] = ""
                if hasattr ( i, "source" ) and "SModelS" in i.source:
                    homegrownd[str(i)] = " [(1)](#A1)"
                if hasattr ( i, "source" ) and "SModelS" in i.source and "agg" in ana_name:
                    homegrownd[str(i)] = " [(2)](#A2)"

            topos.sort()
            # print ( topos )
            topos_s = ""
            topos_names = set()
            for i in topos:
                topos_names.add ( i )
                homegrown = homegrownd[i]

                if homegrown !="" : self.n_homegrown+=1
                # topos_s += ", [[SmsDictionary%s#%s|%s]]%s" % ( dotlessv, i, i, homegrown )
                topos_s += ", [%s](SmsDictionary%s#%s)%s" % ( i, dotlessv, i, homegrown )
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
                # ssuperseded = "[[#%s|%s]]" % ( t, s )
                ssuperseded = "[%s](#%s)" % ( s, t )
            sId = Id
            if not sId.endswith ( "-eff" ) and not sId.endswith( "-ma5" ) and \
               not sId.endswith ( "-agg" ):
                   sId += "-eff"
            Id = removeAnaIdSuffices ( Id )
            self.f.write ( '| [%s](%s)<a name="%s"></a>' % ( Id, url, sId ) )
            if not hasattr ( ana.globalInfo, "prettyName" ):
                print ( "Analysis %s has no pretty name defined." % ana.globalInfo.id )
                print ( "Please add a pretty name and repeat." )
                sys.exit()
            short_desc = self.convert ( ana.globalInfo.prettyName )
            self.f.write ( " | %s | %s | %s |" % ( short_desc,
                   ana.globalInfo.lumi.asNumber(), topos_s ) )
            if self.includeSuperseded:
                self.f.write ( "%s |" % ssuperseded )
            if self.likelihoods:
                if isEffMap:
                    llhd = self.whatLlhdInfo ( ana )
                    self.f.write ( " %s |" % llhd )
                else:
                    llhd = self.yesno ( hasLLHD ( ana ) )
                    self.f.write ( " %s |" % llhd )
            self.f.write ( "\n" )

    def yesno ( self, B ):
        if B in [ True, "True" ]: return "&#10004;"
        if B in [ False, "False" ]: return ""
        return "?"

    def writeStatsFile ( self ):
        """ write out the stats file """
        statsfile = "analyses.py"
        print ( f"[listOfAnalyses] Writing stats file {statsfile}." )
        f = open ( statsfile, "wt" )
        f.write ( "# superseded: %d\n" % self.includeSuperseded )
        f.write ( "A=" + str ( self.stats )+"\n" )
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

    def writeExperiment ( self,  experiment, sqrts ):
        print ( "[listOfAnalyses] Experiment:", experiment )
        for Type in [ "upperLimit", "efficiencyMap" ]:
            anas = []
            for ana in self.expRes:
                id = ana.globalInfo.id
                xsqrts = int ( ana.globalInfo.sqrts.asNumber ( TeV ) )
                if sqrts != xsqrts:
                    continue
                # print ( id )
                ds0 = ana.datasets[0]
                dt = ana.datasets[0].dataInfo.dataType
                if not experiment in id or not Type == dt:
                    continue
                anas.append ( ana )
            self.writeOneTable ( experiment, Type, sqrts, anas )

    def backup( self ):
        if not os.path.exists ( self.filename ):
            return
        o = C.getoutput ( "cp %s Old%s" % ( self.filename, self.filename ) )
        if len(o):
            print ( "backup: %s" % o )

    def diff( self ):
        o = C.getoutput ( "diff %s Old%s" % ( self.filename, self.filename ) )
        if len(o)==0:
            print ( "No changes in %s since last call." % self.filename )
            return
        print ( "[listOfAnalyses] %s has changed (%d changes)" % ( self.filename, len(o.split() ) ) )

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
        argparser.add_argument ( '-l', '--likelihoods', action='store_true',
                                 help='add info about likelihoods' )
        argparser.add_argument ( '-f', '--fastlim', action='store_true',
                                 help='add fastlim results' )
        argparser.add_argument ( '-a', '--add_version', action='store_true',
                                 help='add version labels to links' )
        args = argparser.parse_args()
        setLogLevel ( args.verbose )
        self.includeSuperseded = not args.no_superseded
        self.likelihoods = args.likelihoods
        self.dbpath = args.database
        self.createSuperseded()
        dbpath = self.dbpath
        if self.includeSuperseded:
            dbpath += "+./superseded.pcl"
        self.database = Database ( dbpath, discard_zeroes=True )
        ver = ""
        if args.add_version:
            ver = self.database.databaseVersion.replace(".","")
        if "+" in ver:
            ver = ver [ :ver.find("+") ]
        filename = "ListOfAnalyses%s" % ver
        if self.includeSuperseded:
            filename = "ListOfAnalyses%sWithSuperseded" % ver
        self.filename = filename
        self.add_version = args.add_version ## add version number
        self.ignore = args.ignore ## ignore validation flags
        self.includeFastlim = args.fastlim
        self.expRes = self.database.getExpResults ( )
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
        print ( "[listOfAnalyses] %d home-grown now" % self.n_homegrown )
        self.footer ( )
        self.diff()
        self.metaStatisticsPlot()
        self.moveToGithub( )
        self.writeStatsFile()

if __name__ == '__main__':
    lister = Lister()
    lister.main()
