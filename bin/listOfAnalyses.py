#!/usr/bin/env python

"""
.. module:: listOfAnalyses
         :synopsis: Small script to produce the ListOfAnalyses wiki page

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

from __future__ import print_function
import setPath
import commands 
from short_descriptions import SDs
from smodels.experiment.databaseObj import Database
    
def yesno ( B ):
    if B in [ True, "True" ]: return "Yes"
    if B in [ False, "False" ]: return "No"
    return "?"

def header( f, version ):
    f.write ( 
# """#acl +DeveloperGroup:read,write,revert -All:write,read Default 
# <<LockedPage()>>
"""#acl +DeveloperGroup:read,write,revert -All:write +All:read Default 

= List Of Analyses =
List of analyses and topologies in the SMS results database of v1.1.
The list has been created from the database version `%s`.
There is also an SmsDictionary.

Individual tables: [[#CMSupperLimit|CMS upper limits]], [[#CMSefficiencyMap|CMS efficiency maps]], [[#ATLASupperLimit|ATLAS upper limits]], [[#ATLASefficiencyMap|ATLAS efficiency Maps]]

""" % version )
    
fields = [ "ID", "short description", "L", "&radic;s", "Tx names", "superseded by" ]

def xsel():
    import os
    cmd="cat ListOfAnalyses | xsel -i"
    os.system ( cmd )
    print ( cmd )

def experimentHeader ( f, experiment, Type, nr ):
    f.write ( "\n" )
    stype = "efficiency maps"
    if Type == "upperLimit": 
        stype = "upper limits"
    f.write ( "== %s, %s (%d results) ==\n" % (experiment,stype,nr ) )
    f.write ( "<<Anchor(%s%s)>>\n" % (experiment, Type ) )
    for i in fields:
        f.write ( "||<#EEEEEE:> '''%s'''" % i )
    f.write ( "||\n" )

def emptyLine( f ):
        f.write ( "||" )
        f.write ( " ||"*( len(fields) ) )
        f.write ( "\n" )

def writeOneTable ( f, db, experiment, Type, anas ):
    experimentHeader ( f, experiment, Type, len(anas) )

    keys, anadict = [], {}
    for ana in anas:
        id = ana.globalInfo.id
        if not experiment in id:
            continue
        keys.append ( id )
        anadict[id] = ana
    keys = list ( set ( keys ) )
    keys.sort()
    # print ( keys )
    previous = keys[0]

    for ana_name in keys:
        if len ( ana_name ) != len ( previous ):
            emptyLine( f )
        previous = ana_name
        ana = anadict[ana_name]
        # import IPython
        # IPython.embed()
        try:
            comment = ana.globalInfo.comment
        except Exception as e:
            comment = ""
        # print ( comment )
        fastlim = ( "fastlim" in comment )
        topos = list ( set ( map ( str, ana.getTxNames() ) ) )
        topos.sort()
        # print ( topos )
        topos_s = ""
        for i in topos:
            topos_s += ", [[SmsDictionary#%s|%s]]" % (i, i )
        topos_s = topos_s[2:]
        if fastlim:
            topos_s = "(from fastlim)"
        url = ana.globalInfo.url
        if url.find ( " " ) > 0:
            url = url[:url.find(" ") ]
        Id = ana.globalInfo.id
        superseded = ""
        if hasattr ( ana.globalInfo, "supersededBy" ):
            s = ana.globalInfo.supersededBy
            t = s
            if t.find(" " ) > 0:
                t=t[:t.find(" ")]
            superseded = "[[#%s|%s]]" % ( t, s )
        f.write ( "|| [[%s|%s]]<<Anchor(%s)>>" % ( url, Id, Id ) )
        short_desc = ""
        if Id in SDs: short_desc = SDs[Id]
        f.write ( "|| %s || %s || %d || %s ||" % ( short_desc,
               ana.globalInfo.lumi.asNumber(), ana.globalInfo.sqrts.asNumber(), topos_s ) )
        if "superseded by" in fields:
            f.write ( "%s ||" % superseded )
        f.write ( "\n" )

def writeExperiment ( f, db, experiment ):
    tanas = db.getExpResults( useSuperseded=True )
    for Type in [ "upperLimit", "efficiencyMap" ]:
        anas = []
        for ana in tanas:
            id = ana.globalInfo.id
            # print ( id )
            ds0 = ana.datasets[0]
            dt = ana.datasets[0].dataInfo.dataType
            if not experiment in id or not Type == dt:
                continue
            anas.append ( ana )
        writeOneTable ( f, db, experiment, Type, anas )

def backup():
    o = commands.getoutput ( "cp ListOfAnalyses OldListOfAnalyses" )
    if len(o):
        print ( "backup: %s" % o )

def diff():
    o = commands.getoutput ( "diff ListOfAnalyses OldListOfAnalyses" )
    if len(o)==0:
        print ( "No changes in ListOfAnalyses since last call." )
        return
    print ( "ListOfAnalyses has changed (%d changes)" % ( len(o.split() ) ) )

def main():
    backup()
    f = open ( "ListOfAnalyses", "w" )
    database = Database ( '../../smodels-database/' )
    header( f, database.databaseVersion )
    print ( "Database", database.databaseVersion )
    experiments=[ "CMS", "ATLAS" ]
    for experiment in experiments:
        writeExperiment ( f, database, experiment )
    f.close()
    diff()
    xsel()
    
if __name__ == '__main__':
    main()    
