#!/usr/bin/env python3

""" simple plot to draw the relative statistical error of the best SR """

import matplotlib.pyplot as plt
import copy
import glob
import os
import numpy
import importlib
import warnings
import subprocess
import time
from matplotlib import colors as C
from smodels_utils.helper.various import getPathName

def getTopo ( validation ):
    """ the the name of the topology from the validation file name """
    tokens = validation.split("_")
    return tokens[0]

def getEmbakedDict ( basedir, topo ):
    """ get the embaked file """
    path = f"{basedir}orig/{topo}.embaked"
    if not os.path.exists( path ):
        print ( f"cannot find {path}" )
        return {}
    f=open(path,"rt")
    D=eval(f.read())
    f.close()
    ret={}
    for k,values in D.items():
        if not "__nevents__" in values:
            ret[k]=5000
        else:
            ret[k]=values["__nevents__"]
    return ret

def convertNewAxes ( newa ):
    """ convert new types of axes (dictionary) to old (lists) """
    axes = copy.deepcopy(newa)
    if type(newa)==list:
        return axes[::-1]
    if type(newa)==dict:
        axes = [ newa["x"], newa["y"] ]
        if "z" in newa:
            axes.append ( newa["z"] )
        return axes[::-1]
    # print ( "cannot convert this axis" )
    return None

def getNEvents ( nevents, eff ):
    key = ( int(eff[0]), int(eff[1]) )
    if key in nevents:
        return nevents[key]
    dmax,ret=float("inf"),float("nan")
    def dist ( m1, m2 ):
        return (m1[0]-m2[0])**2 + (m1[1]-m2[1])**2
    for masses,eff in nevents.items():
        d = dist ( masses, key )
        if d < dmax:
            dmax = d
            ret = eff
    return ret

def draw( validationfile, suffix ):
    """
    :param suffix: an index to count multiple planes, or None
    """
    warnings.simplefilter("ignore")
    anaId = "???"
    coll = "CMS"
    p = validationfile.find ( "ATLAS" )
    if p > 0:
        coll = "ATLAS"
    else:
        p = validationfile.find ( "CMS" )
    p2 = validationfile.find("-eff" )
    p2b = validationfile.find("-andre" )
    if p2 < 1:
        p2 = p2b
    anaId = validationfile[p+1+len(coll):p2]
    p3 = validationfile.find("validation/")
    p4 = validationfile[p3+10:].find("_")
    topo = validationfile[p3+10+1:p3+p4+10]
    spec = importlib.util.spec_from_file_location( "output", validationfile )
    output_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(output_module)
    validationData = output_module.validationData

    effs = []
    noResults = []
    skipped, err = 0, None

    for point in validationData:
        if "error" in point:
            skipped += 1
            err = point["error"]
            if "axes" in point:
                axes = convertNewAxes ( point["axes"] )
                if axes != None:
                    noResults.append ( ( axes[1], axes[0] ) )
            continue
        axes = convertNewAxes ( point["axes"] )
        effs.append ( ( axes[1], axes[0], point["efficiency"] ) )
    if skipped > 0:
        print ( f"[drawRelStatErr] skipped {int(skipped)}/{len(validationData)} points: {err}" )
    effs.sort()
    basedir = validationfile[:p3]
    nevents = getEmbakedDict ( basedir, topo )
    x,y,z=[],[],[]
    for eff in effs:
        x.append ( eff[0] )
        y.append ( eff[1] )
        nev = getNEvents( nevents, eff )
        if eff[2] == None:
            rse = float("nan")
        else:
            rse = 1. / numpy.sqrt(eff[2]*nev)
        if eff[2] == 0.:
            rse = float("nan")
        if rse > .35:
            rse = .35
        z.append ( 100. * rse )
    plt.scatter ( x, y, c=z )
    cbar = plt.colorbar()
    cbar.set_label ( "relative statistical error (%)" )
    plt.title ( f"rel.stat.err of best SR, {anaId}:{topo}" )
    plt.xlabel ( "m(mother) [GeV]" )
    plt.ylabel ( "m(LSP) [GeV]" )
    rse = {}
    suff = ""
    if suffix != None:
        suff = f"_{suffix!s}"
    fname = f"relstaterr_{anaId}_{topo}{suff}.png"
    print ( f"[drawRelStatErr] saving to {fname}" )
    plt.savefig ( fname )
    plt.clf()
    return fname

