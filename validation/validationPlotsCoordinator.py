#!/usr/bin/env python

"""
.. module:: validationPlotsCoordinator
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
import validationPlotsHelper

logger = logging.getLogger(__name__)

def main():
    """Gets all the topologies, gets all the analyses for one topology and 
    checks for results.
    Calls the gridDataCreator.py and the validationPlots.py.
    """
    argparser = argparse.ArgumentParser(description = \
    'Produces the grid data for smodels validation plots')
    argparser.add_argument ('-b', '--Base', \
    help = 'set path to base-directory of smodels-database \n \
    - default: /afs/hephy.at/user/w/walten/public/sms/', \
    type = types.StringType, default = '/afs/hephy.at/user/w/walten/public/sms/')
    argparser.add_argument ('-t', '--topology', \
    help = 'topology that should be validated - default: T1',\
    type = types.StringType, default = 'T1')
    argparser.add_argument ('-o', '--order', \
    help = 'perturbation order (LO, NLO, NLL) - default: NLL', \
    type = types.StringType, default = 'NLL')
    argparser.add_argument ('-n', '--events',\
    help = 'set number of events - default: 10000', \
    type = types.IntType, default = 10000)
    argparser.add_argument ('-p', '--parametrization', \
    help = 'mass parametrization when there is an intermediate particle \n \
    - default: None', type = types.StringType, default = None)
    argparser.add_argument ('-v', '--value', help = 'value for parametrization \n \
    - default: 0.50', type = types.StringType, default = '0.50')
    args = argparser.parse_args()
    
    base = args.Base
    topology = args.topology
    if not topology in topologyInfo():
        print('No slha files are available for %s!' %topology)
        sys.exit()
    parametrization = args.parametrization
    value = args.value
    valueString = value
    if not parametrization:
        value = None
        valueString = None
    else:
        value = validationPlotsHelper.validateValue(value)
    browser = Browser(base)
    if not browser:
        print('No valid database!')
        sys.exit()
    if topology[-2:] == 'on':
        topologyName = topology[:-2]
    else: topologyName = topology
    events = args.events
    order = args.order
    allAnalyses = browser.getAnalyses(topology = topology)
    seven = [a for a in allAnalyses if browser.expAnalysis(a) \
    and  browser.expAnalysis(a).sqrts == 7.0]
    analyses = [a for a in allAnalyses if browser.expAnalysis(a) \
    and  browser.expAnalysis(a).sqrts == 8.0]
    analyses = [a for a in analyses if browser.expResultSet(a, topology) \
    and  browser.expResultSet(a, topology).hasUpperLimitDicts()]
    
    path = validationPlotsHelper.getTarget('./gridData/%s/' %topology)
    targetPath = validationPlotsHelper.getTarget('./plots/%s/' %topology)
    
    logFile = open('%s/logFile' %path, 'w')
    
    print("========================================================")
    print('Validating procedure for:')
    print('Topology: ', topology)
    print('Parametrization: ', parametrization)
    print('Value: ', value)
    print('Analyses: ')
    print(analyses)
    print("========================================================")
    
    print("========================================================", file = logFile)
    print('Topology: ', topology, file = logFile)
    print('Parametrization: ', parametrization, file = logFile)
    print('Value: ', value, file = logFile)
    print('Analyses: ', file = logFile)
    print(analyses, file = logFile)
    print("========================================================", file = logFile)
    
    for ana in seven:
            print('Skipped %s with sqrt = %s!' \
            %(ana, browser.expAnalysis(ana).sqrts), file = logFile)
    for ana in analyses:
        arguments = {'analysis': ana, 'base': base, 'events': 10000, \
        'parametrization': parametrization, 'value': value, 'valueString': valueString, 'order': order, 'topology': topology, \
        'directory': path}
        try:    
            gridDataCreator.main(arguments)
            print('Sucsessfully created data grid for analyses: %s' %ana, file = logFile)
        except:
            logger.warning('could not make grid for %s' %ana)
            print('Could not create data grid for analyses: %s' %ana, file = logFile)
        try:
            validationPlots.main(arguments)
            print('Sucsessfully created validation plot for analyses: %s' %ana, file = logFile)
        except:
            logger.warning('could not plot %s' %ana)
            print('Could not create validation plot for analyses: %s' %ana, file = logFile)
        print("--------------------------------------------------------", file = logFile)
    logFile.close()

    
def topologyInfo():
    """Gives some infomation about topologies there are slha files for.
    
    """
    
    topologies = os.listdir('../slha')
    topologies = [t for t in topologies if not '.' in t]
    topologies = [t.split('_')[0] for t in topologies if t.split('_')[1] == '10000']
    
    return topologies

    
if __name__ == '__main__':
    main()      
