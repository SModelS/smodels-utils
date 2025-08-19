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

    def __init__ ( self, database, addVer, dryrun ):
        self.databasePath = database
        self.database = Database ( database )
        ## whats the version
        self.ver=self.database.databaseVersion.replace(".","")
        ## even if we dont write version numbers, we want to
        ## know whats the version
        self.actualVer = self.ver
        if not addVer:
            self.ver=""
        self.fname = f"ExclComparison{self.ver}"
        self.f=open(self.fname,"w" )
        self.dryrun =  dryrun

    def close ( self ):
        self.f.close()

    def header( self ):
        self.f.write (
f"""# Validation plots: comparison of best-SR vs SR combination
This page collects all validation plots that show comparisons of statistical models:
best signal region only versus statistical models at varying degrees of complexity.
The list has been created from the database version {self.database.databaseVersion}, considering also superseded results.
Go to [ATLAS 13 TeV results](#ATLAS), [CMS 13 TeV results](#CMS).
There are no 8 TeV results with statistical models.

There is also a [ListOfAnalyses{self.ver}](https://smodels.github.io/docs/ListOfAnalyses{self.ver}), 
a [ListOfAnalyses{self.ver}WithSuperseded](https://smodels.github.io/docs/ListOfAnalyses{self.ver}WithSuperseded), and [Validation{self.ver}](Validation{self.ver}).

""" )
        # self.f.write ( f"\n## [ATLAS](#ATLAS) [CMS](#CMS)\n" )

    def footer( self ):
        self.f.write ( f"\n<font color='grey'>This page was created {time.asctime()}</font>\n" )
        return

    def tableHeader ( self ):
        columns=[ "#", "Analysis ID", "TxName", "Plot" ]
        lengths=[]
        for header in columns:
            #self.f.write ( f"|<#EEEEEE:> **{header}** " )
            self.f.write ( f"| **{header}** " )
            lengths.append ( len(header)+4 )
        self.f.write ( "|\n" )
        for l in lengths:
            self.f.write ( f"| {'-' * l} " )
        self.f.write ( "|\n" )

    def oneTable ( self, obsfiles ):
        """ given obsfiles, create one table """
        t0 = time.time()
        obsfiles.sort( reverse=True )
        for ctr,obsfile in enumerate ( obsfiles ):
            lpath = obsfile.replace(self.databasePath,"")
            if lpath.startswith("/"):
                lpath = lpath[1:]
            tmp = lpath
            p1 = tmp.find("TeV")
            tmp = tmp[p1+4:]
            pv = tmp.find("validation")
            txname = tmp[pv+11:]
            p_ = txname.find("_")
            txname = txname[:p_]
            tmp = tmp[:pv-1]
            p1 = tmp.find("/")
            tmp = tmp[p1+1:]
            # print ( "@@0 txname", txname ) 
            self.f.write ( f"| {ctr+1} " )
            #from smodels_utils.helper import various
            # anaId = various.removeAnaIdSuffices ( tmp )
            anaId = tmp.replace("-eff","") ## actually we only want to remove -eff
            anaUrl = f"https://smodels.github.io/docs/ListOfAnalyses{self.ver}#{anaId}"
            self.f.write ( f"| <a href='{anaUrl}'>{anaId}</a> " )
            self.f.write ( f"| <a href='https://smodels.github.io/docs/SmsDictionary{self.ver}#{txname}'>{txname}</a> " )
            figPath = f"https://smodels.github.io/validation/{self.actualVer}/{lpath}"
            self.f.write ( f'| <a href="{figPath}"><img width="500px" src="{figPath}?{t0}" /></a>' )
            self.f.write ( "\n" )

    def body ( self ):
        """ the 'body' of the wiki page """
        import glob
        path = f"{self.databasePath}/*/*/*/validation"
        obsfiles = glob.glob ( f"{path}/*obs.png" )
        for exp in [ "ATLAS", "CMS" ]:
            self.f.write ( f'\n<a name="{exp}"></a>\n' )
            self.f.write ( f"## {exp}\n\n" )
            self.tableHeader()
            tmp = [ x for x in obsfiles if exp in x ]
            self.oneTable ( tmp )

    def run ( self ):
        self.header()
        self.body()
        self.footer()
        self.close()
        self.move()

    def move( self ):
        cmd= f"mv {self.fname} ../../smodels.github.io/docs/{self.fname}.md"
        os.system ( cmd )
        print ( cmd )

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description='Write Wiki page that lists all '\
        'validation plots that compare exclusion lines, '\
        'see http://smodels.github.io/docs/ExclComparison')
    argparser.add_argument ( '-D', '--dry_run', help='dry run, dont actually draw',
                             action='store_true' )
    argparser.add_argument ( '-d', '--database', help='path to database [../../smodels-database]',
                             type=str, default='../../smodels-database' )
    argparser.add_argument ( '-a', '--add_version',
            help='add version labels to links', action='store_true' )
    args = argparser.parse_args()
    writer = ExclComparisonWriter ( database=args.database, addVer = args.add_version,
            dryrun = args.dry_run )
    print ( f"[exclComparison] Database {writer.database.databaseVersion}" )
    writer.run()
