#!/usr/bin/env python

"""
.. module:: smsDictionary
         :synopsis: Small script to produce the SmsDictionary wiki page

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

from __future__ import print_function
import setPath
from smodels.experiment.databaseObj import Database

def header( f, version ):

### It has been created with the 
### [[http://smodels.hephy.at/gitweb/?p=smodels-utils.git;a=blob;f=bin/smsDictionary.py;h=25451211ccf1d38e98c34b9d42e44deb39c6d6ea;hb=refs/heads/develop|smsDictionary.py]] tool. 

    f.write ( 
##"""#acl +DeveloperGroup:read,write,revert -All:write,read Default 
## <<LockedPage()>>
"""#acl +DeveloperGroup:read,write,revert -All:write +All:read Default 

= SMS dictionary =
This page intends to collect information about how we map the SModelS description of 
events onto the Tx nomenclature. It has been created with the 
[[http://smodels.hephy.at/gitweb/?p=smodels-utils.git;a=blob;f=bin/smsDictionary.py;h=25451211ccf1d38e98c34b9d42e44deb39c6d6ea;hb=refs/heads/develop|smsDictionary.py]] tool. 

The list has been created from the database version %s.

There is also a ListOfAnalyses.

""" % version )

def footer( f ):
    f.write (
"""

N.B.: Each "()" group corresponds to a branch

"""
)

def xsel():
    import os
    cmd="cat SmsDictionary | xsel -i"
    os.system ( cmd )
    print ( cmd )

def getTopos( database ):
    topos = {}
    for expRes in database.getExpResults():
        for dataset in expRes.datasets:
            for txname in dataset.txnameList:
                stxname = str ( txname )
                if txname in topos:
                    if txname.constraint != topos[stxname]:
                        print ( "txnames for %s mismatch: %s != %s" % 
                                ( txname, txname.constraint, topos[stxname] ) )
                topos[stxname]=txname.constraint
    return topos
    
hasResultsColumn = False

def tableHeader ( f ):    
    # f.write ( '||<tableclass="sortable"> Tx Name || Topology || Graph || Results ||\n' )
    columns=[ "#", "Tx", "Topology", "Graph" ]
    if hasResultsColumn:
        columns.append ( "Results" )
    for header in columns:
        f.write ( "||<#EEEEEE:> '''%s''' " % header )
    f.write ( "||\n" )

def createFeynGraph ( txname, constraint ):
    # return
    from smodels_utils.plotting import feynmanGraph
    c=constraint
    p=c.find("]+")
    if p>-1:
        c=c[:p+1]
    p=c.find("] +")
    if p>-1:
        c=c[:p+1]
    c=c.replace("71.*","").replace("(","").replace(")","")
    feynfile=txname+"_feyn.png"
    print ( "drawing",feynfile,"from",c )
    from smodels.theory import element
    e=element.Element(c)
    feynmanGraph.draw ( e, feynfile, straight=False, inparts=True, verbose=False )
    print ( "done drawing." )

def writeTopo ( f, nr, txname, constraint ):
    f.write ( "||%d||<:>'''%s'''<<Anchor(%s)>>" % ( nr, txname, txname ) )
    constraint = constraint[constraint.find("["):]
    constraint = constraint.replace( " ", "" )
    if constraint[-1]==")": constraint = constraint[:-1]
    createFeynGraph ( txname, constraint )
    constraint = constraint.replace ( "]+[", "]+`<<BR>>`[" )
    f.write ( "||`%s`" % constraint ) 
    f.write ( '||{{http://smodels.hephy.at/feyn/%s_feyn.png||width="150"}}' % txname )
    f.write ( "||\n" )

def writeTopos ( f, topos ):
    keys = topos.keys()
    keys.sort()
    for ctr,txname in enumerate( keys ):
        constraint = topos[txname]
        writeTopo ( f, ctr+1, txname, constraint )

def main():
    f=open("SmsDictionary","w" )
    database = Database ( "../../smodels-database" )
    print ( "database",database.databaseVersion )
    topos = getTopos ( database )
    header( f, database.databaseVersion )
    tableHeader ( f )
    writeTopos ( f, topos )
    footer( f )
    f.close()
    xsel()

if __name__ == '__main__':
    main()    
