#!/usr/bin/env python3

import glob
from datetime import datetime, timedelta

def extractTime ( timestring ):
    """ extract the time from line, 
        e.g. [protomodel-18:00:00] .... """
    line = timestring
    for i in [ "protomodel", "manipulator", "randomWalker", "predictor", "hiscore" ]:
        line = line.replace( f"[{i}-", "" )
    p = line.find("]")
    line = line[:p]
    ps = line.rfind(" ")
    if ps > 0:
        line = line[ps+1:]
    return line

def timeMe():
    base = "/scratch-cbe/users/wolfgan.waltenberger/"
    # rundirs = f"{base}/rundir.real*"
    rundirs = f"{base}/rundir.signal*"
    rundirs = f"{base}/rundir.fake*"
    files = glob.glob ( f"{rundirs}/walker?.log" )
    files += glob.glob ( f"{rundirs}/walker??.log" )
    files += glob.glob ( f"{rundirs}/walker???.log" )
    deltas = []
    for f in files:
        h = open ( f, "rt" )
        lines = h.readlines()
        h.close()
        s1 = extractTime ( lines[0] )
        s2 = extractTime ( lines[-1] )
        FMT = '%H:%M:%S'
        t1 = datetime.strptime(s1, FMT)
        t2 = datetime.strptime(s2, FMT)
        if t2 < t1:
            t2 += timedelta(1)
        tdelta = t2 - t1
        deltas.append ( tdelta )
    import numpy
    print ( "avg:", numpy.mean ( deltas ), "min:", numpy.min ( deltas ), \
            "max:", numpy.max ( deltas) )


timeMe()
