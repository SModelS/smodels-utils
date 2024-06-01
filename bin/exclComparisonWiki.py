#!/usr/bin/env python3

"""
.. module:: exclComparisonWiki
         :synopsis: Small script to produce the ExclComparison wiki page,
                    see http://smodels.github.io/SmsDictionary.
                    Comparing exclusion lines of different stats models

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

import setPath
import time, os
from smodels.experiment.databaseObj import Database

class ExclComparisonWriter:
    htmlpath = "../../smodels.github.io/"

    def __init__ ( self, database, addVer, dryrun, copy ):
        self.databasePath = database
        self.database = Database ( database )
        self.ver=self.database.databaseVersion.replace(".","")
        if not addVer:
            self.ver=""
        self.fname = f"ExclComparison{self.ver}"
        self.f=open(self.fname,"w" )
        self.dryrun =  dryrun
        self.copy = copy

    def close ( self ):
        self.f.close()

    def header( self ):
        self.f.write (
"""# Exclusion Lines Comparison Wiki
A first draft of a page that collects all validation plots that show comparisons of statistical models:
best signal region only versus statistical models at varying degrees of complexity.
The list has been created from the database version %s, considering also superseded results.

There is also a [ListOfAnalyses%s](https://smodels.github.io/docs/ListOfAnalyses%s), a [ListOfAnalyses%sWithSuperseded](https://smodels.github.io/docs/ListOfAnalyses%sWithSuperseded), and [Validation%s](Validation%s).

""" % ( self.database.databaseVersion, self.ver, self.ver, self.ver, self.ver, self.ver, self.ver ) )

    def footer( self ):
        self.f.write ( "\n<font color='grey'>This page was created %s</font>\n" % \
                       time.asctime() )
        return

    def tableHeader ( self ):
        columns=[ "#", "AnaId", "TxName", "Plot" ]
        lengths=[]
        for header in columns:
            #self.f.write ( "|<#EEEEEE:> **%s** " % header )
            self.f.write ( f"| **{header}** " )
            lengths.append ( len(header)+4 )
        self.f.write ( "|\n" )
        for l in lengths:
            self.f.write ( "| "+"-"*l+ " " )
        self.f.write ( "|\n" )

    def run ( self ):
        self.header()
        self.tableHeader ()
        self.footer()
        self.close()
        self.move()

    def move( self ):
        cmd= f"mv {self.fname} ../../smodels.github.io/docs/{self.fname}.md"
        os.system ( cmd )
        print ( cmd )

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description='Write Wiki page that lists all validation plots that compare exclusion lines, see http://smodels.github.io/docs/ExclComparison')
    argparser.add_argument ( '-D', '--dry_run', help='dry run, dont actually draw',
                             action='store_true' )
    argparser.add_argument ( '-c', '--copy', help='copy SMS graphs to ../../smodels.github.io/smsgraphs/ (implies -g)',
                             action='store_true' )
    argparser.add_argument ( '-d', '--database', help='path to database [../../smodels-database]',
                             type=str, default='../../smodels-database' )
    argparser.add_argument ( '-a', '--add_version',
            help='add version labels to links', action='store_true' )
    args = argparser.parse_args()
    writer = ExclComparisonWriter ( database=args.database, addVer = args.add_version,
            dryrun = args.dry_run, copy = args.copy )
    print ( "[exclComparison] Database", writer.database.databaseVersion )
    writer.run()
    if args.copy:
        cmd = f"cp ../smsgraphs/T*.p* {SmsDictWriter.smsgraphpath}"
        import subprocess
        print ( f"[exclComparison] {cmd}" )
        a = subprocess.getoutput ( cmd )
        if len(a)>0:
            print ( f"[exclComparison] error: {a}" )
