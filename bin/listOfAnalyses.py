#!/usr/bin/env python3

"""
.. module:: listOfAnalyses
         :synopsis: Small script to produce the ListOfAnalyses wiki page,
                    markdown syntax.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

from __future__ import print_function
import setPath
try:
    import subprocess as C
except:
    import commands as C
import sys, os, time
from smodels.experiment.databaseObj import Database
from smodels.tools.smodelsLogging import setLogLevel
from smodels.tools.physicsUnits import TeV
from smodels_utils.helper.various import hasLLHD

class Lister:
    def __init__ ( self ):
        self.n_homegrown = 0

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

    def yesno ( self, B ):
        if B in [ True, "True" ]: return "&#10004;"
        if B in [ False, "False" ]: return ""
        return "?"
        #if B in [ True, "True" ]: return "Yes"
        #if B in [ False, "False" ]: return "No"
        #return "?"

    def header( self ):
        """
        :params f: file handle
        :params database: database handle
        """
        version = self.database.databaseVersion
        dotlessv = ""
        if self.add_version:
            dotlessv = version.replace(".","")
        titleplus = ""
        referToOther = "Link to list of results [including superseded results](ListOfAnalyses%sWithSuperseded)" % dotlessv
        if self.superSeded:
            referToOther = "Link to list of results [without superseded results](ListOfAnalyses%s)" % dotlessv
            add=", including superseded results."
            titleplus = "(including superseded results)"
        n_maps = 0
        n_results = 0
        n_topos = set()
        n_anas = set()
        for expR in self.expRes:
            n_anas.add ( expR.id() )
            for t in expR.getTxNames():
                n_topos.add ( t.txName )
            for d in expR.getValuesFor ( "dataId" ):
                ds = expR.getDataset ( d )
                n_results += 1
                n_maps += len ( ds.txnameList )
        self.f.write (
    """

