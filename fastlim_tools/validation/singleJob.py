#!/usr/bin/env python

"""
.. module:: runFiles
   :synopsis: Used to run fastlim for a list of SLHA files using N cores

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""
import sys,os
sys.path.append('../runTools')
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
from gridFastlim import runFastlimFor
from gridSmodels import runSmodelSFor
import argparse
fastlimdir = os.path.join(os.getcwd(),'../fastlim-1.0/')
databasePath = os.path.join(home,'smodels-database')

if __name__ == "__main__":
    
    argparser = argparse.ArgumentParser(description='Runs fastlim/smodels and generate .sms files')
    argparser.add_argument('dir', help='name of SLHA folder containing the SLHA files')
    argparser.add_argument('-Ncore', help='total number of cores to be used', type=int, default=1)
    argparser.add_argument('-Tool', help='Tool to be used (fastlim/smodels)', required=True)
    argparser.add_argument('-Tout', help='Time out limit (in seconds) for a single process', type=float, default=1000)
    args = argparser.parse_args()    
    slhadir = args.dir
    np = args.Ncore
    tout = int(args.Tout)
    if args.Tool == 'fastlim':
        #Runs Fastlim on slhaDir to generate the output as .sms files
        result = runFastlimFor(slhadir,fastlimdir,None,None,np,tout)
        print result
    elif args.Tool == 'smodels':
        #Runs SmodelS on slhaDir to generate the output as .sms files
        result = runSmodelSFor(slhadir,databasePath,None,None,np,tout)
        print result
    sys.exit()