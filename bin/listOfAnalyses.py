#!/usr/bin/env python3

"""
.. module:: listOfAnalyses
         :synopsis: Small script to produce the ListOfAnalyses wiki page,
                    new markdown syntax

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

from __future__ import print_function
import setPath
try:
    import subprocess as C
except:
    import commands as C
import sys, os
from smodels.experiment.databaseObj import Database
from smodels.tools.smodelsLogging import setLogLevel
from smodels.tools.physicsUnits import TeV

def convert ( string ):
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

def yesno ( B ):
    if B in [ True, "True" ]: return "Yes"
    if B in [ False, "False" ]: return "No"
    return "?"

def header( f, database, superseded, add_version, private ):
    """
    :params f: file handle
    :params database: database handle
    :params private: mark wiki page as private (-All:read)
    """
    version = database.databaseVersion
    dotlessv = ""
    if add_version:
        dotlessv = version.replace(".","")
    titleplus = ""
    referToOther = "Link to list of results [including superseded results](ListOfAnalyses%sWithSuperseded)" % dotlessv
    if superseded:
        referToOther = "Link to list of results [without superseded results](ListOfAnalyses%s)" % dotlessv
        add=", including superseded results."
        titleplus = "(including superseded results)"
    n_maps = 0
    n_results = 0
    n_topos = set()
    n_anas = set()
    expRs = database.getExpResults( useSuperseded = superseded )
    for expR in expRs:
        n_anas.add ( expR.id() )
        for t in expR.getTxNames():
            n_topos.add ( t.txName )
        for d in expR.getValuesFor ( "dataId" ):
            ds = expR.getDataset ( d )
            n_results += 1
            n_maps += len ( ds.txnameList )
    protected="+All:read"
    if private:
        protected="-All:read"
    f.write (
# """#acl +DeveloperGroup:read,write,revert -All:write,read Default
"""

# List Of Analyses %s %s 
List of analyses and topologies in the SMS results database,
comprising %d individual maps from %d distinct signal regions, %d different SMS topologies, from a total of %d analyses.
The list has been created from the database version `%s`.
Results from FastLim are included. There is also an  [sms dictionary](SmsDictionary%s) and a [validation page](Validation%s).
%s.
""" % ( version, titleplus, n_maps, n_results, len(n_topos), 
        len(n_anas), version, dotlessv, dotlessv, referToOther ) )

def footer ( f ):
    #f.write ( "<<Anchor(A1)>>(1) ''Home-grown'' result, i.e. produced by SModelS collaboration, using recasting tools like MadAnalysis5 or CheckMATE.\n\n" )
    #f.write ( "<<Anchor(A2)>>(2) Please note that by default we discard zeroes-only results from !FastLim. To remain firmly conservative, we consider efficiencies with relative statistical uncertainties > 25% to be zero.\n\n" )
    #f.write ( "<<Anchor(A3)>>(3) Aggregated result; the results are the public ones, but aggregation is done by the SModelS collaboration.\n" )
    f.write ( "\n\n<a name='A1'>(1)</a> ''Home-grown'' result, i.e. produced by SModelS collaboration, using recasting tools like MadAnalysis5 or CheckMATE.\n\n" )
    f.write ( "<a name='A2'>(2)</a> Please note that by default we discard zeroes-only results from FastLim. To remain firmly conservative, we consider efficiencies with relative statistical uncertainties > 25% to be zero.\n\n" )
    f.write ( "<a name='A3'>(3)</a> Aggregated result; the results are the public ones, but aggregation is done by the SModelS collaboration.\n" )

def listTables ( f, anas ):
    f.write ( "## Individual tables\n" )
    for sqrts in [ 13, 8 ]:
        run = 1
        if sqrts == 13: run = 2
        f.write ( "### Run %d - %d TeV\n" % ( run, sqrts ) )
        for exp in [ "ATLAS", "CMS" ]:
            for tpe in [ "upper limits", "efficiency maps" ]:
                stpe = tpe.replace(" ", "" )
                a = selectAnalyses ( anas, sqrts, exp, tpe )
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
                    flim = "(of which %d FastLim)" % nfastlim
                    aflim = "(of which %d FastLim)" % a_fastlim
                if nres_hscp>0:
                    llp="(of which %d LLP)" % nres_hscp
                #f.write ( " * [[#%s%s%d|%s %s]]: %d %s analyses, %s %s%s results\n" % \
                #          ( exp, stpe, sqrts, exp, tpe, len(a), aflim, nres, flim, llp ) )
                f.write ( " * [%s %s](#%s%s%d): %d %s analyses, %s %s%s results\n" % \
                          ( exp, tpe, exp, stpe, sqrts, len(a), aflim, nres, flim, llp ) )

