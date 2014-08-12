#!/usr/bin/env python

"""
.. module:: referenceXSecs
     :synopsis: Module to wrap the CMS reference cross-sections. 

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>


"""

import setPath  # # set to python path for smodels
import logging
import argparse
import sys
import types

logger = logging.getLogger(__name__)

def xSecs(sqrt):
    """Reads the txt files and produces the python arrays for 7TeV and 8TeV.
    
    """
    
    if not sqrt in ['7TeV', '8TeV']:
        logger.error('No valid square root %s!' %sqrt)
        sys.exit()
    
    
    outFileName = 'referenceXSecs-%s.py' %sqrt
    inFileName = 'xSections%s.txt' %sqrt
    values = readFile(inFileName)
    return values
        
def readFile(fileName):
    f = open('./references/%s' %fileName, 'r')
    lines = f.readlines()
    values = []
    for line in lines:
        line = [l for l in line.split()]
        try:
            values.append([float(line[0].strip()), float(line[2].strip())])
        except ValueError: continue
    f.close()    
    return values