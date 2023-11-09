#!/usr/bin/env python3

""" compare the timing between the stats code and the spey code """

import os, sys
from colorama import Fore
import numpy as np
from datetime import datetime
from smodels_utils.helper.various import getValidationDataPathName

def compare ( dbpath : os.PathLike, analysis : os.PathLike, 
              validationFile : os.PathLike ):
    statspath = getValidationDataPathName ( dbpath, analysis, validationFile )
    speypath = statspath.replace("validation","validationSpey")
    anaName = analysis.replace("13TeV/","").replace("8TeV/","").replace("CMS/","")
    anaName = anaName.replace("ATLAS/","").replace("/","")
    print ( f"[compare] for {Fore.GREEN}{anaName}:{validationFile}{Fore.RESET}" )
    paths = { "stats": statspath, "spey": speypath }
    meta, dicts = {}, {}
    for name,path in paths.items():
        if not os.path.exists ( path ):
            print ( f"[compare] {path} does not exist." )
            sys.exit()
        with open ( path, "rt" ) as h:
            txt=h.read().replace("inf","float('inf')" )
            txt=txt.replace("nan","float('nan')")
            exec(txt, globals() )
            dicts[name]=globals()["validationData"]
            meta[name]=globals()["meta"]
            timestamp = datetime.strptime(meta[name]["timestamp"],"%a %b %d %H:%M:%S %Y")
            dt = ( datetime.now() - timestamp ).days
            if dt > 10:
                print ( f"{Fore.YELLOW}{name} {meta[name]['timestamp']}{Fore.RESET}" )
            h.close()
    statsTimes, speyTimes, ratioTimes = {}, {}, {}
    vratios, ULratios, eULratios = [], [], []
    statsULs, speyULs, ratioULs = {}, {}, {}
    statseULs, speyeULs, ratioeULs = {}, {}, {}
    for pt in dicts["stats"]:
        if "axes" in pt:
            saxes = str(pt["axes"])
            if "t" in pt:
                statsTimes[saxes]=pt["t"]
            if "UL" in pt:
                statsULs[saxes]=pt["UL"]
            if "eUL" in pt:
                statseULs[saxes]=pt["eUL"]
    ctWeird = 0
    for pt in dicts["spey"]:
        if "axes" in pt: 
            saxes = str(pt["axes"])
            if "t" in pt:
                speyTimes[saxes]=pt["t"]
                if saxes in statsTimes:
                    ratio = statsTimes[saxes]/pt["t"]
                    ratioTimes[saxes]=ratio
                    vratios.append ( ratio )
            if "UL" in pt:
                speyULs[saxes]=pt["UL"]
                if saxes in statsULs:
                    ratioUL = statsULs[saxes]/pt["UL"]
                    if ratioUL > 10. or ratioUL < .1:
                        ctWeird += 1
                        if ctWeird < 3:
                            print ( f"[compare] weird value: r(UL)={ratioUL:.2g} for {saxes}" )
                            print ( f"[compare] check {pt['slhafile']}" )
                    ratioULs[saxes] = ratioUL 
                    ULratios.append ( ratioUL )
                if saxes in statseULs:
                    ratioeUL = statseULs[saxes]/pt["eUL"]
                    if ratioeUL > 10. or ratioeUL < .1:
                        ctWeird += 1
                        if ctWeird<3:
                            print ( f"[compare] weird value: r(eUL)={ratioeUL:.2g} for {saxes}" )
                            print ( f"[compare] check {pt['slhafile']}" )
                    ratioeULs[saxes] = ratioeUL 
                    eULratios.append ( ratioeUL )
            if "eUL" in pt:
                speyeULs[saxes]=pt["eUL"]
    validationFile = validationFile[:validationFile.find("_")]
    pre,post="",""
    topoPasses = True
    if len(vratios)*2 < len(statsTimes)+len(speyTimes):
        pre,post = Fore.RED, Fore.RESET
    print ( f"[n]{pre} stat={len(statsTimes)}, spey={len(speyTimes)}, both={len(vratios)}{post}" )
    if len(vratios)!=len(speyTimes) or len(vratios)!=len(statsTimes):
        topoPasses=False
    if len(ULratios)>0:
        mean = np.mean(ULratios)
        std = np.std(ULratios)
        pre,post="",""
        if abs(mean-1.0)>.3 or std>.3:
            pre,post=Fore.RED,Fore.RESET
        print ( f"[UL] {pre}{mean:.2f}+-{std:.2f} ({len(ratioULs)}){post}" )
        if abs(mean-1.)>5e-2 or std>.1:
            topoPasses=False
    else:
        print ( f"{Fore.RED}[UL] no upper limit values{Fore.RESET}" )
        topoPasses=False
    if len(eULratios)>0:
        mean = np.mean(eULratios)
        std = np.std(eULratios)
        pre,post="",""
        if abs(mean-1.0)>.3 or std>.3:
            pre,post=Fore.RED,Fore.RESET
        if abs(mean-1.)>5e-2 or std>.1:
            topoPasses=False
        pre,post="",""
        print ( f"[eUL] {pre}{mean:.2f}+-{std:.2f} ({len(ratioeULs)}){post}" )
    else:
        print ( f"{Fore.RED}[eUL] no expected upper limit values{Fore.RESET}" )

    if len(vratios)==0:
        print ( f"[n] no ratios" )
    else:
        print ( f"[t] stat/spey={np.mean(vratios):.2f}+-{np.std(vratios):.2f}" )
    if topoPasses:
        print ( f"{Fore.GREEN}[compare] passed!{Fore.RED}" )
    print ()
                
def findAll ( dbpath : os.PathLike ):
    """ find all files to compare """
    import glob
    wildcardpath = f"{dbpath}/*TeV/*/*/validationSpey"
    paths = glob.glob ( wildcardpath )
    for path in paths:
        p = path.replace( "/validationSpey", "" )
        #if p.startswith ( "/" ):
        #    p = p[1:]
        p = os.path.basename ( p )
        wildcardvals = os.path.join ( path, "T*_combined.py" )
        validationfiles = glob.glob ( wildcardvals )
        for validationfile in validationfiles:
            statsversion = validationfile.replace("validationSpey","validation" )
            filename = os.path.basename ( validationfile )
            if os.path.exists ( statsversion ):
                compare ( dbpath, p, filename )

    sys.exit()

if __name__ == "__main__":
    dbpath = os.path.join ( os.environ["HOME"], "git", "smodels-database" )
    ana = "CMS-SUS-21-002-eff"
    validationfile = "TChiWZ_2EqMassAx_EqMassBy_combined.py"
    import argparse
    ap = argparse.ArgumentParser(description="Compare timings between stats and spey" )
    ap.add_argument('-d', '--dbpath',
            help='database path [<home>/git/smodels-database]', default=None)
    ap.add_argument('-a', '--analysisname',
            help='analysis path [CMS-SUS-21-002-eff]', default=None)
    ap.add_argument('-v', '--validationfile',
            help='validation path [TChiWZ_2EqMassAx_EqMassBy_combined.py]', default=None)
    ap.add_argument('-A', '--all', action="store_true",
            help='compare all in database path' )
    args = ap.parse_args()
    if args.all:
        findAll ( dbpath )
    if args.dbpath != None:
        dbpath = args.dbpath
    if args.analysisname != None:
        ana = args.analysisname
    if args.validationfile != None:
        validationfile = args.validationfile
    compare ( dbpath, ana, validationfile )
