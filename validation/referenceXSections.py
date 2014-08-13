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
import os

logger = logging.getLogger(__name__)

def xSecs(sqrt, topology):
    """Reads the txt files and produces the python arrays for 7TeV and 8TeV.
    
    """
    
    if not sqrt in ['7TeV', '8TeV']:
        logger.error('No valid square root %s!' %sqrt)
        sys.exit()
    
    
    outFileName = 'referenceXSecs-%s-%s.py' %(sqrt, topology)
    inFileName = 'xSections%s-%s.txt' %(sqrt, topology)
    values = readFile(inFileName)
    return values
        
def readFile(fileName):
    try:
        f = open('./references/%s' %fileName, 'r')
    except IOError:
        logger.error('There are no reference cross sections for: %s-%s' \
        %(topology, sqrt))
        return None
    lines = f.readlines()
    values = []
    for line in lines:
        line = [l for l in line.split()]
        try:
            values.append([float(line[0].strip()), float(line[2].strip())])
        except ValueError: continue
    f.close()    
    return values