def fields ( superseded ):
    fields = [ "ID", "short description", "L [1/fb]", "Tx names" ]
    # fields = [ "ID", "short description", "&radic;s", "L", "Tx names" ]
    if superseded:
        fields.append ( "superseded by" )
    return fields

def xsel( filename ):
    import os
    #cmd="cat %s | xsel -i" % filename
    #os.system ( cmd )
    #print ( cmd )
    cmd="mv %s ../../smodels.github.io/docs/%s.md" % ( filename, filename )
    os.system ( cmd )
    print ( cmd )

def experimentHeader ( f, experiment, Type, sqrts, nr, superseded ):
    f.write ( "\n" )
    stype = "efficiency maps"
    if Type == "upperLimit":
        stype = "upper limits"
    f.write ( '<a name="%s%s%d"></a>\n' % \
              (experiment, stype.replace(" ",""), sqrts) )
    f.write ( "## %s, %s, %d TeV (%d analyses)\n\n" % \
              (experiment,stype,sqrts,nr ) )
    lengths = []
    for i in fields ( superseded ):
        # f.write ( "||<#EEEEEE:> '''%s'''" % i )
        f.write ( "| **%s** " % i )
        lengths.append ( len(i)+6 )
    f.write ( "|\n" )
    for l in lengths:
        f.write ( "|" +"-"*l )
    f.write ( "|\n" )

def emptyLine( f, superseded, ana_name ):
    #f.write ( "||" )
    #f.write ( " ||"*( len(fields(superseded) ) ) )
    #f.write ( "\n" )
    label = "Publications"
    if "PAS" in ana_name:
        label = "Physics Analysis Summaries"
        label = "PAS"
    if "CONF" in ana_name:
        label = "Conf Notes"
    f.write ( "| %s" % "**%s**" % label )
    f.write ( " |"*( len(fields(superseded) ) ) )
    f.write ( "\n" )

def writeOneTable ( f, db, experiment, Type, sqrts, anas, superseded, n_homegrown,
                    version, add_version ):
    dotlessv = ""
    if add_version:
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
    experimentHeader ( f, experiment, Type, sqrts, len(anas), superseded )
    keys.sort()
    # print ( keys )
    previous = keys[0]

    emptyLine( f, superseded, previous )

    for ana_name in keys:
        if len ( ana_name ) != len ( previous ):
            emptyLine( f, superseded, ana_name )
        previous = ana_name
        ana = anadict[ana_name]
        # import IPython
        # IPython.embed()
        try:
            comment = ana.globalInfo.comment
        except Exception as e:
            comment = ""
        # print ( comment )
        fastlim = ( "created from fastlim" in comment )
        topos = list ( set ( map ( str, ana.getTxNames() ) ) )
        homegrownd = {}
        for i in ana.getTxNames():
            if i.validated not in [ True, "n/a", "N/A" ]:
                print ( "Error: validated is %s in %s. Don't know how to handle." % ( i.validated, ana.globalInfo.id ) )
                sys.exit(-1)
            homegrownd[str(i)] = ""
            if hasattr ( i, "source" ) and "SModelS" in i.source:
                # homegrownd[str(i)] = " [[#A1|(1)]]"
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

            if homegrown !="" : n_homegrown[0]+=1
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
        # f.write ( "|| [[%s|%s]]<<Anchor(%s)>>" % ( url, Id, Id ) )
        f.write ( '| [%s](%s)<a name="%s"></a>' % ( Id, url, Id ) )
        if not hasattr ( ana.globalInfo, "prettyName" ):
            print ( "Analysis %s has no pretty name defined." % ana.globalInfo.id )
            print ( "Please add a pretty name and repeat." )
            sys.exit()
        short_desc = convert ( ana.globalInfo.prettyName )
        f.write ( " | %s | %s | %s |" % ( short_desc,
               ana.globalInfo.lumi.asNumber(), topos_s ) )
        #f.write ( "|| %s || %d || %s || %s ||" % ( short_desc,
        #       ana.globalInfo.sqrts.asNumber(), ana.globalInfo.lumi.asNumber(), topos_s ) )
        if superseded:
            f.write ( "%s |" % ssuperseded )
        f.write ( "\n" )

