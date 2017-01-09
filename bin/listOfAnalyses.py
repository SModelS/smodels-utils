#!/usr/bin/env python

"""
.. module:: listOfAnalyses
         :synopsis: Small script to produce the ListOfAnalyses wiki page

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

from __future__ import print_function
import setPath
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

To experiment: [[#CMS|CMS]], [[#ATLAS|ATLAS]]

""" % version )
    

def xsel():
    import os
    cmd="cat ListOfAnalyses | xsel -i"
    os.system ( cmd )
    print ( cmd )

def experimentHeader ( f, experiment ):
    f.write ( "\n" )
    f.write ( "== %s ==\n" % experiment )
    f.write ( "<<Anchor(%s)>>\n" % experiment )
    # f.write ( "||<#EEEEEE:> '''ID''' ||<#EEEEEE:> '''short description''' ||<#EEEEEE:> '''L''' ||<#EEEEEE:> '''Tx names''' ||\n" )
    f.write ( "||<#EEEEEE:> '''ID''' ||<#EEEEEE:> '''short description''' ||<#EEEEEE:> '''L''' ||<#EEEEEE:> '''&radic;s''' ||<#EEEEEE:> '''Tx names''' ||\n" )

def emptyLine( f ):
        f.write ( "|| || || || || ||\n"  )

def writeExperiment ( f, db, experiment ):
    experimentHeader ( f, experiment )
    anas = db.getExpResults()

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
        import IPython
        # IPython.embed()
        try:
            comment = ana.globalInfo.comment
        except Exception as e:
            comment = ""
        # print ( comment )
        fastlim = ( "fastlim" in comment )
        topos = set ( map ( str, ana.getTxNames() ) )
        # print ( topos )
        topos_s = ""
        for i in topos:
            topos_s += ", %s" % i
        topos_s = topos_s[2:]
        if fastlim:
            topos_s = "(from fastlim)"
        url = ana.globalInfo.url
        if url.find ( " " ) > 0:
            url = url[:url.find(" ") ]
        f.write ( "|| [[%s|%s]]" % ( url, ana.globalInfo.id ) )
        f.write ( "|| || %s || %d || %s ||\n" % ( 
               ana.globalInfo.lumi.asNumber(), ana.globalInfo.sqrts.asNumber(), topos_s ) )

def main():
    f = open ( "ListOfAnalyses", "w" )
    database = Database ( '../../smodels-database/' )
    header( f, database.databaseVersion )
    print ( "base=", database.databaseVersion )
    experiments=[ "CMS", "ATLAS" ]
    for experiment in experiments:
        writeExperiment ( f, database, experiment )
    xsel()
    
if __name__ == '__main__':
    main()    
