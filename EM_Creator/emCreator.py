#!/usr/bin/env python3

"""
.. module:: emCreator
        :synopsis: code that extracts the efficiencies from MadAnalysis,
                   and assembles an eff map.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import os, sys, colorama, subprocess, shutil
import bakeryHelpers

class emCreator:
    def __init__ ( self, analyses, topo, njets ):
        self.analyses = analyses
        self.topo = topo
        self.njets = njets

    def info ( self, *msg ):
        print ( "%s[emCreator] %s%s" % ( colorama.Fore.YELLOW, " ".join ( msg ), \
                   colorama.Fore.RESET ) )

    def debug( self, *msg ):
        pass

    def msg ( self, *msg):
        print ( "[emCreator] %s" % " ".join ( msg ) )

    def error ( self, *msg ):
        print ( "%s[emCreator] %s%s" % ( colorama.Fore.RED, " ".join ( msg ), \
                   colorama.Fore.RESET ) )
        sys.exit()

    def extract ( self, masses ):
        topo = self.topo
        njets = self.njets
        process = "%s_%djet" % ( topo, njets )
        dirname = bakeryHelpers.dirName ( process, masses )
        summaryfile = "ma5/ANA_%s/Output/CLs_output_summary.dat" % dirname
        if not os.path.exists ( summaryfile):
            self.error ( "could not find ma5 summary file %s. Skipping." % summaryfile )
            return {}
        f=open(summaryfile,"r")
        lines=f.readlines()
        f.close()
        effs={}
        for line in lines:
            p=line.find("#")
            if p>=0:
                line=line[:p]
            line=line.strip()
            if len(line)==0:
                continue
            if "control region" in line:
                continue
            line = line.replace("signal region","signal_region")
            line = line.replace("control region ","control_region_")
            line = line.replace("signal region ","signal_region_" )
            line = line.replace("control region","control_region" )
            line = line.replace("150-1","150 -1")
            tokens=line.split()
            dsname,ananame,sr,sig95exp,sig95obs,pp,eff,statunc,systunc,totunc=tokens
            eff=float(eff)
            if eff == 0.:
                # print ( "zero efficiency for", ananame,sr )
                continue
            if not ananame in effs:
                effs[ananame]={}
            effs[ananame][sr]=eff
        return effs

    def exe ( self, cmd ):
        self.msg ( "now execute: %s" % cmd )
        ret = subprocess.getoutput ( cmd )
        if len(ret)==0:
            return
        # maxLength=60
        maxLength=560
        if len(ret)<maxLength:
            self.msg ( " `- %s" % ret )
            return
        self.msg ( " `- %s" % ( ret[-maxLength:] ) )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='efficiency map extractor.')
    argparser.add_argument ( '-j', '--njets', help='number of ISR jets [1]',
                             type=int, default=0 )
    argparser.add_argument ( '-t', '--topo', help='topology [T2]',
                             type=str, default="T2" )
    argparser.add_argument ( '-a', '--analyses', help='analyses, comma separated [atlas_sus_2016_07]',
                             type=str, default="atlas_susy_2016_07" )
    mdefault = "all"
    argparser.add_argument ( '-m', '--masses', help='mass ranges, comma separated list of tuples. One tuple gives the range for one mass parameter, as (m_first,m_last,delta_m). m_last and delta_m may be ommitted. "all" means, try to find out yourself [%s]' % mdefault,
                             type=str, default=mdefault )
    args = argparser.parse_args()
    if args.masses == "all":
        masses = bakeryHelpers.getListOfMasses ( args.topo, args.njets )
    else:
        masses = bakeryHelpers.parseMasses ( args.masses )
    creator = emCreator( args.analyses, args.topo, args.njets )
    effs={}
    for m in masses:
        eff = creator.extract( m )
        for k,v in eff.items():
            if not k in effs:
                effs[k]={}
            effs[k][m]=v
    print ( effs )
