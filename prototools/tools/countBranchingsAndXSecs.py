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
        if weight < 0.001: ## at least 0.01*fb
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
    print ( "[countBranchingsAndXSecs] counting all %d files in %s" % ( len(files), path ) )
    if len(files)==0:
        print ( "[countBranchingsAndXSecs] error: no files found" )
        return
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
    import argparse
    argparser = argparse.ArgumentParser(
            description='count the numbers of branchings and xsecs in a directory of slha files' )
    argparser.add_argument ( '-d', '--directory',
            help='directory [slha/]',
            type=str, default="slha/" )
    args = argparser.parse_args()
    
    count( args.directory )
    """
    # Average number of branchings 3.68
    # Average number of xsecs 5.7
    results = [ ( 61370, 3.27, 6.04 ),
                ( 42039, 3.16, 6.15 ),
                ( 77981, 4.37, 4.91 ),
                ( 48703, 4.23, 5.94 ),
                ( 43680, 3.54, 5.55 ),
                ( 61370, 3.23, 6.04 ) ]
    Scanning over 43680 files, 1223040/1223040 particles
    Average number of branchings 3.54 +/- 4.38
    Average number of xsecs 5.55 +/- 8.16
    /home/lessa/pMSSM/data/Wino_excluded_slha
    Scanning over 36553 files, 1023484/1023484 particles
    Average number of branchings 3.43 +/- 4.37
    Average number of xsecs 5.14 +/- 8.43
    /home/lessa/pMSSM/data/Bino_allowed_slha
    Scanning over 61370 files, 1718360/1718360 particles
    Average number of branchings 3.23 +/- 4.27
    Average number of xsecs 6.04 +/- 8.98
    /home/lessa/pMSSM/data/Bino_excluded_slha
    Scanning over 42039 files, 1177092/1177092 particles
    Average number of branchings 3.16 +/- 4.24
    Average number of xsecs 6.15 +/- 9.54
    /home/lessa/pMSSM/data/Higgsino_allowed_slha
    Scanning over 77981 files, 2183468/2183468 particles
    Average number of branchings 4.37 +/- 5.36
    Average number of xsecs 4.91 +/- 7.56
    /home/lessa/pMSSM/data/Higgsino_excluded_slha
    Scanning over 48703 files, 1363684/1363684 particles
    Average number of branchings 4.23 +/- 5.55
    Average number of xsecs 5.94 +/- 9.00
    /home/lessa/pMSSM/data/Wino_allowed_slha
    """
