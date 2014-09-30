#!/usr/bin/env python

"""
.. module:: twikiCreator
   :synopsis: Will produce the entries for the twiki page for the validation plots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>

"""

from __future__ import print_function
from smodels_tools.tools.databaseBrowser import Browser


def main():
    """Gets all the analyses for one topology and 
    checks for results.
    Calls the gridDataCreator.py and the validationPlots.py.
    """
    
    topology = 'TSlepSlep'
    order = 'LO * 1.2'
    base = '/afs/hephy.at/user/w/walten/public/sms/'
    browser = Browser(base)
    if not browser:
        print('No valid database!')
        sys.exit()
    
    outFile = open('./twiki/twiki_%s.txt' %topology, 'w')
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
        checked = 'NO'
        if expResSet.isChecked:
            checked = 'YES'
        massParam = ['%s <<BR>>' %expResSet.members[entry] for entry in expResSet.members]
        massParamField = ''.join(massParam)
        plotField = 'done with 10000 events <<BR>> [[[[attachment:%s%snew.png|%s]]' %(topology, ana, order)
        commentField = 'not yet done'
        if not expResSet.constraint:
            commentField = commentField + ' -> no constraints!'
        if not expResSet.hasUpperLimitDicts():
            commentField = commentField + ' <<BR>> -> no upper limits!'
            
        line = '||%s||%s | %s||%s||%s||' %(analysisField, published, checked, plotField, commentField)
        print(line, file = outFile)
        
    outFile.close()  
    
if __name__ == '__main__':
    main()  