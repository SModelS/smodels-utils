#!/usr/bin/env python

"""
.. module:: validationPlot
     :synopsis: Module to coordinate the validation plot procedure. 

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>


"""

from __future__ import print_function
import setPath  # # set to python path for smodels
import logging
import types
import os
import sys
from smodels_tools.tools.databaseBrowser import Browser
import gridDataCreator
import validationPlots

logger = logging.getLogger(__name__)

def main():
    """Calls the unpacking module, gets all the topologies, gets all the analyses
    for one topology and checks for results. Calls the gridDataCreator.py and the
    validationPlots.py.
    """
    
    topology = 'T2'
    if not topology in topologyInfo():
        print('No slha files are available for %s!' %topology)
        sys.exit()
    base = '/afs/hephy.at/user/w/walten/public/sms/'
    browser = Browser(base)
    if not browser:
        print('No valid database!')
        sys.exit()
    order = 'NLL'
    intermediate = 'xvalue,050'
    analyses = browser.allAnalyses(topology = topology)
    analyses = [a for a in analyses if browser.expResult(a, topology)]
    
    path = getTarget('./gridData/%s/' %topology)
    
    print("========================================================")
    print('Validating procedure for:')
    print('Topology: ', topology)
    print('Analysis: ')
    print(analyses)
    print("========================================================")
    
    for ana in analyses:
    
        arguments = {'analysis': ana, 'base': base, 'events': 10000, \
        'intermediate': intermediate, 'order': order, 'topology': topology, \
        'directory': path}

        gridDataCreator.main(arguments)
        validationPlots.main(arguments)

    
def checkFile(path):
    """Checks if the data file already exists.
    If the file already exists, the user can decide whether to remove it, 
    or to exit the script.
    
    """
    if os.path.exists(path):
        print('File %s already exists!' %path)
        while True:
            userInput = raw_input('Replace old file? [y/n]:  ')
            if userInput == 'n':
                sys.exit()
            if userInput == 'y':
                os.remove(path)
                return path
    return path    

def getTarget(path):
    """Checks if the target directory already exists and creates it if not.
    
    """
    
    if os.path.exists(path):
        logger.info('Target %s already exists.' %path)
        return path
    
    os.mkdir(path)
    logger.info('Created new directory: %s' %path) 
    return path
    
    
def topologyInfo():
    """Gives some infomation about topologies there are slha files for.
    
    """
    
    topologies = os.listdir('../slha')
    topologies = [t for t in topologies if not '.' in t]
    topologies = [t.split('_')[0] for t in topologies if t.split('_')[1] == '10000']
    
    return topologies

    
if __name__ == '__main__':
    main()      
