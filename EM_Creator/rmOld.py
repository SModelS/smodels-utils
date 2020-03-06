#!/usr/bin/env python3

import glob, os, time, pickle, subprocess

def daysFromNow ( timestamp ):
    """ compute how many days in the past from now """
    t0=time.time()
    return ( t0 - timestamp ) / 60. / 60. / 24.

def pprint( sdirs ):
    """ print oldest dirs """
    keys = list(sdirs.keys())
    keys.sort()
    for k in keys[:20]:
        d = daysFromNow(k)
        print ( "%25s: %.1f days old" % ( sdirs[k], d ) )

def savePickle ( sdirs ):
    """ write to pickle """
    f=open("stats.pcl","wb" )
    pickle.dump ( sdirs, f )
    f.close()

def createStats():
    """ produce the stats from scratch """
    t0=time.time()
    sdirs = {}
    files = glob.glob("T*")
    for f in files:
        if "TODO" in f:
            continue
        ms = os.stat ( f ).st_mtime
        sdirs[ms]=f
    """
    files = glob.glob("ma5/ANA_T*")
    for f in files:
        ms = os.stat ( f ).st_mtime
        sdirs[ms]=f
    """
    return sdirs

def loadPickle():
    """ load from pickle """
    f=open("stats.pcl","rb" )
    sdirs = pickle.load ( f )
    f.close()
    return sdirs

def rmOlderThan( sdirs, days ):
    """ remove all older than <days> days """
    keys = list(sdirs.keys())
    keys.sort()
    for k in keys[:20]:
        d = daysFromNow(k)
        if d > days:
            print ( "removing %s: %.1f days old." % ( sdirs[k], d ) )
            cmd = "rm -rf %s" % sdirs[k]
            o = subprocess.getoutput ( cmd )
            print ( "   %s: %s" % ( cmd, o ) )
            cmd = "rm -rf ma5/ANA_%s" % sdirs[k] 
            o = subprocess.getoutput ( cmd )
            print ( "   %s: %s" % ( cmd, o ) )

def main():
    if os.path.exists ( "stats.pcl" ):
        sdirs = loadPickle()
    else:
        sdirs = createStats()
        savePickle ( sdirs )
    pprint ( sdirs )
    rmOlderThan ( sdirs, 30. )

main()
