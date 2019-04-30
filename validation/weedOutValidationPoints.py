#!/usr/bin/env python3

""" Thin out validation points, i.e. remove points that 
are too close to other points. """

import subprocess
import argparse
import glob, os, sys, time, pickle
import tempfile

def distance ( d1, d2 ):
    ret=0.
    for x1,x2 in zip(d1,d2):
        ret += (x1-x2)*(x1-x2)
    return ret

def mkstring ( d ):
    return "_".join ( map(str,map(int,d)))

def weed ( dists, maxDistance ):
    keepIt = {}
    t0=time.time()
    nWeeded = 0
    for x,d1 in enumerate(dists):
        if x % 200 == 0:
            print ( "Checking point #%d %.1f [s]. weeded: %d" % (x,time.time()-t0, nWeeded ) )
        sd1=mkstring(d1)
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
                keepIt[sd2]=False
                nWeeded+=1
                # break
    ret=[]
    for k,v in keepIt.items():
        if v:
            ret.append(k)
    return ret

def main():
    ap = argparse.ArgumentParser(description="Weed out validation tarballs.")
    ap.add_argument ( '-t', '--topo', 
            help='specify the topology to be thinned out [T5WW].',
            default = 'T5WW', type = str )
    ap.add_argument ( '-d', '--distance', 
            help='max tolerated distance (GeV) from other point [10.]',
            default = 10., type = float )
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
    print ( "%d points before weeding." % ( len(dists ) ) )
    t0=time.time()
    weeded = weed ( dists, args.distance**2 )
    print ( "%d points after weeding." % ( len(weeded ) ) )
    print ( "(Took %d seconds)" % ( time.time() - t0 ) )
    a = open("weed.pcl","wb")
    pickle.dump(weeded,a)
    a.close()
    for fname in files:
        f = fname.replace(args.topo+"_","").replace(".slha","")
        f = f.replace(tempdir+"/","")
        if f not in weeded:
            subprocess.getoutput ( "rm %s/%s_%s.slha" % ( tempdir, args.topo, f ) )
    subprocess.getoutput ( "cd %s; tar czvf ../%s.tar.gz %s*slha" % ( tempdir, args.topo, args.topo ) )
    subprocess.getoutput ( "rm -rf %s" % tempdir )


if __name__ == "__main__":
    main()
