#!/usr/bin/env python

"""
.. module:: getSUSYprocess
   :synopsis: Tool for fetching official plots which contain the SUSY process
              definition for the Txnames.

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import sys,webbrowser

sys.path.append('../../smodels')
sys.path.append('../fastlim_tools')
from smodels.tools.databaseBrowser import Browser
from convertTools.convertHelpers import smodels2fastlim

b = Browser('../../smodels-database')

txList = sorted(list(set(b.getValuesFor('txName'))))

figURL = {}

for tx in txList:
    b.loadAllResults()
    b.selectExpResultsWith(txName = tx)
    figURL[tx] = None
    for exp in b:
        txobjList = exp.getTxnameWith({'txName' : tx})
        if not txobjList: continue
        if isinstance(txobjList,list):
            txobj = txobjList[0]
        else:
            txobj = txobjList
        if not hasattr(txobj,'figureUrl') or not txobj.figureUrl:
            continue
        figURL[tx] = txobj.figureUrl
        break

skip = True    
for tx in txList:
    if tx == 'T5WW':
        skip = False
    if skip: continue
    print tx
    if not figURL[tx]:
        print 'missing url'
        fast = smodels2fastlim(tx)
        if fast:
            print 'Fastlim topo:',fast
    else:
        if isinstance(figURL[tx],list):
            figURL[tx] = figURL[tx][0]
        webbrowser.get('firefox').open_new_tab(figURL[tx])
    go = raw_input('Press any key to proceed\n')
