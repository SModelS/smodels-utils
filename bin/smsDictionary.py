#!/usr/bin/env python3

"""
.. module:: smsDictionary
         :synopsis: Small script to produce the SmsDictionary wiki page,
                    see http://smodels.hephy.at/wiki/SmsDictionary

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

## python2 needed because of pyfeyn!

from __future__ import print_function
import setPath
from smodels.experiment.databaseObj import Database
import os
try:
    import commands as C
except:
    import subprocess as C

class SmsDictWriter:
    def __init__ ( self, database, drawFeyn, xkcd, results, addVer ):
        self.databasePath = database
        self.drawFeyn = drawFeyn
        self.xkcd = xkcd
        self.database = Database ( database )
        self.ver="v"+self.database.databaseVersion.replace(".","")
        if not addVer:
            self.ver=""
        self.hasResultsColumn = results
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
events onto the Tx nomenclature. The list has been created from the database version %s, considering also superseded results.

There is also a ListOfAnalyses%s, and a ListOfAnalyses%sWithSuperseded.
""" % (self.database.databaseVersion, self.ver, self.ver ) )

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
            columns.append ( "Appears in" )
        for header in columns:
            self.f.write ( "||<#EEEEEE:> '''%s''' " % header )
        self.f.write ( "||\n" )

    def cleanUp ( self, txname ):
        constr = txname.constraint
        pos = constr.find("*")
        pos2 = constr.find("[")
        if pos > 0 and pos2 > pos:
            constr = constr[pos+1:]
        constr=constr.replace("(","").replace(")","")
        fs = [ "MET", "MET" ]
        if hasattr ( txname, "finalState" ):
            fs = txname.finalState
        ret = "%s`<<BR>>`(%s)" % (constr, ", ".join ( fs ) )
        return ret

    def getTopos( self ):
        topos = {}
        expresults = self.database.getExpResults( useSuperseded=True )
        #expresults = self.database.expResultList ## also non-validated
        for expRes in expresults:
            for dataset in expRes.datasets:
                for txname in dataset.txnameList:
                    stxname = str ( txname )
                    if txname in topos:
                        if txname.constraint != topos[stxname]:
                            print ( "txnames for %s mismatch: %s != %s" %
                                    ( txname, txname.constraint, topos[stxname] ) )
                    if not stxname in topos.keys():
                        topos[stxname]=set()
                    con =  self.cleanUp ( txname )
                    topos[stxname].add ( con )
        for k,v in topos.items():
            topos[k]="; ".join ( v )
        return topos

    def writeTopos ( self ):
        if not os.path.exists ( "feyn/" ):
            C.getoutput ( "mkdir feyn" )
        topos = writer.getTopos()
        keys = list ( topos.keys() )
        keys.sort()
        multipleNames = {}
        for txname in keys:
            constraint = topos[txname]
            if not constraint in multipleNames:
                multipleNames[constraint] = set()
            multipleNames[constraint].add ( txname )

        first=True

        for ctr,txname in enumerate( keys ):
            constraint = topos[txname]
            txnames = multipleNames [ constraint ]
            if txname == list(txnames)[0]: ## only write if first in line
                self.writeTopo ( ctr+1, txnames, constraint, first )
                first = False

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
        from smodels_utils.plotting import feynmanGraph
        fstate=["MET","MET"]
        p=constraint.find(";")
        if p>-1:
            constraint=constraint[:p]
        c=constraint
        p=c.find("<<BR>>" )
        if p>-1:
            c=c[:p]
            fstate = eval ( constraint[p+7:].replace("(","['").replace(")","']").replace(",","','") )
        p=c.find("]+")
        if p>-1:
            c=c[:p+1]
        p=c.find("] +")
        if p>-1:
            c=c[:p+1]
        c=c.replace("71.*","").replace("(","").replace(")","").replace("`","")
        feynfile="feyn/"+txname+".png"
        print ( "drawing",feynfile,"from",c,"with final state",fstate )
        from smodels.theory import element
        try:
            e=element.Element(c,fstate )
        except:
            e=element.Element(c)
        drawer = feynmanGraph.Drawer ( e, verbose=False )
        drawer.draw ( feynfile, straight=writer.straight(), inparts=True )

    def writeTopo ( self, nr, txnames, constraint, first ):
        """ :param first: is this the first time I write a topo? """
        self.f.write ( "||%d||<:>" % nr )
        ltxes = []
        for txname in txnames:
            ltxes.append ( "'''%s'''<<Anchor(%s)>>" % ( txname, txname ) )
        self.f.write ( "<<BR>>".join ( ltxes ) )
        constraint = constraint[constraint.find("["):]
        constraint = constraint.replace( " ", "" )
        # if constraint[-1]==")": constraint = constraint[:-1]
        if self.drawFeyn:
            for txname in txnames:
                self.createFeynGraph ( txname, constraint )
        constraint = constraint.replace ( "]+[", "]+`<<BR>>`[" )
        self.f.write ( "||`%s`" % constraint ) ## "Topology" column
        style = "straight"
        if self.xkcd:
            style = "xkcd"
        ## now "Graph" column
        self.f.write ( '||{{http://smodels.hephy.at/feyn/%s/%s.png||width="200"}}' % ( style, txname ) )
        ## now "Appears in" column
        if self.hasResultsColumn:
            self.f.write ( "||" )
            results = self.database.getExpResults ( txnames = txnames, useSuperseded = True )
            if first:
                self.f.write ( "<25%>" ) ## make sure the last column isnt too small
            if len(results)>9:
                self.f.write ( "[[ListOfAnalyses%s|many (%d)]]" % (self.ver,len(results)) )
            else:
                l = []
                hi = [] ## remove dupes
                for res in results:
                    ID = res.globalInfo.id
                    if ID in hi:
                        continue
                    hi.append ( ID )
                    supers = ""
                    if hasattr ( res.globalInfo, "supersededBy" ):
                        supers="WithSuperseded"
                    l.append ( "[[ListOfAnalyses%s%s#%s|%s]]" % ( self.ver, supers, ID, ID ) )
                self.f.write ( "<<BR>>".join ( l ) )
        self.f.write ( "||\n" )

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description='Write Wiki page that lists all SMSes, their constraints, and draws a Feynman graph, see http://smodels.hephy.at/wiki/SmsDictionary')
    argparser.add_argument ( '-f', '--feynman', help='also create Feynman Graphs',
                             action='store_true' )
    argparser.add_argument ( '-x', '--xkcd', help='draw xkcd style (implies -f)',
                             action='store_true' )
    argparser.add_argument ( '-u', '--upload', help='upload create Feynman graphs (implies -f)',
                             action='store_true' )
    argparser.add_argument ( '-r', '--results', help='dont add results column',
                             action='store_false' )
    argparser.add_argument ( '-d', '--database', help='path to database',
                             type=str, default='../../smodels-database' )
    argparser.add_argument ( '-v', '--version',
            help='dont add version labels to links', action='store_false' )
    args = argparser.parse_args()
    if args.xkcd:
        args.feynman = True
    writer = SmsDictWriter( database=args.database, drawFeyn = args.feynman,
            xkcd = args.xkcd, results = args.results, addVer = args.version )
    print ( "database", writer.database.databaseVersion )
    writer.run()
    if args.upload:
        import socket
        hostname = socket.gethostname()
        dest="straight"
        if args.xkcd:
            dest="xkcd"
        cmd = "cp feyn/T*p* /var/www/feyn/%s/" % dest
        if hostname != "smodels":
            cmd = "scp feyn/T*p* smodels.hephy.at:/var/www/feyn/%s/" % dest
        import subprocess
        print ( cmd )
        a = subprocess.getoutput ( cmd )
        print ( a )
