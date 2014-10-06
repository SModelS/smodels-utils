#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: twikiCreator
   :synopsis: Will produce the entries for the twiki page for the validation plots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""

from __future__ import print_function
import setPath  # # set to python path for smodels
from smodels_tools.tools.databaseBrowser import Browser
import validationPlotsHelper
import argparse
import types
import logging

logger = logging.getLogger(__name__)

def main():
    """Gets all the analyses for one topology and 
    checks for results.
    Calls the gridDataCreator.py and the validationPlots.py.
    """
    argparser = argparse.ArgumentParser(description = \
    'Produces the slha files for smodels validation plots')
    argparser.add_argument ('-b', '--Base', \
    help = 'set path to base-directory of smodels-database\n \
    - default: /afs/hephy.at/user/w/walten/public/sms/', \
    type = types.StringType, default = '/afs/hephy.at/user/w/walten/public/sms/')
    argparser.add_argument ('-t', '--topology', \
    help = 'topology that slha-files should be produced for - default: T1',\
    type = types.StringType, default = 'T1')
    argparser.add_argument ('-o', '--order', \
    help = 'perturbation order (LO, NLO, NLL) - default: NLL', \
    type = types.StringType, default = 'NLL')
    args = argparser.parse_args()
    
    topology = args.topology
    order = args.order
    if order == 'NLO':
        order = 'LO * 1.2'
    
    topoLink = '([[SmsDictionary#%s|%s]])' %(topology, topology)
    browser = Browser(args.Base)
    if not browser:
        print('No valid database!')
        sys.exit()
    path = validationPlotsHelper.checkFile('./twiki/twiki_%s.txt' %topology)    
    outFile = open(path, 'w')
    print(topoLink, file = outFile)
    head = "||'''Analysis  <<BR>>  (√s,lum)''' ||'''mass parametrization''' ||'''published data | checked''' ||'''plot''' ||'''comment''' ||"
    print(head, file = outFile)
    analyses = browser.getAnalyses(topology = topology)

    
    for ana in analyses:
        expAna = browser.expAnalysis(ana)
        if not expAna: continue
        url = expAna.url
        pas = expAna.pas
        lumi = expAna.lumi
        sqrts = expAna.sqrts
        prettyName = expAna.prettyName
        if url:
            url = url.split()[0].strip()
        analysisField = '[[%s|%s]] <<BR>> (%s, %s TeV, %s/fb)' %(url, pas, prettyName, sqrts, lumi)
        published = 'NO'
        if bool(expAna.publishedData):
            published = 'YES'
        expResSet = browser.expResultSet(ana, topology)
        commentField = 'not yet done'
        checked = 'NO'
        massParamField = 'not available'
        plotField = 'not available'
        if not expResSet: 
            commentField = commentField + ' <<BR>> -> no experimental result! <<BR>> -> check database entry!'
        else:
            if expResSet.isChecked:
                checked = 'YES'
            try:
                massParam = [(str(expResSet.members[entry]) + '<<BR>>') for entry in expResSet.members]
                massParamField = ''.join(massParam)
            except KeyError, e:
                logger.error('When calling the members of the set, \n \
                a KeyError occured: %s' %e)
                massParamField = 'not available'
            plotField = 'done with 10000 events <<BR>> [[attachment:%s%snew.png|%s]]' %(topology, ana, order)
            if not expResSet.constraint:
                commentField = commentField + ' -> no constraints!'
            if not expResSet.hasUpperLimitDicts():
                commentField = commentField + ' <<BR>> -> no upper limits!'
            
        line = '||%s||%s||%s | %s||%s||%s||' %(analysisField, massParamField, published, checked, plotField, commentField)

        print(line, file = outFile)
        
    outFile.close()  
    
if __name__ == '__main__':
    main()  
