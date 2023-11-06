#!/usr/bin/env python3

""" compare the timing between the stats code and the spey code """

import os, sys
import numpy as np

def compare ( dbpath : os.PathLike, analysis : os.PathLike, 
              validationFile : os.PathLike ):
    statspath = os.path.join ( dbpath, analysis, "validation", validationFile )
    speypath = os.path.join ( dbpath, analysis, "validationSpey", validationFile )
    anaName = analysis.replace("13TeV/","").replace("8TeV/","").replace("CMS/","")
    anaName = anaName.replace("ATLAS/","").replace("/","")
    paths = { "stats": statspath, "spey": speypath }
    dicts = {}
    for name,path in paths.items():
        if not os.path.exists ( path ):
            print ( f"[compareTiming] {path} does not exist." )
            sys.exit()
        with open ( path, "rt" ) as h:
            exec(h.read(), globals() )
            dicts[name]=globals()["validationData"]
            h.close()
    statsTimes, speyTimes, ratios = {}, {}, {}
    vratios = []
    for pt in dicts["stats"]:
        if "axes" in pt and "t" in pt:
            saxes = str(pt["axes"])
            statsTimes[saxes]=pt["t"]
    for pt in dicts["spey"]:
        if "axes" in pt and "t" in pt:
            saxes = str(pt["axes"])
            speyTimes[saxes]=pt["t"]
            if saxes in statsTimes:
                ratio = statsTimes[saxes]/pt["t"]
                ratios[saxes]=ratio
                vratios.append ( ratio )
    print ( f"[compareTiming] for {anaName}:{validationFile}" )
    print ( f"[compareTiming] n: stat={len(statsTimes)}, spey={len(speyTimes)}, both={len(vratios)}" )
    print ( f"[compareTiming] r(stat/spey)={np.mean(vratios):.2f}+-{np.std(vratios):.2f}" )
                

if __name__ == "__main__":
    dbpath = os.path.join ( os.environ["HOME"], "git", "smodels-database" )
    ana = "13TeV/CMS/CMS-SUS-21-002-eff/"
    validationfile = "TChiWZ_2EqMassAx_EqMassBy_combined.py"
    import argparse
    ap = argparse.ArgumentParser(description="Compare timings between stats and spey" )
    ap.add_argument('-d', '--dbpath',
            help='database path [<home>/git/smodels-database]', default=None)
    ap.add_argument('-a', '--analysispath',
            help='analysis path [13TeV/CMS/CMS-SUS-21-002-eff/]', default=None)
    ap.add_argument('-v', '--validationpath',
            help='validation path [TChiWZ_2EqMassAx_EqMassBy_combined.py]', default=None)
    args = ap.parse_args()
    if args.dbpath != None:
        dbpath = args.dbpath
    if args.analysispath != None:
        ana = args.analysispath
    if args.validationpath != None:
        validationfile = args.validationpath
    compare ( dbpath, ana, validationfile )
