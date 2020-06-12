#!/usr/bin/env python3

""" simple plot to draw the relative statistical error of the best SR """

import matplotlib.pyplot as plt
import copy
import os
import numpy
import importlib
import warnings
import subprocess
import time
from matplotlib import colors as C
from smodels_utils.helper.various import getPathName

def getEmbakedDict ( basedir, topo ):
    """ get the embaked file """
    path = basedir+"orig/"+topo+".embaked"
    if not os.path.exists( path ):
        print ( "cannot find %s" % path )
        return {}
    f=open(path,"rt")
    D=eval(f.read())
    f.close()
    ret={}
    for k,values in D.items():
        if not "__nevents__" in values:
            ret[k]=0
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
    print ( "cannot convert this axis" )
    return None

def getNEvents ( nevents, eff ):
    key = ( int(eff[0]), int(eff[1]) )
    if key in nevents:
        return nevents[key]
    dmax,ret=float("inf"),0.
    def dist ( m1, m2 ):
        return (m1[0]-m2[0])**2 + (m1[1]-m2[1])**2
    for masses,eff in nevents.items():
        d = dist ( masses, key )
        if d < dmax:
            dmax = d
            ret = eff
    return ret

def draw( validationfile ):
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
                noResults.append ( ( axes[1], axes[0] ) )
            continue
        axes = convertNewAxes ( point["axes"] )
        effs.append ( ( axes[1], axes[0], point["efficiency"] ) )
    if skipped > 0:
        print ( "[drawBestSRs] skipped %d/%d points: %s" % ( skipped, len(validationData), err ) )
    effs.sort()
    basedir = validationfile[:p3]
    nevents = getEmbakedDict ( basedir, topo )
    x,y,z=[],[],[]
    for eff in effs:
        x.append ( eff[0] )
        y.append ( eff[1] )
        nev = getNEvents( nevents, eff )
        if eff[2] == None:
            rse = 0.
        else:
            rse = 1. / numpy.sqrt(eff[2]*nev)
        if rse > .35:
            rse = .35
        z.append ( 100. * rse )
    plt.scatter ( x, y, c=z )
    cbar = plt.colorbar()
    cbar.set_label ( "relative statistical error (%)" )
    plt.title ( "rel.stat.err of best SR, %s:%s" % ( anaId, topo ) )
    plt.xlabel ( "m(mother) [GeV]" )
    plt.ylabel ( "m(LSP) [GeV]" )
    rse = {}
    fname = "relstaterr_%s_%s.png" % ( anaId, topo )
    print ( "[drawBestSRs} saving to %s" % fname )
    plt.savefig ( fname )
    plt.clf()
    return fname

def writeBestSRs( push = False ):
    import glob
    Dir = "../../smodels.github.io/ratioplots/"
    files = glob.glob("%sbestSR*png" % Dir )
    files.sort()
    topos = set()
    for f in files:
        p = f.rfind ( "_" )
        topos.add ( f[p+1:-4] )
    # print ( topos )
    with open ( "%sbestSRs.md" % Dir, "wt" ) as g:
        g.write ( "# plots of best expected signal regions\n" )
        g.write ( "as of %s\n" % time.asctime() )
        g.write ( "checkout also the [ratio plots](README.md)\n" )
        tsorted = list(topos)
        tsorted.sort() ## why???
        for topo in tsorted:
            g.write ( "\n## Topology: %s\n\n" % topo )
            g.write ( "| andre | suchi |\n" )
            for f in files:
                src = f.replace( Dir, "" )
                if not topo in src:
                    continue
                g.write ( '| <img src="%s" /> ' % ( src ) )
            g.write ( "|\n" )
    cmd = "cd ../../smodels.github.io/; git commit -am 'automated commit' ; git push"
    o = ""
    if push:
        o = subprocess.getoutput ( cmd )
    print ( "[drawBestSRs] cmd %s: %s" % (cmd, o ) )
    
if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser( description = "plot relative statistical error of best signal region" )
    argparser.add_argument ( "-d", "--dbpath", help="path to database [../../smodels-database/]", type=str,
                             default="../../smodels-database/" )
    argparser.add_argument ( "-a", "--analysis", 
            help="analysis name, like the directory name [CMS-EXO-13-006-eff]", 
            type=str, default="CMS-EXO-13-006-eff" )
    argparser.add_argument ( "-v", "--validationfile", 
            help="validation file [THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py]", 
            type=str, default="THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py" )
    argparser.add_argument ( "-D", "--default", action="store_true", 
            help="default run on arguments. currently set to be the exo 13 006 plots" )
    argparser.add_argument ( "-c", "--copy", action="store_true", 
            help="cp to smodels.github.io, as it appears in https://smodels.github.io/ratioplots/" )
    argparser.add_argument ( "-p", "--push", action="store_true", 
            help="commit and push to smodels.github.io, as it appears in https://smodels.github.io/ratioplots/" )
    args = argparser.parse_args()
    if not args.default and not args.analysis.endswith("-eff"):
        print ( "[drawBestSRs] warning, analysis name does not end with -eff, might an error" )
    if args.default:
        for a in [ "CMS-EXO-13-006-andre", "CMS-EXO-13-006-eff" ]:
            for v in [ "THSCPM1b_2EqMassAx_EqWidthAy.py", "THSCPM3_2EqMassAx_EqMassBy**.py", "THSCPM4_*.py", "THSCPM5_2EqMassAx_EqMassBx-100_EqMassCy*.py", "THSCPM6_EqMassA__EqmassAx_EqmassBx-100_Eqma*.py", "THSCPM8_2EqMassAx*.py", "THSCPM2b_*.py" ]:
                print ( "[drawBestSRs:default] now drawing %s:%s" % (a, v ) )
                ipath = getPathName ( args.dbpath, a, v )
                fname = draw( ipath )
                if args.copy:
                    cmd = "cp %s ../../smodels.github.io/ratioplots/" % fname
                    o = subprocess.getoutput ( cmd )
                    print ( "[drawBestSRs] cmd %s: %s" % (cmd, o ) )
    else:
        ipath = getPathName ( args.dbpath, args.analysis, args.validationfile )
        fname = draw( ipath )
        if args.copy:
            cmd = "cp %s ../../smodels.github.io/ratioplots/" % fname
            o = subprocess.getoutput ( cmd )
            print ( "[drawBestSRs] cmd %s: %s" % (cmd, o ) )
    if args.copy:
        writeBestSRs( args.push )
