#!/usr/bin/env python3

""" check if slha files have NLO cross sections. compute if they dont. """

import subprocess
import sys
import glob
import random
import pyslha
import IPython
import math

def process ( files, pretend ):
    total = len (files)
    not_lo, not_nlo = 0, 0
    ssmultipliers = ""
    ## for thscpm6
    if True:
        ## suppress everything but ( '*200000?', '*100000?' )
        D = { ('*1000022', '*' ): 0., ('*1000023', '*' ): 0. }
        ssmultipliers = ' --ssmultipliers "%s" ' % str(D)
        # print ( "ssm", ssmultipliers )
    for f in files:
        has_lo  = False
        has_nlo = False
        p = pyslha.readSLHAFile ( f )
        for k,xsecs in p.xsections.items():
            for x in xsecs.xsecs:
                order = x.qcd_order_str
                if "LO" in order or "Born" in order: ## FIXME why??
                    has_lo = True
                if "NL" in order:
                    has_nlo=True
                    break
        if not has_nlo:
            if not has_lo:
                print ( "%s has neither LO nor NLO" % f )
                cmd = "~/git/smodels/smodelsTools.py xseccomputer -e 50000 -N -P -8 %s -f %s" % ( ssmultipliers, f )
                if pretend:
                    pass
                else:
                    print ( cmd )
                    a = subprocess.getoutput ( cmd )
                    print ( a )
                not_lo += 1
            else:
                print  ("%s has only LO" % f )
                cmd = "~/git/smodels/smodelsTools.py xseccomputer -e 50000 -N -P -8 -O -f %s" % f
                if pretend:
                    pass
                else:
                    print ( cmd )
                    a = subprocess.getoutput ( cmd )
                    print ( a )
                not_nlo += 1

    print ( "%d/%d with NLL." % ( total - not_lo - not_nlo, total ) )
    print ( "%d/%d with LO only." %  ( not_nlo, total ) )
    print ( "%d/%d with no xsecs." % ( not_lo, total ) )

def main():
    import argparse, multiprocessing
    argparser = argparse.ArgumentParser()

    argparser.add_argument('-f', '--files', 
                           help = 'file pattern to glob [T*.slha]',
                           type=str,default = "T*.slha" )
    argparser.add_argument('-p', '--pretend', help="pretend, dry-run",
                           action="store_true" )
    argparser.add_argument('-n', '--nprocesses', help="number of processes [1]",
                           type=int, default = 1 )
    args = argparser.parse_args()
    pretend = False
    pat = "T*slha"
    pretend = args.pretend
    pat = args.files
    print ( "checking for %s" % pat )

    files = glob.glob ( pat )
    random.shuffle ( files )

    if args.nprocesses == 1: ## multiprocess
        process ( files, pretend )
        return
    p = multiprocessing.Pool ( args.nprocesses )
    ps = []
    delta = int(math.ceil(len(files)/args.nprocesses))
    for i in range(args.nprocesses):
        chunk = files[delta*i:delta*(i+1)]
        p=multiprocessing.Process(target=process, args=(chunk,pretend) )
        p.start()
        ps.append ( p )
    for p in ps:
        p.join()

main()
