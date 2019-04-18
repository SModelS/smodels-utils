#!/usr/bin/env python3

"""
.. module:: emCreator
        :synopsis: code that extracts the efficiencies from MadAnalysis,
                   and assembles an eff map.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import os, sys, colorama, subprocess, shutil

class emCreator:
    def __init__ ( self ):
        pass

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

    def extract ( self ):
        summaryfile = "ma5/ANALYSIS_0/Output/CLs_output_summary.dat"
        if not os.path.exists ( summaryfile):
            self.error ( "could not find ma5 summary file %s" % summaryfile )
            sys.exit()
        f=open(summaryfile,"r")
        lines=f.readlines()
        f.close()
        for line in lines:
            p=line.find("#")
            if p>=0:
                line=line[:p]
            line=line.strip()
            if len(line)==0:
                continue
            line = line.replace("signal region","signal_region").
            line = line.replace("control region ","control_region_")
            line = line.replace("signal region ","signal_region_" )
            line = line.replace("control region","control_region" )
            line = line.replace("SRSS07_lPP_Njets0_MT0to100_PTll50toInf_MET100to150-1","SRSS07_lPP_Njets0_MT0to100_PTll50toInf_MET100to150 -1")
            line = line.replace("SRSS07_lMM_Njets0_MT0to100_PTll50toInf_MET100to150-1","SRSS07_lMM_Njets0_MT0to100_PTll50toInf_MET100to150 -1")
            tokens=line.split()
            print ( "entry", tokens, len(tokens) )
            dsname,ananame,sr,sig95exp,sig95obs,pp,eff,statunc,systunc,totunc=tokens

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
    creator = emCreator()
    creator.extract()
