#!/usr/bin/env python3

"""
.. module:: smsDictionary
         :synopsis: Small script to produce the SmsDictionary wiki page,
                    see http://smodels.github.io/SmsDictionary.
                    New markdown syntax.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

import setPath
from smodels.experiment.databaseObj import Database
from smodels.experiment.txnameObj import TxName
from smodels_utils.helper.various import removeAnaIdSuffices
import os, time

try:
    import commands as C
except:
    import subprocess as C

class SmsDictWriter:
    smsgraphpath = "../../smodels.github.io/smsgraphs/"

    def __init__ ( self, database, drawSMSGraphs, results, addVer,
                   dryrun, checkfirst, copy, ignoreValidated ):
        self.databasePath = database
        self.constraintsToTxNames = {}
        self.hasWarned=False
        self.ignoreValidated = ignoreValidated
        self.drawSMSGraphs = drawSMSGraphs
        self.dryrun =  dryrun
        self.copy = copy
        self.checkfirst = checkfirst
        self.database = Database ( database )
        self.ver=self.database.databaseVersion.replace(".","")
        # self.ver="v"+self.database.databaseVersion.replace(".","")
        if not addVer:
            self.ver=""
        self.hasResultsColumn = results
        self.fname = f"SmsDictionary{self.ver}"
        self.f=open(self.fname,"w" )

    def close ( self ):
        self.f.close()

    def header( self ):
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
        columns=[ "#", "Tx", "Process", "SMS Graph" ]
        if self.hasResultsColumn:
            columns.append ( "Appears in" )
        lengths=[]
        for header in columns:
            #self.f.write ( "|<#EEEEEE:> **%s** " % header )
            self.f.write ( f"| **{header}** " )
            lengths.append ( len(header)+4 )
        self.f.write ( "|\n" )
        for l in lengths:
            self.f.write ( "| "+"-"*l+ " " )
        self.f.write ( "|\n" )

    def getConstraint ( self, txname : TxName ) -> str:
        """ given a txname object, retrieve the constraint """
        constraints = list ( map ( str, list ( txname.smsMap.keys() ) ) )
        tmp = []
        for c in constraints:
            tmp.append ( c.replace(", (",",`<BR> &rarr;`(" ) )
        constr = "`<BR><BR>`".join ( tmp )
        txn = txname.txName
        if not txn in self.constraintsToTxNames:
            self.constraintsToTxNames[txn]={}
        self.constraintsToTxNames[txn][constr]=txname
        return constr

    def getAllTopologies( self ) -> dict:
        """ get the txnames and their constraints """
        topos = {}
        expresults = self.database.getExpResults( )
        if self.ignoreValidated:
            expresults = self.database.expResultList ## also non-validated
        expresults.sort()
        for expRes in expresults:
            datasets = expRes.datasets
            datasets.sort( key = lambda x: str(x) )
            for dataset in datasets:
                txnames = dataset.txnameList
                txnames.sort()
                for txname in txnames:
                    tx = str ( txname ) # e.g. T1
                    con = self.getConstraint ( txname )
                    if txname in topos:
                        if con != topos[stxname]:
                            print ( f"[smsDictionary] txnames for {txname} mismatch: {txname.constraint} != {topos[stxname]}" )
                    if not con in topos.keys():
                        topos[tx]=set()
                    topos[tx].add ( con )
        keys = list(topos.keys())
        keys.sort()
        for k in keys:
            v = topos[k]
            topos[k]="; ".join ( v )
        # import IPython ; IPython.embed ( colors="neutral" ) ; import sys; sys.exit()
        return topos

    def writeAllTopologies ( self ):
        """ write the table with all topologies (Tx names) """
        if not os.path.exists ( "../smsgraphs/" ):
            C.getoutput ( "mkdir ../smsgraphs" )
        topos = writer.getAllTopologies()
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
                self.writeOneTopology ( i, txnames, constraint, first )
                first = False

    def run ( self ):
        self.header()
        self.tableHeader ()
        self.writeAllTopologies ( )
        self.footer()
        self.close()
        self.move()

    def move( self ):
        cmd=f"mv {self.fname} ../../smodels.github.io/docs/{self.fname}.md"
        os.system ( cmd )
        print ( cmd )

    def createSmsGraph ( self, txname, constraint ):
        """ create the sms graphs, store them in ../smsgraphs/ """
        print ( f"[smsDictionary] creating {txname}" )
        pathbase = f"../smsgraphs/{txname}"
        smsMap = self.constraintsToTxNames[txname][constraint].smsMap
        for mp,name in smsMap.items():
            path = f"{pathbase}_{name.replace('sms_','')}.png"
            # print ( f"plotting {txname} {constraint} to {path} {name}" )
            import shutil
            if shutil.which ( "convert" ):
                tmp = "/dev/shm/tmp.png"
                mp.draw(filename=tmp,view=False)
                cmd = f"convert {tmp} -transparent white {path}"
                import subprocess
                subprocess.getoutput ( cmd )
            else:
                mp.draw(filename=path,view=False)
        # import sys; sys.exit()

    def createEntriesForTopology ( self, nr : int, txnames : set[str],
            constraint : str ) -> list:
        """ create a list corresponding to the elements in the entry
            of the table for one topology """
        #print ( f"FIXME adapt the topology names!!!" )
        #print ( f"write topology with {constraint}" )
        entries = [ nr ]
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
            ltxes.append ( f'<a name="{txname}"></a>**{txnameabb}**<br>' )
        entries.append ( "<BR>".join ( ltxes ) )
        # FIXME v3
        if self.drawSMSGraphs:
            for txname in txnames:
                ext = 1
                pngpath = f"{SmsDictWriter.smsgraphpath}/{txname}_{ext}.png"
                exists = os.path.exists ( pngpath )
                if not self.checkfirst and self.copy and exists and not self.hasWarned:
                    print ( f"[smsDictionary] WARNING: will overwrite {SmsDictWriter.smsgraphpath}/{txname}.png" )
                    print ( "[smsDictionary] use -s if that is not what you wanted" )
                    self.hasWarned = True
                if self.checkfirst and exists:
                    print ( f"[smsDictionary] skipping {pngpath}" )
                    if self.hasWarned == False:
                        self.hasWarned=True
                        print ( "[smsDictionary] (it exists already and you specified to skip existing graphs. if that is not what you want, do not use -s)." )
                    continue
                self.createSmsGraph ( txname, constraint )
        # shortnames = { "photon": "y", "higgs": "h" }
        shortnames = { } #
        maps = self.constraintsToTxNames[txname][constraint].smsMap
        for k,v in shortnames.items():
            constraint = constraint.replace( k, v )
        constraint = "`" + constraint + "`"
        entries.append ( constraint ) # "Topology" column
        images = ""
        for i in range ( len(maps) ):
            images += f'<img alt="{txname}_{i+1}" src="../smsgraphs/{txname}_{i+1}.png"><BR>'
            # images += f'<img alt="{txname}_{i+1}" src="../smsgraphs/{txname}_{i+1}.png" height="130"><BR>'
        entries.append ( images ) # "Graph" column

        if self.hasResultsColumn:
            results = self.database.getExpResults ( txnames = txnames )
            if len(results)>9:
                entries.append ( f"[many ({len(results)})](ListOfAnalyses{self.ver}WithSuperseded)" )
            else:
                l = []
                hi = [] ## remove dupes
                for res in results:
                    ID = removeAnaIdSuffices ( res.globalInfo.id )
                    if ID in hi:
                        continue
                    hi.append ( ID )
                    supers = ""
                    if hasattr ( res.globalInfo, "supersededBy" ):
                        supers="WithSuperseded"
                    # lets got
                    l.append ( f"[{ID}]({res.globalInfo.url})" )
                    # before we had a link to the entry at ListOfAnalyses
                    # l.append ( "[%s](ListOfAnalyses%s%s#%s)" % ( ID, self.ver, supers, ID ) )
                entries.append ( "<BR>".join ( l ) ) ## "Appears in" column
        return entries

    def writeOneTopology ( self, nr : int, txnames : set[str], constraint : str,
            first : bool ) -> None:
        """ :param first: is this the first time I write a topo? """
        elements = self.createEntriesForTopology ( nr, txnames, constraint )
        for element in elements:
            self.f.write ( f"| {element} " )
        self.f.write ( "|\n" )

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description='Write Wiki page that lists all SMSes, their constraints, and draws a SMS graph, see http://smodels.github.io/docs/SmsDictionary')
    argparser.add_argument ( '-g', '--smsgraphs', help='also create SMS Graphs',
                             action='store_true' )
    argparser.add_argument ( '-s', '--checkfirst', help=f'create only SMS Graphs that do not exist in {SmsDictWriter.smsgraphpath}',
                             action='store_true' )
    argparser.add_argument ( '-D', '--dry_run', help='dry run, dont actually draw',
                             action='store_true' )
    argparser.add_argument ( '-c', '--copy', help='copy SMS graphs to ../../smodels.github.io/smsgraphs/ (implies -g)',
                             action='store_true' )
    argparser.add_argument ( '-r', '--results', help='dont add results column',
                             action='store_false' )
    argparser.add_argument ( '-i', '--ignoreValidated', help='dont add results column',
                             action='store_false' )
    argparser.add_argument ( '-d', '--database', help='path to database [../../smodels-database]',
                             type=str, default='../../smodels-database' )
    argparser.add_argument ( '-a', '--add_version',
            help='add version labels to links', action='store_true' )
    args = argparser.parse_args()
    writer = SmsDictWriter( database=args.database, drawSMSGraphs = args.smsgraphs,
            results = args.results, addVer = args.add_version,
            dryrun = args.dry_run, checkfirst = args.checkfirst, copy = args.copy,
            ignoreValidated = args.ignoreValidated )
    print ( "[smsDictionary] Database", writer.database.databaseVersion )
    writer.run()
    if args.copy:
        cmd = f"cp ../smsgraphs/T*.p* {SmsDictWriter.smsgraphpath}"
        import subprocess
        print ( f"[smsDictionary] {cmd}" )
        a = subprocess.getoutput ( cmd )
        if len(a)>0:
            print ( f"[smsDictionary] error: {a}" )
