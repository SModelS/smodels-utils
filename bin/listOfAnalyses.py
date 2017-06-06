#!/usr/bin/env python

"""
.. module:: listOfAnalyses
         :synopsis: Small script to produce the ListOfAnalyses wiki page

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

from __future__ import print_function
import setPath
import commands 
import sys
from short_descriptions import SDs
from smodels.experiment.databaseObj import Database
from smodels.tools.smodelsLogging import setLogLevel
from smodels.tools.physicsUnits import TeV

# setLogLevel("debug")
    
def yesno ( B ):
    if B in [ True, "True" ]: return "Yes"
    if B in [ False, "False" ]: return "No"
    return "?"

def header( f, version, superseded ):
    add="."
    titleplus = ""
    referToOther = "Link to list of results [[ListOfAnalysesWithSuperseded|including superseded results]]"
    if superseded:
        referToOther = "Link to list of results [[ListOfAnalyses|without superseded results]]"
        add=",including superseded results."
        titleplus = " (including superseded results)"
    f.write ( 
# """#acl +DeveloperGroup:read,write,revert -All:write,read Default 
"""#acl +DeveloperGroup:read,write,revert -All:write +All:read Default 
<<LockedPage()>>

= List Of Analyses %s =
List of analyses and topologies in the SMS results database of v1.1%s
The list has been created from the database version `%s`.
There is also an SmsDictionary.
%s
""" % ( titleplus, add, version, referToOther ) )

def listTables ( f, anas ):
    f.write ( "== Individual tables ==\n" )
    for sqrts in [ 13, 8 ]:
        run = 1
        if sqrts == 13: run = 2
        f.write ( "\n=== Run %d - %d TeV ===\n" % ( run, sqrts ) )
        for exp in [ "ATLAS", "CMS" ]:
            for tpe in [ "upper limits", "efficiency maps" ]:
                stpe = tpe.replace(" ", "" )
                a = selectAnalyses ( anas, sqrts, exp, tpe )
                nres = 0
                for A in a:
                    nres+= len ( A.getTxNames() )
                if len(a) == 0: continue
                f.write ( " * [[#%s%s%d|%s %s]]: %d analyses, %d results\n" % \
                          ( exp, stpe, sqrts, exp, tpe, len(a), nres ) )

def fields ( superseded ):
    fields = [ "ID", "short description", "L [1/fb]", "Tx names" ]
    # fields = [ "ID", "short description", "&radic;s", "L", "Tx names" ]
    if superseded:
        fields.append ( "superseded by" )
    return fields

def xsel( filename ):
    import os
    cmd="cat %s | xsel -i" % filename
    os.system ( cmd )
    print ( cmd )

def experimentHeader ( f, experiment, Type, sqrts, nr, superseded ):
    f.write ( "\n" )
    stype = "efficiency maps"
    if Type == "upperLimit": 
        stype = "upper limits"
    f.write ( "== %s, %s, %d TeV (%d analyses) ==\n" % \
              (experiment,stype,sqrts,nr ) )
    f.write ( "<<Anchor(%s%s%d)>>\n" % \
              (experiment, stype.replace(" ",""), sqrts) )
    for i in fields ( superseded ):
        f.write ( "||<#EEEEEE:> '''%s'''" % i )
    f.write ( "||\n" )

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
    f.write ( "||  %s" % "'''%s'''" % label )
    f.write ( " ||"*( len(fields(superseded) ) ) )
    f.write ( "\n" )

def writeOneTable ( f, db, experiment, Type, sqrts, anas, superseded ):
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
        topos.sort()
        # print ( topos )
        topos_s = ""
        for i in topos:
            topos_s += ", [[SmsDictionary#%s|%s]]" % ( i, i )
        topos_s = topos_s[2:]
        if fastlim:
            topos_s = "(from fastlim)"
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
            ssuperseded = "[[#%s|%s]]" % ( t, s )
        f.write ( "|| [[%s|%s]]<<Anchor(%s)>>" % ( url, Id, Id ) )
        short_desc = ""
        if Id in SDs: short_desc = SDs[Id]
        f.write ( "|| %s || %s || %s ||" % ( short_desc,
               ana.globalInfo.lumi.asNumber(), topos_s ) )
        #f.write ( "|| %s || %d || %s || %s ||" % ( short_desc,
        #       ana.globalInfo.sqrts.asNumber(), ana.globalInfo.lumi.asNumber(), topos_s ) )
        if superseded:
            f.write ( "%s ||" % ssuperseded )
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

def writeExperiment ( f, db, experiment, sqrts, superseded ):
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
        writeOneTable ( f, db, experiment, Type, sqrts, anas, superseded )

def backup( filename ):
    o = commands.getoutput ( "cp %s Old%s" % ( filename, filename ) )
    if len(o):
        print ( "backup: %s" % o )

def diff( filename ):
    o = commands.getoutput ( "diff %s Old%s" % ( filename, filename ) )
    if len(o)==0:
        print ( "No changes in %s since last call." % filename )
        return
    print ( "%s has changed (%d changes)" % ( filename, len(o.split() ) ) )

def main():
    superSeded=True
    for i in sys.argv[1:]:
        if i == "-n": superSeded=False
    filename = "ListOfAnalyses"
    if superSeded:
        filename = "ListOfAnalysesWithSuperseded"
    backup( filename )
    f = open ( filename, "w" )
    database = Database ( '../../smodels-database/' )
    header( f, database.databaseVersion, superSeded )
    listTables ( f, database.getExpResults ( useSuperseded = superSeded ) )
    print ( "Database", database.databaseVersion )
    experiments=[ "CMS", "ATLAS" ]
    for sqrts in [ 13, 8 ]:
        for experiment in experiments:
            writeExperiment ( f, database, experiment, sqrts, superSeded )
    f.close()
    diff( filename )
    xsel( filename )
    
if __name__ == '__main__':
    main()    
