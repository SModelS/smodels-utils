#!/usr/bin/env python3

"""
.. module:: smsDictionary
         :synopsis: Small script to produce the SmsDictionary wiki page,
                    see http://smodels.github.io/SmsDictionary.
                    New markdown syntax.

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
    def __init__ ( self, database, drawFeyn, xkcd, results, addVer, private ):
        self.databasePath = database
        self.drawFeyn = drawFeyn
        self.xkcd = xkcd
        self.database = Database ( database )
        self.ver=self.database.databaseVersion.replace(".","")
        self.private = private
        # self.ver="v"+self.database.databaseVersion.replace(".","")
        if not addVer:
            self.ver=""
        self.hasResultsColumn = results
        self.fname = "SmsDictionary%s" % self.ver
        self.f=open(self.fname,"w" )

    def straight( self ):
        return (not self.xkcd)

    def close ( self ):
        self.f.close()

    def header( self ):
        protected = "+All:read"
        if self.private:
            protected = "-All:read"
        self.f.write (
"""

# SMS dictionary
This page intends to collect information about how we map the SModelS description of
events onto the Tx nomenclature. The list has been created from the database version %s, considering also superseded results.

There is also a [ListOfAnalyses%s](https://smodels.github.io/docs/ListOfAnalyses%s), a [ListOfAnalyses%sWithSuperseded](https://smodels.github.io/docs/ListOfAnalysesWithSuperseded%s), and [Validation%s](Validation%s).

""" % ( self.database.databaseVersion, self.ver, self.ver, self.ver, self.ver, self.ver, self.ver ) )

    def footer( self ):
        return
        self.f.write (
"""

N.B.: Each "()" group corresponds to a branch

"""
    )

    def tableHeader ( self ):
        columns=[ "#", "Tx", "Topology", "Graph" ]
        if self.hasResultsColumn:
            columns.append ( "Appears in" )
        lengths=[]
        for header in columns:
            #self.f.write ( "|<#EEEEEE:> **%s** " % header )
            self.f.write ( "| **%s** " % header )
            lengths.append ( len(header)+4 )
        self.f.write ( "|\n" )
        for l in lengths:
            self.f.write ( "| "+"-"*l+ " " )
        self.f.write ( "|\n" )
        

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
        ret = "%s`<BR>`(%s)" % (constr, ", ".join ( fs ) )
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
        if not os.path.exists ( "../feyn/" ):
            C.getoutput ( "mkdir ../feyn" )
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
        cmd="cat %s | xsel -i" % self.fname
        os.system ( cmd )
        print ( cmd )
        cmd="cp %s ../../smodels.github.io/docs/%s.md" % ( self.fname, self.fname )
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
        feynfile="../feyn/"+txname+".png"
        sfstate = str(fstate).replace(" ","").replace("'","")
        print ( "[smsDictionary.py] draw",feynfile,"from",c,"with",sfstate )
        exe = "../smodels_utils/plotting/feynmanGraph.py -i "
        cmd = exe
        if writer.straight():
            cmd += " -s"
        br = c.find("<BR")
        constr = c[:br]
        cmd += ' -c "%s"' % constr
        cmd += " -f '%s'" % str(fstate).replace("[","(").replace("]",")").replace("'",'"')
        cmd += " -o %s" % feynfile
        a = C.getoutput ( cmd )
        """ nicer way, just doesnt clear the canvas in bulk mode
        from smodels.theory import element
        try:
            e=element.Element(c,fstate )
        except:
            e=element.Element(c)
        drawer = feynmanGraph.Drawer ( e, verbose=False )
        drawer.draw ( feynfile, straight=writer.straight(), inparts=True )
        """

    def writeTopo ( self, nr, txnames, constraint, first ):
        """ :param first: is this the first time I write a topo? """
        # self.f.write ( "| %d | <:>" % nr )
        self.f.write ( "| %d | " % nr )
        ltxes = []
        for txname in txnames:
            txnameabb = txname
            if len ( txnameabb ) > 8:
                pos = 8
                unabbrv = [ "tau", "off", "Chim", "Chip", "Slep" ]
                for ua in unabbrv:
                    if txnameabb.find ( ua ) in [6,7,9]:
                        pos = txnameabb.find ( ua )
                txnameabb=txnameabb[:pos]+"-<br>"+txnameabb[pos:]
            ltxes.append ( '<a name="%s"></a>**%s**<br>' % ( txname, txnameabb ) )
            # ltxes.append ( '<a name="%s"><b>%s</b></a>' % ( txname, txname ) )
        self.f.write ( "<BR>".join ( ltxes ) )
        constraint = constraint[constraint.find("["):]
        constraint = constraint.replace( " ", "" )
        constraint = constraint.replace ( "jet", "q" )
        constraint = constraint.replace ( "photon", "y" )
        constraint = constraint.replace ( "higgs", "h" )
        # if constraint[-1]==")": constraint = constraint[:-1]
        if self.drawFeyn:
            for txname in txnames:
                self.createFeynGraph ( txname, constraint )
        constraint = constraint.replace ( "]+[", "]+`<BR>`[" )
        constraint = constraint.replace ( ";",";`<BR>`" )
        constraint = "`" + constraint + "`"
        #if len(constraint)>20:
        #    print ( "constraint", constraint )
        #    constraint = constraint[:20]+"`<BR>`"+constraint[20:]
        self.f.write ( " | %s" % constraint ) ## "Topology" column
        style = "straight"
        if self.xkcd:
            style = "xkcd"
        ## now "Graph" column
        self.f.write ( ' | ![%s](../feyn/%s/%s.png)' % ( txname, style, txname ) )
        ## now "Appears in" column
        if self.hasResultsColumn:
            self.f.write ( " | " )
            results = self.database.getExpResults ( txnames = txnames, useSuperseded = True )
            if first:
                # self.f.write ( "<25%>" ) ## make sure the last column isnt too small
                pass
            if len(results)>9:
                self.f.write ( "[many (%d)](ListOfAnalyses%s)" % (len(results),self.ver) )
            else:
                l = []
                hi = [] ## remove dupes
                for res in results:
                    ID = res.globalInfo.id
                    ID = ID.replace("-agg","" )
                    if ID in hi:
                        continue
                    #ID = ID.replace("CMS-","**C**-" )
                    #ID = ID.replace("ATLAS-","**A**-" )
                    hi.append ( ID )
                    supers = ""
                    if hasattr ( res.globalInfo, "supersededBy" ):
                        supers="WithSuperseded"
                    l.append ( "[%s](ListOfAnalyses%s%s#%s)" % ( ID, self.ver, supers, ID ) )
                self.f.write ( "<BR>".join ( l ) )
        self.f.write ( "|\n" )

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description='Write Wiki page that lists all SMSes, their constraints, and draws a Feynman graph, see http://smodels.hephy.at/wiki/SmsDictionary')
    argparser.add_argument ( '-f', '--feynman', help='also create Feynman Graphs',
                             action='store_true' )
    argparser.add_argument ( '-x', '--xkcd', help='draw xkcd style (implies -f)',
                             action='store_true' )
    argparser.add_argument ( '-u', '--upload', help='upload create Feynman graphs (implies -f)',
                             action='store_true' )
    argparser.add_argument ( '-p', '--private', help='declare as private (add wiki acl line on top)', action='store_true' )
    argparser.add_argument ( '-r', '--results', help='dont add results column',
                             action='store_false' )
    argparser.add_argument ( '-d', '--database', help='path to database [../../smodels-database]',
                             type=str, default='../../smodels-database' )
    argparser.add_argument ( '-a', '--add_version',
            help='add version labels to links', action='store_true' )
    args = argparser.parse_args()
    if args.xkcd:
        args.feynman = True
    writer = SmsDictWriter( database=args.database, drawFeyn = args.feynman,
            xkcd = args.xkcd, results = args.results, addVer = args.add_version,
            private = args.private  )
    print ( "[smsDictionary.py] Database", writer.database.databaseVersion )
    writer.run()
    if args.upload:
        import socket
        hostname = socket.gethostname()
        dest="straight"
        if args.xkcd:
            dest="xkcd"
        cmd = "cp ../feyn/T*p* /var/www/feyn/%s/" % dest
        if hostname == "smodels":
            print ( "WARNING: made the plots on smodels, via X tunneling. this may create problems (a bug in pyfeyn?). Check the plots! Or make the plots from your desktop." )
        if hostname != "smodels":
            cmd = "scp ../feyn/T*p* smodels.hephy.at:/var/www/feyn/%s/" % dest
        import subprocess
        print ( cmd )
        a = subprocess.getoutput ( cmd )
        print ( a )
