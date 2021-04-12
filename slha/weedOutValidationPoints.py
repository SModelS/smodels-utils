#!/usr/bin/env python3

""" Thin out validation points, i.e. remove points that 
are too close to other points. """

import subprocess
import argparse
import glob, os, sys, time, pickle
import tempfile
from math import sqrt

def distance ( d1, d2 ):
    ret=0.
    for x1,x2 in zip(d1,d2):
        ret += (x1-x2)*(x1-x2)
    return ret

def mkstring ( d ):
    return "_".join ( map(str,map(int,d)))

def weed ( dists, maxDistance, massgaps, verbose, keep60s = False ):
    """ weed out points
    :param keep60s: if true, then keep points with m(LSP)=60 GeV
    :returns: points that survived the weeding
    """
    if len(dists)==0:
        return
    keepIt = {}
    t0=time.time()
    nWeeded = 0
    mgaps = [0.] * (int(len(dists[0])/2.)-1)
    if massgaps != "":
        mgaps = eval(massgaps)
    print ( "[weed] massgap considered", mgaps )
    for x,d1 in enumerate(dists):
        if x % 200 == 0:
            print ( "Checking point #%d %.1f [s]. weeded: %d" % (x,time.time()-t0, nWeeded ) )
        sd1=mkstring(d1)
        if keep60s and abs ( d1[2] - 60. ) < 1e-5:
            ## keep all at mlsp=60
            keepIt[sd1]=True
        if sd1 in keepIt: ## can only be false
            continue
        nhalf = int(len(d1)/2)
        for idx,dcur in enumerate(d1[:nhalf]):
            if idx == 0:
                continue
            if dcur >= d1[idx-1]:
                if verbose:
                    print ( "Inverted masses %s" % d1 )
                keepIt[sd1]=False
                nWeeded+=1
                break
            if dcur > d1[idx-1] - mgaps[idx-1]:
                if verbose:
                    print ( "Massgap not fulfilled %s" % d1 )
                keepIt[sd1]=False
                nWeeded+=1
                break
        dhalf = d1[nhalf:]
        for idx,dcur in enumerate(dhalf):
            if idx == 0:
                continue
            if dcur >= dhalf[idx-1]:
                if verbose:
                    print ( "Inverted masses %s" % d1 )
                keepIt[sd1]=False
                nWeeded+=1
                break
            if dcur > dhalf[idx-1] - mgaps[idx-1]:
                if verbose:
                    print ( "Massgap not fulfilled %s" % d1 )
                keepIt[sd1]=False
                nWeeded+=1
                break
        if sd1 in keepIt: ## can only be false
            continue
        keepIt[sd1]=True
        # maxi = min(len(dists),x+1000)
        maxi = len(dists)
        for y,d2 in enumerate(dists[x+1:maxi]):
            sd2 = mkstring(d2)
            if sd2 in keepIt:
                continue
            d= distance(d1,d2)
            if d < maxDistance:
                if verbose:
                    print ( "kick out %s: too close to %s (d=%.1f)." % (sd2,sd1,sqrt(d)) )
                keepIt[sd2]=False
                nWeeded+=1
                # break
    ret=[]
    for k,v in keepIt.items():
        if v:
            ret.append(k)
    return ret

def main():
    ap = argparse.ArgumentParser(description="Weed out validation tarballs in smodels-utils/slha/.")
    ap.add_argument ( '-t', '--topo', 
            help='specify the topology to be thinned out [T5WW].',
            default = 'T5WW', type = str )
    ap.add_argument ( '-d', '--distance', 
            help='minimum tolerated distance (GeV) from other point [24.]',
            default = 24., type = float )
    ap.add_argument ( '-g', '--massgaps', 
            help='require mass gaps, e.g. (0,80.). Used to make sure that some particle is onshell. E.g. (0,80.) is to acertain that a W in the second cascade is onshell. Auto means, guess from topo name. [auto]',
            default = "auto", type = str )
    ap.add_argument ( '-v', '--verbose', help='be verbose', action='store_true' )
    ap.add_argument ( '--keep60s', help='keep points with m(LSP)=60 GeV', 
                      action='store_true' )
    args = ap.parse_args()
    tarball = "../slha/%s.tar.gz" % args.topo
    if not os.path.exists ( tarball ):
        print ( "tarball %s does not exist." % tarball )
        sys.exit()
    tempdir = tempfile.mkdtemp ( dir="./" )
    subprocess.getoutput ( "cd %s; tar xzvf ../%s" % (tempdir, tarball ) )
    files = glob.glob("%s/%s*slha" % ( tempdir, args.topo ) )
    dists = []
    for fname in files:
        f = fname.replace(args.topo+"_","").replace(".slha","")
        f = f.replace(tempdir+"/","")
        tokens = list(map(float,f.split("_")))
        dists.append ( tokens )
    dists.sort()
    npoints=len(dists)
    print ( "%d points before weeding." % ( npoints ) )
    t0=time.time()
    massgaps = args.massgaps
    if massgaps == "auto":
        if args.topo in [ "T6WW", "T6WZh", "T5WW", "T5ZZ", "T6ZZ", "T5WZh" ]:
            massgaps = "(0.,80.)"
    if massgaps == "auto": ## still?
        massgaps = ""
    keep60s = args.keep60s # False
    weeded = weed ( dists, args.distance**2, massgaps, args.verbose, keep60s )
    print ( "%d points after weeding, from %d points before." % ( len(weeded ), npoints ) )
    print ( "(Took %d seconds)" % ( time.time() - t0 ) )
    #a = open("weed.pcl","wb")
    # pickle.dump(weeded,a)
    # a.close()
    for fname in files:
        f = fname.replace(args.topo+"_","").replace(".slha","")
        f = f.replace(tempdir+"/","")
        if f not in weeded:
            subprocess.getoutput ( "rm %s/%s_%s.slha" % ( tempdir, args.topo, f ) )
    subprocess.getoutput ( "cd %s; tar czvf ../%s.tar.gz %s*slha" % ( tempdir, args.topo, args.topo ) )
    subprocess.getoutput ( "rm -rf %s" % tempdir )
    print ( "To keep the changes (I wont do this automatically): " )
    cmd = "cp %s.tar.gz ../slha/" % args.topo
    print ( cmd )
    subprocess.getoutput ( "echo '%s' | xsel -i" % cmd )


if __name__ == "__main__":
    main()
