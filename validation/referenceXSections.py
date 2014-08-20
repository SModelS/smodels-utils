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
from smodels.tools.physicsUnits import pb, fb, GeV

logger = logging.getLogger(__name__)

def xSecs(sqrt, topology):
    """Reads the txt files and produces the python arrays for 7TeV and 8TeV.
    
    """
    
    if not sqrt in ['7TeV', '8TeV']:
        logger.error('No valid square root %s!' %sqrt)
        sys.exit()
    
    
    outFileName = 'referenceXSecs-%s-%s.py' %(sqrt, topology)
    if topology[:2] == 'T1': production = 'T1'
    elif topology[:2] == 'T2': production = 'T2'
    elif topology[:4] == 'TChi': production = 'TChi'
    elif topology[:5] == 'TSlep': production = 'TSlep'   
    else:
        logger.error('Production for topology %s is unknown!' %topology)
        return None
    inFileName = 'xSections%s-%s.txt' %(sqrt, production)
    values = readFile(inFileName)
    return values
        
def readFile(fileName):
    try:
        f = open('./references/%s' %fileName, 'r')
    except IOError:
        logger.error('There are no reference cross sections: %s' \
        %(fileName))
        return None
    lines = f.readlines()
    values = []
    for line in lines:
        line = [l for l in line.split()]
        i = 1
        if 'GeV' in line[1]: i = 2
        try:
            values.append([float(line[0].strip()) * GeV, float(line[i].strip()) * pb])
        except ValueError: continue
    f.close()    
    return values