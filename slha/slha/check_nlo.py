#!/usr/bin/env python3

""" check if slha files have NLO cross sections. compute if they dont. """

import subprocess
import sys
import glob
import random
import pyslha
import IPython
import math

def process ( files, pretend, ssmultipliers, pythia, nevents, sqrtS ):
    """ process the files, i.e. compute xsecs for them 
    :param pretend: pretend, just count, dont actually do anything
    :param ssmultipliers: filter on signal strength multipliers
                          used mostly to turn off certain production channels
    :param pythia: pythia version to use (6 or 8)
    :param nevents: number of events to produce
    :param sqrtS: compute for sqrts (TeV)
    """
    total = len (files)
    not_lo, not_nlo, not_13, not_8 = 0, 0, 0, 0
    ssms = ""
    ## for thscpm6
    if ssmultipliers not in [ None, "", "None", "none" ]:
        ## suppress everything but ( '*200000?', '*100000?' )
        # D = { ('*1000022', '*' ): 0., ('*1000023', '*' ): 0. }
        ssms = ' --ssmultipliers "%s" ' % str(ssmultipliers)
        # print ( "ssm", ssmultipliers )
    for f in files:
        has_lo  = False
        has_nlo = False
        has_13 = False
        has_8 = False
        p = pyslha.readSLHAFile ( f )
        for k,xsecs in p.xsections.items():
            for x in xsecs.xsecs:
                sqrts = x.sqrts
                order = x.qcd_order_str
                if abs ( sqrts - 13000. ) < 1e-4:
                    has_13 =True
                if abs ( sqrts - 8000. ) < 1e-4:
                    has_8 =True
                if "LO" in order or "Born" in order: ## FIXME why??
                    has_lo = True
                if "NL" in order:
                    has_nlo=True
        xsecc = "~/git/smodels/smodelsTools.py xseccomputer"
        ms=""
        if sqrtS in [ 8 ]:
            ms=" -s 8"
        if sqrtS in [ 13 ]:
            ms=" -s 13"
        xsecc = xsecc + ms
        if not has_nlo:
            if not has_lo:
                print ( "%s has neither LO nor NLO" % f )
                cmd = "%s -e %d -N -P -%d %s -f %s" % \
                       ( xsecc, nevents, pythia, ssms, f )
                if pretend:
                    pass
                else:
                    print ( cmd )
                    a = subprocess.getoutput ( cmd )
                    print ( a )
                not_lo += 1
            else:
                print  ("%s has only LO" % f )
                cmd = "%s -e %d -N -P -%d -O -f %s" % \
                       ( xsecc, nevents, pythia, f )
                if pretend:
                    pass
                else:
                    print ( cmd )
                    a = subprocess.getoutput ( cmd )
                    print ( a )
                not_nlo += 1
        if not has_13 and sqrtS in [ 0, 13 ]:
            print ( "%s has not sqrts 13 " % f )
            cmd = "%s -e %d -N -P -%d %s -f %s" % \
                   ( xsecc, nevents, pythia, ssms, f )
            if pretend:
                pass
            else:
                print ( cmd )
                a = subprocess.getoutput ( cmd )
                print ( a )
            not_13 += 1
        # print ( "here sqrts", sqrts, "has8", has_8 )
        if not has_8 and sqrtS in [ 0, 8 ]:
            print ( "%s has not sqrts 8 " % f )
            cmd = "%s -e %d -N -P -%d %s -f %s" % \
                   ( xsecc, nevents, pythia, ssms, f )
            if pretend:
                pass
            else:
                print ( cmd )
                a = subprocess.getoutput ( cmd )
                print ( a )
            not_8 += 1

    if pretend:
        print ( "%d/%d with NLL." % ( total - not_lo - not_nlo, total ) )
        print ( "%d/%d with LO only." %  ( not_nlo, total ) )
        if sqrtS in [ 0, 13 ]:
            print ( "%d/%d with no 13 TeV." %  ( not_13, total ) )
        if sqrtS in [ 0, 8 ]:
            print ( "%d/%d with no  8 TeV." %  ( not_8, total ) )
        print ( "%d/%d with no xsecs." % ( not_lo, total ) )

def zipThem ( files ):
    """ zip them up """
    topo = files[0][:files[0].find("_")]
    cmd = "tar czvf %s.tar.gz %s*slha" % ( topo, topo )
    print ( cmd )
    subprocess.getoutput ( cmd )

def main():
    import argparse, multiprocessing
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-f', '--files', 
                           help = 'file pattern to glob. if tarball given, then unpack and repack [T*.slha]',
                           type=str,default = "T*.slha" )
    argparser.add_argument('-P', '--pythia', 
                           help = 'pythia version to use [6]',
                           type=int, default = 6 )
    argparser.add_argument('-e', '--nevents', 
                           help = 'number of events [50000]',
                           type=int, default = 50000 )
    argparser.add_argument('-S', '--sqrts', 
                           help = 'sqrts: 0, 8, or 13. if 0, then 8 and 13. [0]',
                           type=int, default = 0 )
    argparser.add_argument('-s', '--ssmultipliers', 
                           help = 'supply a filter for signal strengths [None]',
                           type=str, default = None )
    argparser.add_argument('-p', '--pretend', help="pretend, dry-run",
                           action="store_true" )
    argparser.add_argument('-l', '--list_ssms', help="list useful ssm filters, then quit",
                           action="store_true" )
    argparser.add_argument('-n', '--nprocesses', help="number of processes [1]",
                           type=int, default = 1 )
    args = argparser.parse_args()
    repack = False
    if args.files.endswith(".tar.gz"):
        files = glob.glob("T*slha")
        if len(files)>0:
            print ( "[check_nlo] error, you ask me to unpack a tarball but there are slha files in the directory." )
            sys.exit()
        ## remove cruft slha files, unpack tarball
        cmd = "rm -rf T*slha" 
        subprocess.getoutput ( cmd )
        cmd = "tar xzvf %s" % args.files
        subprocess.getoutput ( cmd )
        args.files = "T*slha"
        repack = True
    if args.list_ssms:
        print ( "Some sensible -s arguments" )
        print ( "No neutralino production" )
        print ( "{ ('*1000022', '*' ): 0., ('*1000023', '*' ): 0. }" )
        print ( "No weakino production" )
        print ( "{ ('*100002?', '*' ): 0. }" )
        sys.exit()
    pretend = False
    pat = "T*slha"
    pretend = args.pretend
    pat = args.files
    print ( "[check_nlo] checking for %s" % pat )

    files = glob.glob ( pat )
    random.shuffle ( files )

    if args.nprocesses == 1: ## multiprocess
        process ( files, pretend, args.ssmultipliers, args.pythia, args.nevents, args.sqrts )
        return
    p = multiprocessing.Pool ( args.nprocesses )
    ps = []
    delta = int(math.ceil(len(files)/args.nprocesses))
    for i in range(args.nprocesses):
        chunk = files[delta*i:delta*(i+1)]
        p=multiprocessing.Process(target=process, args=(chunk,pretend,args.ssmultipliers,args.pythia,args.nevents, args.sqrts) )
        p.start()
        ps.append ( p )
    for p in ps:
        p.join()
    if repack:
        zipThem ( args.files )

main()
