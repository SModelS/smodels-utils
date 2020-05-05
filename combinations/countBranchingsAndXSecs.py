#!/usr/bin/env python3

""" simple script to count the average number of non-trivial branchings per particle,
    in the PMSSM """

import pyslha, glob, IPython, numpy
from smodels.theory.crossSection import getXsecFromSLHAFile
from smodels.tools.physicsUnits import fb, pb, TeV

def countPerFile ( f ):
    slha = pyslha.readSLHAFile( f )
    decays = slha.decays.items()
    nbranchings = {}
    for mpid,particle in decays:
        if abs(mpid)<99999:
            continue
        nbr=0
        for decay in particle.decays:
            dpids = decay.ids
            br = decay.br
            if br > 0.01 and br < 1.:
                nbr+=1
        if nbr>0: ## have to add up to 1, so remove one!
            nbr -= 1
        nbranchings[mpid]=nbr
    nxsecs = {}
    for pid in nbranchings.keys():
        nxsecs[pid]=0
    xsecs = getXsecFromSLHAFile ( f )
    for xsec in xsecs:
        weight = xsec.value.asNumber ( fb ) ## the weight in fb
        if weight < 0.01: ## at least 0.01*fb
            continue
        order = xsec.info.order
        if order > 0: ## no double count b/c of order
            continue
        sqrts = xsec.info.sqrts.asNumber ( TeV )
        if abs(sqrts-13.) > 1e-5: # only look at 13 tev
            continue
        pids = xsec.pid
        for pid in pids:
            if abs(pid) not in nxsecs:
                continue
            nxsecs[abs(pid)]+=1
    # IPython.embed()
    return nbranchings, nxsecs

def count( path ):
    files = glob.glob("%s/*.slha" % path )
    brstats,xsecstats = [], []
    for f in files:
        nbranchings, nxsecs = countPerFile( f )
        for pid,n in nbranchings.items():
            brstats.append ( n )
        for pid,n in nxsecs.items():
            xsecstats.append ( n )
    print ( "Scanning over %d files, %d/%d particles" % \
            ( len(files), len(brstats), len(xsecstats) ) )
    print ( "Average number of branchings %.2f +/- %.2f " % \
            ( numpy.mean ( brstats ), numpy.std ( brstats ) ) )
    print ( "Average number of xsecs %.2f +/- %.2f" % \
            ( numpy.mean ( xsecstats ), numpy.std ( xsecstats ) ) )

if __name__ == "__main__":
    count( "pmssm/" )
    # Scanning over 323 files, 9044/9044 particles
    # Average number of branchings 3.11 +/- 2.68 
    # Average number of xsecs 1.74 +/- 3.89