# List Of Analyses %s %s
List of analyses and topologies in the SMS results database,
comprising %d individual maps from %d distinct signal regions, %d different SMS topologies, from a total of %d analyses.
The list has been created from the database version `%s`.
Results from FastLim are included. There is also an  [sms dictionary](SmsDictionary%s) and a [validation page](Validation%s).
%s.
    """ % ( version, titleplus, n_maps, n_results, len(n_topos),
            len(n_anas), version, dotlessv, dotlessv, referToOther ) )

    def footer ( self ):
        self.f.write ( "\n\n<a name='A1'>(1)</a> ''Home-grown'' result, i.e. produced by SModelS collaboration, using recasting tools like MadAnalysis5 or CheckMATE.\n\n" )
        self.f.write ( "<a name='A2'>(2)</a> Please note that by default we discard zeroes-only results from FastLim. To remain firmly conservative, we consider efficiencies with relative statistical uncertainties > 25% to be zero.\n\n" )
        self.f.write ( "<a name='A3'>(3)</a> Aggregated result; the results are the public ones, but aggregation is done by the SModelS collaboration.\n" )
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
                        anas[exp].add ( ana.globalInfo.id )
            self.f.write ( "In total, we have results from %d ATLAS and %d CMS %d TeV searches.\n" % (len(anas["ATLAS"]), len(anas["CMS"]), sqrts ) )
                
            for exp in [ "ATLAS", "CMS" ]:
                for tpe in [ "upper limits", "efficiency maps" ]:
                    nMaps = 0
                    stpe = tpe.replace(" ", "" )
                    a = self.selectAnalyses ( sqrts, exp, tpe )
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

                    self.f.write ( " * [%s %s](#%s%s%d): %d %s analyses, %s%s%s results%s\n" % \
                              ( exp, tpe, exp, stpe, sqrts, len(a), aflim, nres, flim, llp, mapsCountS ) )

    def fields ( self ):
        ret = [ "ID", "short description", "L [1/fb]", "Tx names" ]
        # fields = [ "ID", "short description", "&radic;s", "L", "Tx names" ]
        if self.superSeded:
            ret.append ( "superseded by" )
        if self.likelihoods:
            ret.append ( "llhds" )
        return ret

    def moveToGithub( self ):
        """ move files to smodels.github.io """
        import os
        cmd="mv %s ../../smodels.github.io/docs/%s.md" % \
             ( self.filename, self.filename )
        os.system ( cmd )
        print ( cmd )

    def experimentHeader ( self, experiment, Type, sqrts, nr ):
        self.f.write ( "\n" )
        stype = "efficiency maps"
        if Type == "upperLimit":
            stype = "upper limits"
        self.f.write ( '<a name="%s%s%d"></a>\n' % \
                  (experiment, stype.replace(" ",""), sqrts) )
        self.f.write ( "## %s, %s, %d TeV (%d analyses)\n\n" % \
                  (experiment,stype,sqrts,nr ) )
        lengths = []
        for i in self.fields ( ):
            # f.write ( "||<#EEEEEE:> '''%s'''" % i )
            self.f.write ( "| **%s** " % i )
            lengths.append ( len(i)+6 )
        self.f.write ( "|\n" )
        for l in lengths:
            self.f.write ( "|" +"-"*l )
        self.f.write ( "|\n" )

    def emptyLine( self, ana_name ):
        label = "Publications"
        if "PAS" in ana_name:
            label = "Physics Analysis Summaries"
            label = "PAS"
        if "CONF" in ana_name:
            label = "Conf Notes"
        self.f.write ( "| %s" % "**%s**" % label )
        self.f.write ( " |"*( len(self.fields() ) ) )
        self.f.write ( "\n" )

    def writeOneTable ( self, experiment, Type, sqrts, anas ):
        version = self.database.databaseVersion
        dotlessv = ""
        if self.add_version:
            dotlessv = version.replace(".","")
        keys, anadict = [], {}
        for ana in anas:
            id = ana.globalInfo.id
            xsqrts = int ( ana.globalInfo.sqrts.asNumber ( TeV ) )
            # print ( "sqrts,xsqrts=", sqrts, xsqrts )
            if xsqrts != sqrts:
                continue
            id = ana.globalInfo.id
            if not experiment in id:
                continue
            keys.append ( id )
            anadict[id] = ana
        keys = list ( set ( keys ) )
        if len(keys) == 0:
            return
        self.experimentHeader ( experiment, Type, sqrts, len(anas) )
        keys.sort()
        # print ( keys )
        previous = keys[0]

        self.emptyLine( previous )

        for ana_name in keys:
            if len ( ana_name ) != len ( previous ):
                self.emptyLine( ana_name )
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
                    print ( "Error: validated is %s in %s. Don't know how to handle." % ( i.validated, ana.globalInfo.id ) )
                    sys.exit(-1)
                homegrownd[str(i)] = ""
                if hasattr ( i, "source" ) and "SModelS" in i.source:
                    homegrownd[str(i)] = " [(1)](#A1)"
                if hasattr ( i, "source" ) and "SModelS" in i.source and "agg" in ana_name:
                    homegrownd[str(i)] = " [(3)](#A3)"
                    #homegrownd[str(i)] = " [[#A3|(3)]]"

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
                topos_s += " (from FastLim [(2)](#A2))"
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
            self.f.write ( '| [%s](%s)<a name="%s"></a>' % ( Id, url, Id ) )
            if not hasattr ( ana.globalInfo, "prettyName" ):
                print ( "Analysis %s has no pretty name defined." % ana.globalInfo.id )
                print ( "Please add a pretty name and repeat." )
                sys.exit()
            short_desc = self.convert ( ana.globalInfo.prettyName )
            self.f.write ( " | %s | %s | %s |" % ( short_desc,
                   ana.globalInfo.lumi.asNumber(), topos_s ) )
            if self.superSeded:
                self.f.write ( "%s |" % ssuperseded )
            if self.likelihoods:
                llhd = self.yesno ( hasLLHD ( ana ) )
                self.f.write ( "%s |" % llhd )
            self.f.write ( "\n" )

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
        print ( "Experiment:", experiment )
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
        print ( "%s has changed (%d changes)" % ( self.filename, len(o.split() ) ) )

    def main( self ):
        import argparse
        argparser = argparse.ArgumentParser(description='Create list of analyses in wiki format, see https://smodels.github.io/docs/ListOfAnalyses')
        argparser.add_argument ( '-n', '--no_superseded', help='ignore superseded results', action='store_true' )
        argparser.add_argument ( '-d', '--database', help='path to database [../../smodels-database]',
                                 type=str, default='../../smodels-database' )
        argparser.add_argument ( '-v', '--verbose', help='verbosity level (error, warning, info, debug) [info]', type=str, default='info' )
        argparser.add_argument ( '-i', '--ignore', help='ignore the validation flags of analysis (i.e. also add non-validated results)', action='store_true' )
        argparser.add_argument ( '-l', '--likelihoods', help='add info about likelihoods', action='store_true' )
        argparser.add_argument ( '-a', '--add_version', help='add version labels to links', action='store_true' )
        args = argparser.parse_args()
        setLogLevel ( args.verbose )
        self.superSeded = not args.no_superseded
        self.likelihoods = args.likelihoods
        self.database = Database ( args.database, discard_zeroes=True )
        ver = ""
        if args.add_version:
            ver = self.database.databaseVersion.replace(".","")
        filename = "ListOfAnalyses%s" % ver
        if self.superSeded:
            filename = "ListOfAnalyses%sWithSuperseded" % ver
        self.filename = filename
        self.add_version = args.add_version ## add version number
        self.ignore = args.ignore ## ignore validation flags
        self.expRes = self.database.getExpResults ( useSuperseded = self.superSeded )
        self.backup()
        self.f = open ( filename, "w" )
        self.header()
        self.listTables ( )
        print ( "Database:", self.database.databaseVersion )
        experiments=[ "CMS", "ATLAS" ]
        for sqrts in [ 13, 8 ]:
            for experiment in experiments:
                self.writeExperiment ( experiment, sqrts )
        print ( "%d home-grown now" % self.n_homegrown )
        self.footer ( )
        self.diff()
        self.moveToGithub( )

if __name__ == '__main__':
    lister = Lister()
    lister.main()