def writeMDPage( push = False ):
    """ write the markdown page for smodels.github.io """

    Dir = "../../smodels.github.io/relstaterr/"
    path = f"{Dir}relstaterr_*.png"
    files = glob.glob( path )
    files.sort()
    stats = {}
    for f in files:
        print ( "f", f )
        p1 = f.find("relstaterr/")
        f = f.replace(".png","")
        f = f[p1+22:]
        tokens = f.split("_")
        if not tokens[0] in stats:
            stats [ tokens[0] ] = []
        if tokens[1] == "TGQ12":
            continue
        stats [ tokens[0] ].append ( tokens[1] )
    print ( f"[drawRelStatErr] writing {Dir}README.md" )
    # print ( "[drawRelStatErr] files %s" % path )
    with open ( f"{Dir}README.md", "wt" ) as g:
        g.write ( "# Plots of relative statistical errors\n" )
        g.write ( f"as of {time.asctime()}\n" )
        g.write ( "\n" )
        g.write ( "## stats\n" )
        for ana,topos in stats.items():
            g.write ( f" * {ana}: " )
            prevtopo = ""
            for ctr,topo in enumerate(topos):
                if prevtopo == topo:
                    continue
                if ctr > 0:
                    g.write ( ", " )
                g.write ( f"[{topo}](#{f"{ana}_{topo}"})" )
                prevtopo = topo
            g.write ( "\n" )
        g.write ( "\n" )
        g.write ( "## plots\n" )
        g.write ( "\n" )
        g.write ( "| **topo** | **image** |\n" )
        g.write ( "|----------|-----------|\n" )

        for f in files:
            src=os.path.basename ( f )
            p1 = f.find("relstaterr/")
            f = f.replace(".png","")
            f = f[p1+22:]
            tokens = f.split("_")
            if "TGQ12" in tokens[1]:
                print ( "[drawRelStatErr] skipping TGQ12" )
                continue
            t0 = int(time.time() )-1590000000
            img = f'<img src="{src}?{int(t0)}" />' 
            anchor = f'{tokens[0]}, {tokens[1]}<a name="{f}"></a>'
            g.write ( f'| {anchor} | {img} |\n' )
        g.write ( "\n" )
        g.close()
    cmd = "cd ../../smodels.github.io/; git commit -am 'automated commit' ; git push"
    o = ""
    if push:
        o = subprocess.getoutput ( cmd )
    print ( f"[drawRelStatErr] cmd {cmd}: {o}" )
    
if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser( description = "plot relative statistical error of best signal region" )
    argparser.add_argument ( "-d", "--dbpath", help="path to database [../../smodels-database/]", type=str,
                             default="../../smodels-database/" )
    argparser.add_argument ( "-a", "--analysis", 
            help="analysis name, like the directory name [CMS-EXO-13-006-eff]", 
            type=str, default="CMS-EXO-13-006-eff" )
    argparser.add_argument ( "-v", "--validationfile", 
            help="validation file, can use wildcards [T*py]", 
            type=str, default="T*.py" )
    argparser.add_argument ( "-D", "--default", action="store_true", 
            help="default run on arguments. currently set to be the exo 13 006 plots" )
    argparser.add_argument ( "-c", "--copy", action="store_true", 
            help="cp to smodels.github.io, as it appears in https://smodels.github.io/relstaterr/" )
    argparser.add_argument ( "-p", "--push", action="store_true", 
            help="commit and push to smodels.github.io, as it appears in https://smodels.github.io/relstaterr/" )
    args = argparser.parse_args()
    if not args.default and not args.analysis.endswith("-eff") and not args.analysis in [ "", "None", "none", None ]:
        print ( "[drawRelStatErr] warning, analysis name does not end with -eff, might be an error?" )
        args.analysis += "-eff"
    if args.default:
        analyses = [ "CMS-EXO-13-006-andre", "CMS-EXO-13-006-eff" ]
        validations = [ "THSCPM1b_2EqMassAx_EqWidthAy.py", "THSCPM3_2EqMassAx_EqMassBy**.py", "THSCPM4_*.py", "THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py", "THSCPM6_EqMassA__EqmassAx_EqmassBx-100_Eqma*.py", "THSCPM8_2EqMassAx*.py", "THSCPM2b_*.py" ]
    else:
        analyses = [ args.analysis ]
        if args.analysis in [ "None", "", "none", None ]:
            analyses = []
        validations = [ args.validationfile ]
        if "*" in args.validationfile:
            path = f"{args.dbpath}*/*/{args.analysis}/validation/{args.validationfile}" 
            print ( "searching", path )
            tmp = glob.glob ( path )
            validations = []
            for v in tmp:
                p1 = v.find("validation/")
                t = v[p1+11:]
                validations.append ( t )

    for analysis in analyses:
        topos = {}
        for validationfile in validations:
            topo = getTopo ( validationfile )
            suffix=None
            if topo in topos:
                suffix=len(topos[topo])
                topos[topo].append ( validationfile )
            else:
                topos[topo]= [ validationfile ]
            ipath = getPathName ( args.dbpath, analysis, validationfile )
            fname = draw( ipath, suffix )
            if args.copy:
                cmd = f"cp {fname} ../../smodels.github.io/relstaterr/"
                o = subprocess.getoutput ( cmd )
                print ( f"[drawRelStatErr] cmd {cmd}: {o}" )
    if args.copy:
        writeMDPage( args.push )
