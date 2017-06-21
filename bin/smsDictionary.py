#!/usr/bin/env python

"""
.. module:: smsDictionary
         :synopsis: Small script to produce the SmsDictionary wiki page,
                    see http://smodels.hephy.at/wiki/SmsDictionary

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

from __future__ import print_function
import setPath
from smodels.experiment.databaseObj import Database
import os
try:
    import commands as C
except:
    import subprocess as C

class SmsDictWriter:
    def __init__ ( self, drawFeyn=False, xkcd=False ):
        self.drawFeyn = drawFeyn
        self.xkcd = xkcd
        self.database = None
        self.hasResultsColumn = False
        self.f=open("SmsDictionary","w" )

    def straight( self ):
        return (not self.xkcd)

    def close ( self ):
        self.f.close()

    def header( self ):
        self.f.write (
"""#acl +DeveloperGroup:read,write,revert -All:write +All:read Default

= SMS dictionary =
This page intends to collect information about how we map the SModelS description of
events onto the Tx nomenclature. The list has been created from the database version %s.

There is also a ListOfAnalyses.
""" % self.database.databaseVersion )

    def footer( self ):
        return
        self.f.write (
"""

N.B.: Each "()" group corresponds to a branch

"""
    )

    def tableHeader ( self ):
        # f.write ( '||<tableclass="sortable"> Tx Name || Topology || Graph || Results ||\n' )
        columns=[ "#", "Tx", "Topology", "Graph" ]
        if self.hasResultsColumn:
            columns.append ( "Results" )
        for header in columns:
            self.f.write ( "||<#EEEEEE:> '''%s''' " % header )
        self.f.write ( "||\n" )

    def getTopos( self ):
        topos = {}
        # expresults = database.getExpResults()
        expresults = self.database.expResultList ## also non-validated
        for expRes in expresults:
            for dataset in expRes.datasets:
                for txname in dataset.txnameList:
                    stxname = str ( txname )
                    if txname in topos:
                        if txname.constraint != topos[stxname]:
                            print ( "txnames for %s mismatch: %s != %s" %
                                    ( txname, txname.constraint, topos[stxname] ) )
                    topos[stxname]=txname.constraint
        return topos

    def writeTopos ( self ):
        if not os.path.exists ( "feyn/" ):
            C.getoutput ( "mkdir feyn" )
        topos = writer.getTopos()
        keys = topos.keys()
        keys.sort()
        multipleNames = {}
        for txname in keys:
            constraint = topos[txname]
            if not constraint in multipleNames:
                multipleNames[constraint] = set()
            multipleNames[constraint].add ( txname )

        for ctr,txname in enumerate( keys ):
            constraint = topos[txname]
            txnames = multipleNames [ constraint ]
            if txname == list(txnames)[0]: ## only write if first in line
                self.writeTopo ( ctr+1, txnames, constraint )

    def run ( self ):
        self.header()
        self.tableHeader ()
        self.writeTopos ( )
        self.footer()
        self.close()
        self.xsel()

    def xsel( self ):
        import os
        cmd="cat SmsDictionary | xsel -i"
        os.system ( cmd )
        print ( cmd )

    def createFeynGraph ( self, txname, constraint ):
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
        feynfile="feyn/"+txname+".png"
        print ( "drawing",feynfile,"from",c )
        from smodels.theory import element
        e=element.Element(c)
        feynmanGraph.draw ( e, feynfile, straight=writer.straight(),
                            inparts=True, verbose=False )

    def writeTopo ( self, nr, txnames, constraint ):
        self.f.write ( "||%d||<:>" % nr )
        ltxes = []
        for txname in txnames:
            ltxes.append ( "'''%s'''<<Anchor(%s)>>" % ( txname, txname ) )
        self.f.write ( "<<BR>>".join ( ltxes ) )
        constraint = constraint[constraint.find("["):]
        constraint = constraint.replace( " ", "" )
        if constraint[-1]==")": constraint = constraint[:-1]
        if self.drawFeyn:
            for txname in txnames:
                self.createFeynGraph ( txname, constraint )
        constraint = constraint.replace ( "]+[", "]+`<<BR>>`[" )
        self.f.write ( "||`%s`" % constraint )
        style = "straight"
        if self.xkcd:
            style = "xkcd"
        self.f.write ( '||{{http://smodels.hephy.at/feyn/%s/%s.png||width="150"}}' % ( style, txname ) )
        ## for debugging
        ## self.f.write  ( '{{http://smodels.hephy.at/feyn/xkcd/%s.png||width="150"}}' % txname )
        self.f.write ( "||\n" )

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description='Write Wiki page that lists all SMSes, their constraints, and draws a Feynman graph, see http://smodels.hephy.at/wiki/SmsDictionary')
    argparser.add_argument ( '-f', '--feynman', help='also create Feynman Graphs',
                             action='store_true' )
    argparser.add_argument ( '-x', '--xkcd', help='draw xkcd style (implies -f)',
                             action='store_true' )
    args = argparser.parse_args()
    if args.xkcd:
        args.feynman = True
    writer = SmsDictWriter( drawFeyn = args.feynman, xkcd = args.xkcd )
    writer.database = Database ( "../../smodels-database" )
    print ( "database", writer.database.databaseVersion )
    writer.run()
