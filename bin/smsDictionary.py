#!/usr/bin/env python3

"""
.. module:: smsDictionary
         :synopsis: Small script to produce the SmsDictionary wiki page,
                    see http://smodels.github.io/SmsDictionary.
                    New markdown syntax.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

## python2 needed because of pyfeyn!

# from __future__ import print_function
import setPath
from smodels.experiment.databaseObj import Database
from smodels_utils.helper.various import removeAnaIdSuffices
import os, time

try:
    import commands as C
except:
    import subprocess as C

class SmsDictWriter:
    feynpath = "../../smodels.github.io/feyn/straight/"

    def __init__ ( self, database, drawFeyn, xkcd, results, addVer, private,
                   dryrun, checkfirst, copy ):
        self.databasePath = database
        self.hasWarned=False
        self.drawFeyn = drawFeyn
        self.dryrun =  dryrun
        self.copy = copy
        self.xkcd = xkcd
        self.checkfirst = checkfirst
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
"""# SMS dictionary
This page intends to collect information about how we map the SModelS description of
events onto the Tx nomenclature. The list has been created from the database version %s, considering also superseded results.

There is also a [ListOfAnalyses%s](https://smodels.github.io/docs/ListOfAnalyses%s), a [ListOfAnalyses%sWithSuperseded](https://smodels.github.io/docs/ListOfAnalyses%sWithSuperseded), and [Validation%s](Validation%s).

""" % ( self.database.databaseVersion, self.ver, self.ver, self.ver, self.ver, self.ver, self.ver ) )

    def footer( self ):
        self.f.write ( "\n<font color='grey'>This page was created %s</font>\n" % \
                       time.asctime() )
        return

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
        expresults.sort()
        for expRes in expresults:
            datasets = expRes.datasets
            datasets.sort( key = lambda x: str(x) )
            for dataset in datasets:
                txnames = dataset.txnameList
                txnames.sort()
                for txname in txnames:
                    stxname = str ( txname )
                    if txname in topos:
                        if txname.constraint != topos[stxname]:
                            print ( "[smsDictionary] txnames for %s mismatch: %s != %s" %
                                    ( txname, txname.constraint, topos[stxname] ) )
                    if not stxname in topos.keys():
                        topos[stxname]=set()
                    con =  self.cleanUp ( txname )
                    topos[stxname].add ( con )
        keys = list(topos.keys())
        keys.sort()
        for k in keys:
            v = topos[k]
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

        i=0
        for _,txname in enumerate( keys ):
            constraint = topos[txname]
            txnames = multipleNames [ constraint ]
            if txname == list(txnames)[0]: ## only write if first in line
                i+=1
                self.writeTopo ( i, txnames, constraint, first )
                first = False

    def run ( self ):
        self.header()
        self.tableHeader ()
        self.writeTopos ( )
        self.footer()
        self.close()
        self.move()

    def move( self ):
        cmd="mv %s ../../smodels.github.io/docs/%s.md" % ( self.fname, self.fname )
        os.system ( cmd )
        print ( cmd )


    def createFeynGraph ( self, txname, constraint ):
        fcon = constraint
        constrs = fcon.split ( ";" )
        fstate=["MET","MET"]
        print ( "[smsDictionary] createFeynGraph", txname, fstate, constraint )
        c = constrs[0]
        for i in constrs:
            if len(i)<len(c):
                c=i
        # print ( "[smsDictionary] shortest constraint for",txname,"is",c )
        p=constraint.find("<<BR>>" )
        p7=p+7
        if p == -1:
            p=constraint.find("<BR>" )
            p7 = p + 5
        if p>-1:
            c=c[:p]
            lastc = len(constraint)
            if ";" in constraint:
                lastc=constraint.find(";")
            # print ( "constraint %s " % constraint, "p7", p7, "lastc", lastc, "p", p )
            # print ( "fs",constraint[p7:lastc] )
            fstate = eval ( constraint[p7:lastc].replace("(","['").replace(")","']").replace(",","','") )
        feynfile="../feyn/"+txname+".png"
        sfstate = str(fstate).replace(" ","").replace("'","")
        print ( "[smsDictionary] draw",feynfile,"from",c,"with",sfstate,"(full constraint reads",fcon,")" )
        exe = "../smodels_utils/plotting/feynmanGraph.py -i "
        cmd = exe
        if writer.straight():
            cmd += " -s"
        br = c.find("<BR")
        constr = c[:br].replace("`","")
        cmd += ' -c "%s"' % constr
        #if txname == "T5Disp":
        #    cmd += ' -L "[[0],[0]]"'
        cmd += " -f '%s'" % str(fstate).replace("[","(").replace("]",")").replace("'",'"')
        cmd += " -o %s" % feynfile
        print ( "[smsDictionary]", cmd )
        if not self.dryrun:
            a = C.getoutput ( cmd )
            print ( "  `-",a )

    def writeTopo ( self, nr, txnames, constraint, first ):
        """ :param first: is this the first time I write a topo? """
        # self.f.write ( "| %d | <:>" % nr )
        self.f.write ( "| %d | " % nr )
        ltxes = []
        for txname in txnames:
            txnameabb = txname
            if len ( txnameabb ) > 9:
                pos = 8
                unabbrv = [ "tau", "off", "Chim", "Chip", "Slep", "Stau" ]
                for ua in unabbrv:
                    if txnameabb.find ( ua ) in [6,7,9]:
                        pos = txnameabb.find ( ua )
                txnameabb=txnameabb[:pos]+"-<br>"+txnameabb[pos:]
            ltxes.append ( '<a name="%s"></a>**%s**<br>' % ( txname, txnameabb ) )
            # ltxes.append ( '<a name="%s"><b>%s</b></a>' % ( txname, txname ) )
        self.f.write ( "<BR>".join ( ltxes ) )
        constraint = constraint[constraint.find("["):]
        constraint = constraint.replace( " ", "" )
        # constraint = constraint.replace ( "jet", "q" )
        if self.drawFeyn:
            for txname in txnames:
                exists = os.path.exists ( f"{SmsDictWriter.feynpath}/{txname}.png" )
                if not self.checkfirst and self.copy and exists and not self.hasWarned:
                    print ( f"[smsDictionary] WARNING: will overwrite {SmsDictWriter.feynpath}/{txname}.png" )
                    print ( "[smsDictionary] use -s if that is not what you wanted" )
                    self.hasWarned = True
                if self.checkfirst and exists:
                    print ( "[smsDictionary] skipping %s.png" % txname )
                    if self.hasWarned == False:
                        self.hasWarned=True
                        print ( "[smsDictionary] (it exists already and you specified to skip existing graphs. if that is not what you want, do not use -s)." )
                    continue
                self.createFeynGraph ( txname, constraint )
        constraint = constraint.replace ( "photon", "y" )
        constraint = constraint.replace ( "higgs", "h" )
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
        # self.f.write ( ' | ![%s](../feyn/%s/%s.png)' % ( txname, style, txname ) )
        self.f.write ( ' | <img alt="%s" src="../feyn/%s/%s.png" height="130">' % ( txname, style, txname ) )
        ## now "Appears in" column
        if self.hasResultsColumn:
            self.f.write ( " | " )
            results = self.database.getExpResults ( txnames = txnames )
            if first:
                # self.f.write ( "<25%>" ) ## make sure the last column isnt too small
                pass
            if len(results)>9:
                self.f.write ( "[many (%d)](ListOfAnalyses%sWithSuperseded)" % (len(results),self.ver) )
            else:
                l = []
                hi = [] ## remove dupes
                for res in results:
                    ID = removeAnaIdSuffices ( res.globalInfo.id )
                    if ID in hi:
                        continue
                    #ID = ID.replace("CMS-","**C**-" )
                    #ID = ID.replace("ATLAS-","**A**-" )
                    hi.append ( ID )
                    supers = ""
                    if hasattr ( res.globalInfo, "supersededBy" ):
                        supers="WithSuperseded"
                    # lets got
                    l.append ( "[%s](%s)" % ( ID, res.globalInfo.url ) )
                    # before we had a link to the entry at ListOfAnalyses
                    # l.append ( "[%s](ListOfAnalyses%s%s#%s)" % ( ID, self.ver, supers, ID ) )
                self.f.write ( "<BR>".join ( l ) )
        self.f.write ( "|\n" )

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description='Write Wiki page that lists all SMSes, their constraints, and draws a Feynman graph, see http://smodels.hephy.at/wiki/SmsDictionary')
    argparser.add_argument ( '-f', '--feynman', help='also create Feynman Graphs',
                             action='store_true' )
    argparser.add_argument ( '-s', '--checkfirst', help=f'create only Feynman Graphs that do not exist in {SmsDictWriter.feynpath}',
                             action='store_true' )
    argparser.add_argument ( '-x', '--xkcd', help='draw xkcd style (implies -f)',
                             action='store_true' )
    argparser.add_argument ( '-D', '--dry_run', help='dry run, dont actually draw',
                             action='store_true' )
    argparser.add_argument ( '-c', '--copy', help='copy Feynman graphs to ../../smodels.github.io/feyn/straight/ (implies -f)',
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
            private = args.private, dryrun = args.dry_run,
            checkfirst = args.checkfirst, copy = args.copy )
    print ( "[smsDictionary] Database", writer.database.databaseVersion )
    writer.run()
    if args.copy:
        dest="straight"
        if args.xkcd:
            dest="xkcd"
        cmd = f"cp ../feyn/T*.p* {SmsDictWriter.feynpath}"
        import subprocess
        print ( "[smsDictionary] %s" % cmd )
        a = subprocess.getoutput ( cmd )
        if len(a)>0:
            print ( "[smsDictionary] error: %s" % a )