def selectAnalyses ( anas, sqrts, experiment, Type ):
    ret = []
    T=Type.replace(" ","" ).lower().replace("maps","map").replace("limits","limit" )
    # print ( "select",len(anas),sqrts,experiment,T )
    for ana in anas:
        xsqrts = int ( ana.globalInfo.sqrts.asNumber ( TeV ) )
        id = ana.globalInfo.id
        if sqrts != xsqrts:
            continue
        # print ( id )
        ds0 = ana.datasets[0]
        dt = ana.datasets[0].dataInfo.dataType.lower().replace("maps","map")
        # print ( "dt=",dt )
        if not experiment in id or not T == dt:
            continue
        ret.append ( ana )
    return ret

def writeExperiment ( f, db, experiment, sqrts, superseded, n_homegrown, version, add_version ):
    print ( "Experiment:", experiment )
    tanas = db.getExpResults( useSuperseded=superseded )
    for Type in [ "upperLimit", "efficiencyMap" ]:
        anas = []
        for ana in tanas:
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
        writeOneTable ( f, db, experiment, Type, sqrts, anas, superseded, \
                        n_homegrown, version, add_version )

def backup( filename ):
    if not os.path.exists ( filename ):
        return
    o = C.getoutput ( "cp %s Old%s" % ( filename, filename ) )
    if len(o):
        print ( "backup: %s" % o )

def diff( filename ):
    o = C.getoutput ( "diff %s Old%s" % ( filename, filename ) )
    if len(o)==0:
        print ( "No changes in %s since last call." % filename )
        return
    print ( "%s has changed (%d changes)" % ( filename, len(o.split() ) ) )

def help():
    print ( "Usage: %s [-n] [-h]" % sys.argv[0] )
    print ( "       -n: dont add superseded results" )
    print ( "       -h: show this help" )
    sys.exit()

def main():
    n_homegrown=[0]
    superSeded=True
    import argparse
    argparser = argparse.ArgumentParser(description='Create list of analyses in wiki format, see http://smodels.hephy.at/wiki/ListOfAnalyses')
    argparser.add_argument ( '-n', '--no_superseded', help='ignore superseded results', action='store_true' )
    argparser.add_argument ( '-p', '--private', help='declare as private (add wiki acl line on top)', action='store_true' )
    argparser.add_argument ( '-d', '--database', help='path to database [../../smodels-database]',
                             type=str, default='../../smodels-database' )
    argparser.add_argument ( '-v', '--verbose', help='verbosity level (error, warning, info, debug) [info]', type=str, default='info' )
    argparser.add_argument ( '-a', '--add_version', help='add version labels to links', action='store_true' )
    args = argparser.parse_args()
    setLogLevel ( args.verbose )
    superSeded = not args.no_superseded
    database = Database ( args.database, discard_zeroes=True )
    ver = ""
    if args.add_version:
        ver = database.databaseVersion.replace(".","")
    filename = "ListOfAnalyses%s" % ver
    if superSeded:
        filename = "ListOfAnalyses%sWithSuperseded" % ver
    backup( filename )
    f = open ( filename, "w" )
    header( f, database, superSeded, args.add_version, args.private )
    listTables ( f, database.getExpResults ( useSuperseded = superSeded ) )
    print ( "Database:", database.databaseVersion )
    experiments=[ "CMS", "ATLAS" ]
    for sqrts in [ 13, 8 ]:
        for experiment in experiments:
            writeExperiment ( f, database, experiment, sqrts, \
                              superSeded, n_homegrown, database.databaseVersion, args.add_version )
    print ( "%d home-grown now" % n_homegrown[0] )
    footer ( f )
    f.close()
    diff( filename )
    xsel( filename )

if __name__ == '__main__':
    main()
