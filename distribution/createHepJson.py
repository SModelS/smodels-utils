#!/usr/bin/env python3

""" simple script to create smodels-database.json that will be used
to mark SModelS entries at hepdata """

import os, sys
from typing import Union
from smodels_utils.helper.databaseManipulations import filterFastLimFromList,\
         filterSupersededFromList
from smodels_utils.helper.terminalcolors import *
from smodels.experiment.expResultObj import ExpResult

class HepJsonCreator:
    def __init__ ( self, long_version : bool, dbpath : os.PathLike ):
        """
        :ivar extra_fields: if false, then add only fields required by hepdata,
        :param long_version: create the long, now default version,
        not the old short version
        if true, add more info like wiki page url, arxiv id, publication, etc
        """
        ## the short version is this super simplistic version that
        ## hepdata was using initially
        self.long_version = long_version
        self.extra_fields = True
        if not os.path.exists ( "cache" ):
            os.mkdir ( "cache" )
        self.entries = {}

        from smodels.experiment.databaseObj import Database
        dbpaths = dbpath.split("+")
        validNames = [ "official", "superseded", "fastlim", "full_llhds",
            "nonaggregated", "backup", "latest", "backupunittest",
            "unittest", "debug" ]
        for dbp in dbpaths:
            dbp = dbp.strip()
            if not os.path.exists ( dbp ):
               if not dbp in validNames:
                   print ( f"[createHepJson] {dbpath} not found" )
                   sys.exit()
        self.dbpath = dbpath
        self.db = Database ( dbpath )

    def merge ( self, entry1, entry2, anaId ):
        """ merge two entries """
        for k,v in entry2.items():
            if not k in entry1:
                entry1[k]=v
                continue
            if k == "resultType" and v != entry1[k]:
                if v in entry1[k]: ## already in!
                    continue
                entry1[k]+=f",{v}"
                continue
            if k == "path" and v != entry1[k]:
                if v in entry1[k]: ## already in!
                    continue
                entry1[k]+=f",{v}"
                continue
            if k == "SRcomb":
                if v in [ None, "None" ]: ## skip
                    continue
                entry1[k] = v
                # print ( f"merging {entry1} and {entry2}: {entry1}" )
                continue
            if k == "prettyName":
                # take the shorter!
                if v in entry1[k]:
                    entry1[k]=v
            if str(v) != str(entry1[k]):
                print ( f"[createHepJson] {YELLOW}entry '{k}' differs for {anaId}: '{v}' != '{entry1[k]}'{RESET}" )
                print ( f"[createHepJson] {YELLOW}will use {entry1[k]}{RESET}" )
        return entry1

    def getHepData ( self, nr : int, ana_id : str ) -> str:
        """ get either the content of https://www.hepdata.net/record/ins{nr}, if evaluable,
        or get this url, FIXME not used """
        hepdata = f"https://www.hepdata.net/record/ins{nr}"
        cachefile = f"cache/{nr}"
        if os.path.exists ( cachefile ):
            try:
                with open ( cachefile, "rt" )  as f:
                    content = f.read()
                    f.close()
                    return content
            except Exception as e:
                print ( f"{RED}cannot read cachefile '{cachefile}': '{e}'{RESET}" )
        import requests
        req = requests.request ( url=hepdata, method="GET" )
        try:
            content = eval(req.content)
            ret = content["@id"]
            with open ( cachefile, "wt" ) as f:
                f.write ( ret )
                f.close()
            return ret
        except SyntaxError as e:
            print ( f"{RED}cannot read content for #{nr}[{ana_id}]:: {hepdata}: {str(req.content)[:80]} {e}{RESET}" )
            return hepdata

    def short_header ( self ):
        self.f.write ( "{\n" )

    def header( self ):
        """ header of the json file """
        import smodels
        self.f.write ( "{\n" )
        self.f.write ( '  "schema_version": "1.0.0",\n' )
        self.f.write ( '  "tool": "SModelS",\n' )
        # ver = smodels.installation.version()
        ver = self.db.databaseVersion
        self.f.write (f'  "version": "{ver}",\n' )
        from datetime import datetime
        from zoneinfo import ZoneInfo
        # now = datetime.now(timezone.utc)
        now = datetime.now(ZoneInfo("Europe/Vienna"))
        timestamp = now.isoformat()
        self.f.write (f'  "date_created": "{timestamp}",\n' )
        self.f.write (f'  "implementations_description": "SModelS analysis",\n' )
        self.f.write ( '  "link_types": [ "main_url", "val_url", "publication", "arXiv" ],\n' )
        self.f.write ( '  "url_templates": {\n' )
        self.f.write ( '    "main_url": "https://github.com/SModelS/smodels-database-release/tree/main/{path}",\n' )
        self.f.write ( '    "val_url": "https://smodels.github.io/docs/Validation#{name}",\n' )
        if self.extra_fields:
            self.f.write ( '    "publication": "https://doi.org/{publication_doi}",\n' )
            self.f.write ( '    "arXiv": "https://arxiv.org/abs/{arXiv_id}"\n' )
        self.f.write ( '  },\n' )
        self.f.write ( '  "analyses" : [\n' )

    def short_footer ( self ):
        self.f.write ( '\n}\n' )

    def footer(self):
        """ footer of the json file """
        self.f.write ( '  ],\n' )
        self.f.write ( '  "implementations_license": {\n' )
        self.f.write ( '      "name": "cc-by-4.0",\n' )
        self.f.write ( '      "url": "https://creativecommons.org/licenses/by/4.0"\n' )
        self.f.write ( '  }\n' )
        self.f.write ( '}\n' )

    def getInspireFromWebPage ( self, gI ) -> Union[None,int]:
        """ try to get the inspire number from the wiki page """
        if not hasattr ( gI, "url" ):
            return None
        import requests
        r = requests.get ( gI.url )
        txt = r.text
        ## first search for inspirehep.net/record links
        p1 = txt.find("://inspirehep.net/record/")
        while p1 > 0 and len(txt)>0:
            p1 = txt.find("://inspirehep.net/record/")
            txt = txt[p1+25:]
            p2 = txt.find('"')
            tmp = txt[:p2]
            try:
                tmp = int(tmp)
                return tmp
            except ValueError as e:
                pass
        p1 = txt.find("://inspirehep.net/literature/")
        while p1 > 0 and len(txt)>0:
            p1 = txt.find("://inspirehep.net/literature/")
            txt = txt[p1+27:]
            p2 = txt.find('"')
            tmp = txt[:p2]
            try:
                tmp = int(tmp)
                return tmp
            except ValueError as e:
                pass
        txt = r.text
        ## now try  hepdata.net/record links
        p1 = txt.find("://www.hepdata.net/record/ins")
        while p1 > 0 and len(txt)>0:
            p1 = txt.find("://www.hepdata.net/record/ins")
            txt = txt[p1+29:]
            p2 = txt.find('"')
            tmp = txt[:p2]
            try:
                tmp = int(tmp)
                return tmp
            except ValueError as e:
                pass
                # print ( e )
        return None

    def collectEntry ( self, i : int, er : ExpResult ):
        """ collect a single entry, add to self.entries
        :param i: entry #
        :param n_entries: number of entries, total
        """
        gI = er.globalInfo
        from smodels_utils.helper.various import getCollaboration
        coll = getCollaboration ( gI.id )
        dses = er.datasets
        resultType = "EM"
        SRcomb = None
        if hasattr ( gI, "covariance" ):
            SRcomb = "SLv1"
        if hasattr ( gI, "jsonFiles" ):
            SRcomb = "pyhf"
        if len(dses) == 1 and dses[0].dataInfo.dataId == None:
            resultType = "UL"
        Id = gI.id
        for ext in [ "-ma5", "-ewk", "-strong", "-agg", "-hino", "-multibin", "-exclusive" ]:
           Id = Id.replace(ext,"")
        entry = { "exp": coll, "ana_id": Id, "resultType": resultType }
        path = gI.path.replace("/globalInfo.txt","")
        p1 = path.rfind("/")
        entry["path"]=path[p1+1:]
        if hasattr ( gI, "type" ):
            entry["signature_type"]=gI.type
        for ds in dses:
            if hasattr ( ds.dataInfo, "thirdMoment" ):
                SRcomb = "SLv2"
            for txn in ds.txnameList:
                if not hasattr ( txn, "dataUrl" ):
                    continue
                dU = txn.dataUrl
                if dU == None:
                    continue
                if "/ins" in dU:
                    p1 = dU.find("/ins")
                    tmp = dU[p1+4:]
                    p2 = tmp.find("/")
                    if p2 > -1 :
                        tmp = tmp[:p2]
                    p2 = tmp.find("?")
                    if p2 > -1 :
                        tmp = tmp[:p2]
                    p2 = tmp.find("_")
                    if p2 > -1 :
                        tmp = tmp[:p2]
                    # print ( "tmp", dU, "->", tmp )
                    inspire = tmp
                    #hepdata = self.getHepData  ( inspire, Id )
                    # inspire = f"https://inspirehep.net/literature/{tmp}"
                    #entry["hepdata"]=hepdata
                    entry["inspire"]=inspire
                    break
        if SRcomb != None:
            entry["SRcomb"]=SRcomb
        if hasattr ( gI, "arxiv" ):
            ar = gI.arxiv
            p1 = ar.rfind("/")
            entry["arXiv_id"]=ar[p1+1:]
        if hasattr ( gI, "prettyName" ):
            entry["pretty_name"]=gI.prettyName
        if True and hasattr ( gI, "publication" ):
            entry["paper"]=gI.publication
        if hasattr ( gI, "publicationDOI" ):
            doi = gI.publicationDOI
            # doi = doi.replace("http://doi.org/","")
            doi = doi.replace("https://doi.org/","")
            entry["publication_doi"]=doi
        wiki = gI.url
        if ";" in wiki:
            wiki = wiki.find(";")
        entry["wiki"]=wiki
        if not "inspire" in entry:
            inspire = self.getInspireFromWebPage ( gI )
            if inspire != None:
                entry["inspire"]=inspire
                #hepdata = self.getHepData  ( inspire, Id )
                #entry["hepdata"]= hepdata
        if False:
            print ( f"[createHepJson] {entry}" )
        if Id in self.entries:
            merged = self.merge ( self.entries[Id], entry, Id )
            self.entries[Id] = merged
            return merged
        else:
            self.entries[Id] = entry
        return entry

    def collectEntries( self, expResList ) ->  bool:
        """ collect entries into self.entries """
        n_results = len(expResList)
        for i,er in enumerate(expResList):
            print ( f"[createHepJson] {i+1}/{n_results}: {er.globalInfo.id}" )
            self.collectEntry ( i, er )
        return True

    def short_body( self ):
        expResList = self.db.getExpResults()
        expResList = filterFastLimFromList ( expResList )
        supersededList = filterSupersededFromList ( expResList, True )
        superseded = set ( [ x.globalInfo.id for x in supersededList ] )
        self.collectEntries ( expResList )
        from smodels_utils.helper.various import getSqrts
        first = True
        ver = self.db.databaseVersion
        dotlessver = ver.replace(".","")
        baseUrl = f"https://smodels.github.io/docs/ListOfAnalyses#"
        supersededUrl = f"https://smodels.github.io/docs/ListOfAnalysesWithSuperseded#"
        # baseUrl = f"https://smodels.github.io/docs/ListOfAnalyses{dotlessver}#"
        # baseUrl = f"https://smodels.github.io/docs/ListOfAnalyses{dotlessver}WithSuperseded#"
        for anaId,entry in self.entries.items():
            if not "inspire" in entry:
                continue
            if not first:
                self.f.write ( ',\n' )
            inspire = entry["inspire"]
            self.f.write ( f'      "{inspire}": [\n' )

            resultTypes = entry["resultType"].lower().split(",")
            validations = set()
            for resultType in resultTypes:
                if anaId in superseded:
                    validations.add ( f'"{supersededUrl}{anaId}"' )
                else:
                    validations.add ( f'"{baseUrl}{anaId}"' )
                #validations.append ( f'"{baseUrl}{anaId}_{resultType}"' )
            for i,validation in enumerate(validations):
                self.f.write ( f'              {validation}' )
                isLast = ( i == len(validations)-1 )
                if not isLast:
                    self.f.write ( ',' )
                self.f.write ( '\n' )
            self.f.write ( "\n      ]" )
            first = False

    def body( self ):
        """ the body of the json file, i.e. the actual list of entries """
        expResList = self.db.getExpResults()
        expResList = filterFastLimFromList ( expResList )
        self.collectEntries ( expResList )
        from smodels_utils.helper.various import getSqrts
        first = True
        def writeLabel ( label : str, entry : list, isFirst : bool ):
            """ from entry, write 'label' """
            if not label in entry:
                return
            if not isFirst:
                self.f.write ( ',\n' )
            l = entry[label]
            self.f.write ( f'      "{label}": "{l}"' )

        for anaId,entry in self.entries.items():
            if not "inspire" in entry:
                print ( f"[createHepJson] {RED}no inspire id for {entry['ana_id']}: skip!{RESET}" )
                continue
            if not first:
                self.f.write ( ',\n' )
            first = False
            self.f.write ( '    {\n' )
            inspire = entry["inspire"]
            self.f.write ( f'      "inspire_id": {inspire},\n' )

            labels = []
            if self.extra_fields:
                labels = [ "ana_id" ]
            for label in labels:
                writeLabel ( label, entry, isFirst=True )
            self.f.write ( ',\n' )
            sqrts = getSqrts ( anaId )
            exp = entry["exp"]
            resultTypes = entry["resultType"].lower().split(",")
            implementations = []
            for path in entry["path"].split(","):
                implementation = f'{sqrts}TeV/{exp}/{path}/'
                implementations.append ( implementation )
            self.f.write ( f'      "implementations": [\n' )
            validations = []
            for resultType in resultTypes:
                validations.append ( f'{anaId}_{resultType}' )

            isFirst=True
            for implementation,validation in zip(implementations,validations):
                if not isFirst:
                    self.f.write ( ",\n" )
                self.f.write ( '        {\n' )
                self.f.write ( f'          "name": "{validation}",\n' )
                self.f.write ( f'          "path": "{implementation}"\n' )
                self.f.write ( '        }' )
                isFirst=False

            self.f.write ( f'\n      ],\n' )
            isFirst = True
            labels = [ "pretty_name", "signature_type" ]
            if self.extra_fields:
                labels = [ "pretty_name", "publication_doi", "arXiv_id", "SRcomb", "signature_type", "wiki" ]
            for label in labels:
                writeLabel ( label, entry, isFirst )
                isFirst = False
            self.f.write ( '\n    }' )
        self.f.write('\n' )

    def check ( self, analysisId : str ):
        """ check what entry we would get for a single analysis,
        for debugging """
        expResList = self.db.getExpResults( analysisIDs = [ analysisId ] )
        expResList = filterFastLimFromList ( expResList )
        for er in expResList:
            entry = self.collectEntry ( 0, er )
            print ( er )
            print ( entry )

    def create( self, outputfile : os.PathLike ):
        """ create smodels-analyses.json """
        self.f=open(outputfile,"wt")
        if self.long_version:
            self.header( )
            self.body( )
            self.footer()
        else:
            self.short_header( )
            self.short_body( )
            self.short_footer()
        print ( f"[createHepJson] writing to {outputfile}" )
        self.f.close()

    def interact ( self ):
        """ start interactive shell, to debug """
        import sys, IPython; IPython.embed( colors = "neutral" )

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="simple script to create the smodels-analyses.json files" )
    dbpath = os.path.abspath ( \
        f"{os.path.dirname(__file__)}/../../smodels-database" )
    ap.add_argument('-d', '--dbpath',
            help= f'path to database [{dbpath}]',
            default=dbpath)
    ap.add_argument('-o', '--outputfile',
            help='path to database [smodels-analyses.json]',
            default='smodels-analyses.json')
    ap.add_argument('-s', '--short_version',
            help='create short version, not long',
            action='store_true' )
    ap.add_argument('-c', '--check',
            help='check the entry of one analysis',
            type=str, default=None )
    ap.add_argument('-i', '--interact',
            help='launch interactive shell at the end',
            action='store_true' )
    args = ap.parse_args()
    args.long_version = not args.short_version
    # args.dbpath = "official"
    creator = HepJsonCreator( args.long_version, args.dbpath )
    if args.check not in [ "", None ]:
        creator.check ( args.check )
        import sys; sys.exit()
    creator.create( args.outputfile )
    if args.interact:
        creator.interact()
