#!/usr/bin/env python3

""" produce NLL entries with a given k-factor in a tarball """

import shutil
import tempfile
import argparse
import pyslha
import os
import subprocess
import glob

def addKFactor ( fname, kfactor ):
    """ add NLL entries with given kfactor to tarball 
    :param fname: name of file
    :param kfactor: e.g. 1.2
    """
    slhaData = pyslha.readSLHAFile(fname )
    sxsecs = { 8000: {}, 13000: {} }
    for k,xsecs in slhaData.xsections.items():
        pids = k[2:]
        for x in xsecs.xsecs:
            sqrts = int ( float ( x.sqrts ) )
            order = x.qcd_order_str
            if "NL" in order:
                print ( f"error: found NLO (or higher) xsecs in file {fname}. skip" )
                return
            value = x.value
            sxsecs[sqrts][pids]=value*kfactor
    # print ( f"adding to {fname}" )
    f = open ( fname, "at" )
    f.write ( "\n" )
    for sqrts,xsecs_ in sxsecs.items():
        for pids,value in xsecs_.items():
            f.write ( f"XSECTION  {sqrts:.3G}  2212 2212 2 {pids[0]} {pids[1]} ## added by addKFactor k={kfactor} [pb]\n" )
            f.write ( f"  0  2  0  0  0  0    {value:.5G} SModelSv2.1.2\n\n" )

    f.close()
    return

def add ( tarball, kfactor, keep ):
    """ add NLL entries with given kfactor to tarball 
    :param tarball: e.g. TChiWZ_Cd2.tar.gz
    :param kfactor: e.g. 1.2
    """
    if not os.path.exists ( tarball ):
        print ( f"error: tarball {tarball} does not exist" )
        return
    D = tempfile. mkdtemp ( prefix= "kf_", dir = "./" )
    cmd = f"cp {tarball} {D}"
    subprocess.getoutput ( cmd )
    cmd = f"cd {D}; tar xzvf {tarball}"
    subprocess.getoutput ( cmd )
    files = glob.glob ( f"{D}/T*.slha" )
    for f in files:
        addKFactor ( f, kfactor )
    cmd = f"cd {D}; tar czvf ../{tarball} T*.slha"
    subprocess.getoutput ( cmd )
    if not keep:
        cmd = "cd {D}; rm T*.slha"
        subprocess.getoutput ( cmd )
        shutil.rmtree ( D )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description="adds NLL xsec entries with given k factors to tarballs")
    argparser.add_argument ( '-k', nargs='?', help='k-factor [1.2]',
        type=float, default=1.2 )
    argparser.add_argument ( '-t', '--tarball', nargs='?', help='tarball [TChiWZ_Cd2.tar.gz]',
        type=str, default='TChiWZ_Cd2.tar.gz' )
    argparser.add_argument( '--keep', action='store_true',
        help="keep temporary files" )
    args=argparser.parse_args()
    add ( args.tarball, args.k, args.keep )
