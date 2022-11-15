#!/usr/bin/env python


"""
.. module:: reWriteUnits
   :synopsis: Module to convert cross-sections in SLHA files from fb to pb

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys,os,glob

sys.path.append('../../smodels/')

from smodels.theory import crossSection
from smodels.tools import xsecComputer
from smodels.tools.physicsUnits import fb


def reWriteFile(slhafile):
    """
    Rewrites the cross-section in a SLHA file
    """

    #Read original cross-sections
    xsecs = crossSection.getXsecFromSLHAFile(slhafile, xsecUnit = fb)

    #Remove cross-sections from file
    sFile = open(slhafile,'r')
    sData = sFile.read()
    sData = sData[:sData.find('XSECTION')]
    sFile.close()
    os.remove(slhafile)
    sFile = open(slhafile,'w')
    sFile.write(sData)
    sFile.close()

    #Write original cross-sections, but now in pb
    xsecComputer.addXSecToFile(xsecs,slhafile,comment = '(unit = pb)')


def reWriteFolder(slhadir):

    for slhafile in glob.iglob(os.path.join(slhadir,'*')):
        if not os.path.isfile(slhafile): continue
        f = open(slhafile,'r')
        fdata = f.read()
        f.close()
        #Skip non-SLHA files
        if not 'BLOCK MASS' in fdata: continue
        if not 'XSECTION' in fdata: continue
        #Skip files already converted:
        if '(unit = pb)' in fdata: continue

        reWriteFile(slhafile)



if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--directory', help = 'rewrite units of all slha files in directory',
                                           default = None)
    argparser.add_argument('-f', '--file', help = 'rewrite units of given slha file',
                                           default = None)
    args = argparser.parse_args()
    if args.directory:
    #slhadir = '/home/walten/git/smodels-utils/slha/T1tttt/'
        reWriteFolder(args.directory)
    if args.file:
        reWriteFile(args.file )
